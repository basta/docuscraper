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

limiter = Limiter(key_func=get_remote_address)

# Adjust path to import from the root directory
sys.path.append(str(Path(__file__).resolve().parents[1]))

from doc_scraper_engine.engine import ScrapingEngine

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


@app.post("/scrape", response_model=dict)
@limiter.limit("5/minute")
async def scrape_site(request: Request, scrape_request: ScrapeRequest):
    """
    Accepts a URL, CSS selector, and an optional filter, then returns the scraped content.
    """
    try:
        engine = ScrapingEngine(
            start_url=str(scrape_request.start_url),
            selector=scrape_request.selector,
            url_filter=scrape_request.url_filter
        )
        final_text = await engine.run()
        return {"content": final_text}
    except Exception as e:
        # In a real app, you'd have more specific error handling
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
