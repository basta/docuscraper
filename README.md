# DocuScraper 📄

A fast, asynchronous command-line tool to crawl and scrape documentation websites, consolidating all content into a single text file. Ideal for creating context files for LLMs.

---

## Key Features

-   🚀 **Asynchronous by Design**: Uses `aiohttp` to crawl and scrape multiple pages concurrently.
-   🎯 **Precise Content Extraction**: Uses CSS selectors to target the exact content you need, ignoring navigation, sidebars, and footers.
-   🔎 **Wildcard URL Filtering**: Easily restrict the crawl to specific sections of a site (e.g., `/docs/*`) to get only the relevant pages.

---

## Installation

This project uses `uv` for dependency management.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/basta/docuscraper.git
    cd docuscraper
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install the project in editable mode:**
    ```bash
    uv pip install -e .
    ```

---

## Usage

The tool is run from the command line using the `doc-scraper` command.

```bash
doc-scraper --start-url <URL> --selector "<CSS_SELECTOR>" --filter "<PATTERN>" --output-file <FILENAME.txt>
```

### **Arguments**

* `--start-url`: The initial URL to begin crawling.

* `--selector`: The CSS selector for the main content area.

* `--filter` (Optional): A wildcard pattern to only include matching URLs.

* `--output-file`: The path to save the final text file.

### **Example**

Scrape only the "Commands" section of the Typer documentation:

```bash
doc-scraper \
  --start-url "https://typer.tiangolo.com/" \
  --selector "div.md-content" \
  --filter "https://typer.tiangolo.com/tutorial/commands/*" \
  --output-file "typer_commands_docs.txt"
```
