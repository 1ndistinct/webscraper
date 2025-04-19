"""
App entrypoint
"""

import asyncio
import json
import logging
from pydantic import HttpUrl
import typer

from .utils import setup_logging
from . import scraper

app = typer.Typer()


@app.command("scrape")
def scrape(
    starting_url: str, max_depth: int = 10, results_filename: str = "results.json"
):
    """
    Scrape all connecting URL's from a given website
    """
    logging.info("starting webscraper from %s...", starting_url)
    parsed_url = HttpUrl(starting_url)  # will fail fast if its the incorrect format
    id_ = asyncio.run(scraper.begin(parsed_url, max_depth))
    with open(results_filename, "w", encoding="utf-8") as f:
        f.write(json.dumps(scraper.get_results(id_)))
    logging.info("scraping completed.")


if __name__ == "__main__":
    setup_logging()
    app()
