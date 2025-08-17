import asyncio
from typing import Dict, List

import aiohttp
from bs4 import BeautifulSoup

class Scraper:
    """
    Asynchronously scrapes content from a list of URLs based on a CSS selector.
    """

    def __init__(self, selector: str, max_concurrent_requests: int = 10):
        """
        Initializes the Scraper.

        Args:
            selector: The CSS selector for the main content area of the pages.
            max_concurrent_requests: The maximum number of concurrent HTTP requests.
        """
        if not selector:
            raise ValueError("A CSS selector must be provided.")
        self.selector = selector
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def scrape_urls(self, urls: List[str]) -> Dict[str, str]:
        """
        Scrapes a list of URLs and returns their content.

        Args:
            urls: A list of URLs to scrape.

        Returns:
            A dictionary mapping each URL to its scraped content.
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_and_extract(url, session) for url in urls]
            results = await asyncio.gather(*tasks)
            # Filter out None results from failed scrapes and combine into a dict
            return {url: content for url, content in zip(urls, results) if content is not None}

    async def _fetch_and_extract(self, url: str, session: aiohttp.ClientSession) -> str | None:
        """
        Fetches a single URL and extracts content using the specified selector.
        """
        async with self.semaphore:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200 and "text/html" in response.headers.get("Content-Type", ""):
                        html = await response.text()
                        soup = BeautifulSoup(html, "lxml")
                        content_area = soup.select_one(self.selector)
                        if content_area:
                            return content_area.get_text(separator=" ", strip=True)
                        else:
                            print(f"Warning: Selector '{self.selector}' not found on {url}")
                            return None
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                return None
        return None
