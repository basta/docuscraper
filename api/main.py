from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from typing import Optional
import sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware #
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict
import asyncio
import uuid
import json


limiter = Limiter(key_func=get_remote_address)

# A simple in-memory store for active scraping jobs
# In a production app, you might use Redis or a database
job_store: Dict[str, asyncio.Queue] = {}

# Adjust path to import from the root directory
sys.path.append(str(Path(__file__).resolve().parents[1]))

from doc_scraper_engine.engine import ScrapingEngine

async def run_scraper_in_background(job_id: str, start_url: str, selector: str, url_filter: Optional[str]):
    """The background task that runs the scraper and puts results in the queue."""
    queue = job_store.get(job_id)
    if not queue:
        print(f"Error: Job ID {job_id} not found in store.")
        return

    try:
        engine = ScrapingEngine(
            start_url=start_url,
            selector=selector,
            url_filter=url_filter
        )
        # The engine will now put messages into the queue instead of returning
        await engine.run(queue=queue)
    except Exception as e:
        # Put a final error message in the queue
        error_message = json.dumps({"type": "error", "message": f"An unexpected error occurred: {str(e)}"})
        await queue.put(error_message)
    finally:
        # Sentinel value to indicate completion
        await queue.put(None)

async def sse_generator(job_id: str, request: Request):
    """Yields SSE messages from a job's queue."""
    queue = job_store.get(job_id)
    if not queue:
        print(f"Attempted to stream non-existent job_id: {job_id}")
        return

    try:
        while True:
            if await request.is_disconnected():
                print(f"Client for job {job_id} disconnected.")
                break

            try:
                message = await asyncio.wait_for(queue.get(), timeout=15)
                if message is None: # Sentinel value means the job is done
                    break

                yield f"data: {message}\n\n"
                queue.task_done()

            except asyncio.TimeoutError:
                continue
    finally:
        print(f"Closing stream and cleaning up job: {job_id}")
        if job_id in job_store:
            del job_store[job_id]


app = FastAPI(
    title="DocuScraper API",
    description="An API to crawl and scrape documentation websites into a single text block.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



class ScrapeRequest(BaseModel):
    start_url: HttpUrl
    selector: str
    url_filter: Optional[str] = None

import aiofiles
from fastapi.responses import PlainTextResponse

HISTORY_DIR = Path(__file__).resolve().parents[1] / "history"

@app.get("/history", response_model=list)
async def get_history():
    """
Returns a list of past scrape jobs from the history index.
    """
    index_file = HISTORY_DIR / "index.json"
    if not index_file.exists():
        return []
    try:
        async with aiofiles.open(index_file, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
    except (IOError, json.JSONDecodeError):
        return []

@app.get("/history/{job_id}", response_class=PlainTextResponse)
async def get_history_content(job_id: str):
    """
Returns the saved text content for a given job_id.
    """
    content_file = HISTORY_DIR / f"{job_id}.txt"
    if not content_file.exists():
        raise HTTPException(status_code=404, detail="Scrape result not found.")

    async with aiofiles.open(content_file, "r", encoding="utf-8") as f:
        return await f.read()


@app.post("/scrape", response_model=dict)
@limiter.limit("5/minute")
async def start_scrape_job(request: Request, scrape_request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
Starts a scraping job in the background and returns a job_id to stream results from.
    """
    job_id = str(uuid.uuid4())
    job_store[job_id] = asyncio.Queue()

    background_tasks.add_task(
        run_scraper_in_background,
        job_id,
        str(scrape_request.start_url),
        scrape_request.selector,
        scrape_request.url_filter
    )

    return {"job_id": job_id}

@app.get("/scrape/stream/{job_id}")
async def stream_scrape_progress(job_id: str, request: Request):
    """
Endpoint for the frontend to connect to for SSE updates.
    """
    return StreamingResponse(sse_generator(job_id, request), media_type="text/event-stream")

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
