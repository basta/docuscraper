from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
import sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware # 👈 1. Add this import


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

class ScrapeRequest(BaseModel):
    start_url: HttpUrl
    selector: str
    url_filter: Optional[str] = None

@app.post("/scrape", response_model=dict)
async def scrape_site(request: ScrapeRequest):
    """
    Accepts a URL, CSS selector, and an optional filter, then returns the scraped content.
    """
    try:
        engine = ScrapingEngine(
            start_url=str(request.start_url),
            selector=request.selector,
            url_filter=request.url_filter
        )
        final_text = await engine.run()
        return {"content": final_text}
    except Exception as e:
        # In a real app, you'd have more specific error handling
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "DocuScraper API is running. POST to /scrape to start."}
