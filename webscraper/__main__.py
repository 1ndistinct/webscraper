"""
App entrypoint
"""

import logging
import typer
from pydantic import HttpUrl
from .setup import setup_logging

app = typer.Typer()


@app.command("scrape")
def scrape(starting_url: str):
    """
    Scrape all connecting URL's from a given website
    """
    validated_url = HttpUrl(starting_url)  # validate URL is in correct format
    logging.info("starting webscraper from %s...", validated_url)

    logging.info("scraping completed.")


if __name__ == "__main__":
    setup_logging()
    app()
