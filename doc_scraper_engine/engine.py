import asyncio
from typing import Optional

from .crawler import Crawler
from .scraper import Scraper
from .processor import Processor

class ScrapingEngine:
    """
    Orchestrates the crawling, scraping, and processing workflow.
    """

    def __init__(self, start_url: str, selector: str, url_filter: Optional[str] = None, max_pages: int = 50):
        """
        Initializes the engine with the necessary configuration.

        Args:
            start_url: The initial URL to begin crawling.
            selector: The CSS selector for the main content to be scraped.
            url_filter: An optional wildcard pattern to filter URLs.
        """
        self.start_url = start_url
        self.selector = selector
        self.crawler = Crawler(start_url, url_filter=url_filter, max_pages=max_pages)
        self.scraper = Scraper(selector)
        self.processor = Processor()

    async def run(self) -> str:
        """
        Executes the entire scraping pipeline.

        1. Crawls the website to find all relevant URLs.
        2. Scrapes the content from each URL.
        3. Processes and combines the content into a single text block.

        Returns:
            The final, cleaned, and combined text from the documentation site.
        """
        print(f"Starting crawl from: {self.start_url}")
        urls_to_scrape = await self.crawler.crawl()
        print(f"Found {len(urls_to_scrape)} URLs to scrape.")

        print(f"Scraping content using selector: '{self.selector}'")
        scraped_content = await self.scraper.scrape_urls(urls_to_scrape)
        print(f"Successfully scraped content from {len(scraped_content)} pages.")

        print("Processing and cleaning text...")
        final_text = self.processor.process(scraped_content)
        print("Processing complete.")

        return final_text
