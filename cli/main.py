import asyncio
import typer
from typing_extensions import Annotated
from pathlib import Path
from typing import Optional

# Adjust the path to import from the parent directory
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from doc_scraper_engine.engine import ScrapingEngine

app = typer.Typer(
    help="A CLI tool to crawl and scrape documentation websites into a single text file."
)


def run_async(coro):
    """Helper to run an async function."""
    return asyncio.run(coro)


@app.command()
def scrape(
        start_url: Annotated[
            str, typer.Option(..., "--start-url", "-u", help="The starting URL for the documentation site.")],
        selector: Annotated[
            str, typer.Option(..., "--selector", "-s", help="The CSS selector for the main content area.")],
        output_file: Annotated[
            Optional[Path], typer.Option("--output-file", "-o", help="Path to save the final text file.")] = None,
        url_filter: Annotated[Optional[str], typer.Option("--filter", "-f",
                                                          help="Wildcard pattern to filter URLs (e.g., 'https://site.com/docs/*').")] = None,
):
    """
    Crawl a documentation website and scrape its content into a single file.
    """
    typer.echo(f"🚀 Starting scrape for {start_url}")
    if url_filter:
        typer.echo(f"Filtering URLs with pattern: {url_filter}")

    engine = ScrapingEngine(start_url=start_url, selector=selector, url_filter=url_filter)

    try:
        final_text = run_async(engine.run())

        if output_file:
            output_file.write_text(final_text, encoding="utf-8")
            typer.secho(f"✅ Success! Content saved to {output_file}", fg=typer.colors.GREEN)
        else:
            typer.echo("\n--- SCRAPED CONTENT ---\n")
            typer.echo(final_text)
            typer.secho("\n✅ Success! Content printed above.", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"❌ An error occurred: {e}", fg=tye.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
