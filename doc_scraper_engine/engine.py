import asyncio
from typing import Optional
import json
import time
from pathlib import Path

from .crawler import Crawler
from .scraper import Scraper
from .processor import Processor

class ScrapingEngine:
    """
Orchestrates the crawling, scraping, and processing workflow.
"""

    def __init__(self, start_url: str, selector: str, url_filter: Optional[str] = None, max_pages: int = 50):
        self.start_url = start_url
        self.selector = selector
        self.url_filter = url_filter
        self.max_pages = max_pages
        # Crawler is now initialized inside run() to pass the queue
        self.scraper = Scraper(selector)
        self.processor = Processor()
        self._index_lock = asyncio.Lock()
        self.HISTORY_DIR = Path(__file__).resolve().parents[1] / "history"

    async def _save_result(self, job_id: str, content: str, metadata: dict):
        """Saves scrape content and updates the metadata index."""
        try:
            self.HISTORY_DIR.mkdir(exist_ok=True)
            content_file = self.HISTORY_DIR / f"{job_id}.txt"
            content_file.write_text(content, encoding="utf-8")

            index_file = self.HISTORY_DIR / "index.json"

            async with self._index_lock:
                history = []
                if index_file.exists():
                    try:
                        history = json.loads(index_file.read_text("utf-8"))
                    except json.JSONDecodeError:
                        history = [] # Overwrite corrupted index

                new_entry = {
                    "job_id": job_id,
                    "timestamp": int(time.time()),
                    **metadata
                }
                history.insert(0, new_entry) # Add to the top

                # Keep history to a reasonable size, e.g., 50 entries
                history = history[:50]

                index_file.write_text(json.dumps(history, indent=4), encoding="utf-8")

            print(f"Result for job {job_id} saved to history.")

        except Exception as e:
            # Log error but don't crash the main scraping process
            print(f"Failed to save result for job {job_id}: {e}")

    async def run(self, queue: asyncio.Queue, job_id: Optional[str] = None) -> None:
        """
Executes the entire scraping pipeline and sends progress via a queue.
        """
        try:
            crawler = Crawler(self.start_url, url_filter=self.url_filter, max_pages=self.max_pages)

            await queue.put(json.dumps({"type": "progress", "message": f"Starting crawl from: {self.start_url}"}))

            # Pass the queue to the crawler to get real-time page found updates
            urls_to_scrape = await crawler.crawl(progress_queue=queue)
            await queue.put(json.dumps({"type": "progress", "message": f"Crawl complete. Found {len(urls_to_scrape)} URLs to scrape."}))

            await queue.put(json.dumps({"type": "progress", "message": f"Scraping content using selector: '{self.selector}'"}))
            scraped_content = await self.scraper.scrape_urls(urls_to_scrape)
            scraped_count = len(scraped_content)
            await queue.put(json.dumps({"type": "progress", "message": f"Successfully scraped content from {scraped_count} pages."}))

            if len(urls_to_scrape) > scraped_count:
                failed_count = len(urls_to_scrape) - scraped_count
                await queue.put(json.dumps({"type": "progress", "message": f"Note: Failed to scrape {failed_count} pages (selector not found or error)."}))

            await queue.put(json.dumps({"type": "progress", "message": "Processing and cleaning text..."}))
            final_text = self.processor.process(scraped_content)

            if job_id:
                await self._save_result(
                    job_id=job_id,
                    content=final_text,
                    metadata={
                        "start_url": self.start_url,
                        "selector": self.selector,
                        "url_filter": self.url_filter,
                    }
                )

            await queue.put(json.dumps({"type": "progress", "message": "Processing complete."}))

            # Send the final content
            await queue.put(json.dumps({"type": "complete", "content": final_text}))



        except Exception as e:
            error_message = json.dumps({"type": "error", "message": f"An error occurred in the engine: {str(e)}"})
            await queue.put(error_message)
