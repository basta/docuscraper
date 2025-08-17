import re
from typing import Dict

class Processor:
    """
    Cleans and formats scraped text content.
    """

    def process(self, scraped_data: Dict[str, str]) -> str:
        """
        Takes scraped data and formats it into a single, clean text block.

        Args:
            scraped_data: A dictionary mapping URLs to their raw text content.

        Returns:
            A single string containing the cleaned and combined text.
        """
        full_text = ""
        for url, content in scraped_data.items():
            cleaned_content = self._clean_text(content)
            # Add a title-like header for each page's content for context
            full_text += f"--- Content from {url} ---\n\n"
            full_text += cleaned_content
            full_text += "\n\n"
        return full_text

    def _clean_text(self, text: str) -> str:
        """
        Performs cleaning operations on a block of text.
        """
        # Replace multiple spaces/newlines with a single one
        text = re.sub(r'\s{2,}', ' ', text)
        # Replace multiple newlines with a double newline for paragraph breaks
        text = re.sub(r'\n+', '\n\n', text)
        return text.strip()

