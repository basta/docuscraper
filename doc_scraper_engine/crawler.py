import asyncio
import fnmatch
from typing import Set, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


class Crawler:
    """
    Asynchronously crawls a website to find all unique, in-domain URLs
    using a producer-consumer pattern.
    """

    def __init__(self, start_url: str, url_filter: Optional[str] = None, max_concurrent_requests: int = 10):
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.url_filter = url_filter
        self.queue = asyncio.Queue()
        self.visited_urls: Set[str] = set()
        self.max_concurrent_requests = max_concurrent_requests

    async def crawl(self) -> List[str]:
        """
        Starts the crawling process and returns a list of all found URLs.
        """
        # The queue is the central point for tasks (URLs to process)
        self.queue.put_nowait(self.start_url)

        async with aiohttp.ClientSession() as session:
            # Create a pool of worker tasks to process the queue concurrently
            workers = [
                asyncio.create_task(self._worker(f"worker-{i}", session))
                for i in range(self.max_concurrent_requests)
            ]

            # Wait for the queue to be fully processed
            await self.queue.join()

            # All URLs have been processed, so we can cancel the workers
            for worker in workers:
                worker.cancel()

            await asyncio.gather(*workers, return_exceptions=True)

        return sorted(list(self.visited_urls))

    async def _worker(self, name: str, session: aiohttp.ClientSession):
        """
        A worker task that continuously fetches URLs from the queue and processes them.
        """
        while True:
            try:
                url = await self.queue.get()

                if url in self.visited_urls:
                    self.queue.task_done()
                    continue

                # Log which URL is being processed
                print(f"Processing: {url}")
                self.visited_urls.add(url)
                await self._fetch_and_find_links(url, session)

                # Signal that this task from the queue is done
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {name} encountered an error: {e}")
                self.queue.task_done()

    async def _fetch_and_find_links(self, url: str, session: aiohttp.ClientSession):
        """
        Fetches a single URL, parses its content for new links,
        and adds them back to the queue for the workers to process.
        """
        try:
            async with session.get(url, timeout=10) as response:
                # Log the result of the fetch attempt
                print(f"  -> Fetched ({response.status}): {url}")
                if response.status == 200 and "text/html" in response.headers.get("Content-Type", ""):
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")

                    # Find links and add them to the queue
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        full_url = urljoin(url, href)
                        parsed_url = urlparse(full_url)
                        clean_url = parsed_url._replace(query="", fragment="").geturl()

                        if self._is_valid_url(clean_url) and clean_url not in self.visited_urls:
                            await self.queue.put(clean_url)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    def _is_valid_url(self, url: str) -> bool:
        """
        Checks if a URL is in the same domain, is a web URL, and matches the filter.
        """
        parsed_url = urlparse(url)
        # Check if it's an HTTP/HTTPS URL and belongs to the same domain
        if not (parsed_url.scheme in ["http", "https"] and parsed_url.netloc == self.base_domain):
            return False

        # If a filter is provided, check if the URL matches the pattern
        if self.url_filter:
            if not fnmatch.fnmatch(url, self.url_filter):
                return False

        return True
