"""
Logic for scraping endpoints given a starting point
"""

import asyncio
import logging
import signal
from urllib.parse import urljoin
from uuid import UUID, uuid4
from bs4 import BeautifulSoup
from pydantic import HttpUrl, ValidationError
import httpx

from webscraper.settings import get_core_settings
from .utils import get_httpx_client
from .definitions import Status, ScrapeEventSettings
from .datastore import Db, get_db


async def _fetch_page(
    url: HttpUrl, client: httpx.AsyncClient, settings: ScrapeEventSettings, db: Db
) -> str:
    """
    fetch page content
    """
    try:
        response = await client.get(url.encoded_string())
        response.raise_for_status()
        db.set_url_status(settings.id_, url, Status.SUCCESS)
        return response.text
    except httpx.HTTPError:
        logging.exception("Failed to fetch %s", url)
        db.set_url_status(settings.id_, url, Status.FAILED)
        return ""


def _extract_links(html: str, current_url: HttpUrl):
    """
    Extract links from page
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("a", href=True):
        url: str = urljoin(current_url.encoded_string(), tag["href"])  # type:ignore
        try:
            yield HttpUrl(url)
        except ValidationError:
            logging.debug("invalid href %s, continuing...", url)


def validate_next_steps(settings: ScrapeEventSettings, url: str, depth: int):
    """
    Get the next status for an event
    """
    try:
        parsed_url = HttpUrl(url)
    except ValidationError:
        logging.debug("invalid url, settings ignored.")
        return Status.IGNORED

    db = get_db()
    if depth > settings.max_depth:
        logging.debug("max depth reached, settings ignored.")
        return Status.IGNORED

    if parsed_url.host != settings.base_url.host:
        logging.debug(
            "url %s on a different domain to base url %s, setting ignored.",
            parsed_url.host,
            settings.base_url.host,
        )
        return Status.IGNORED

    if (status := db.get_url_status(settings.id_, url)) != Status.MISSING:
        logging.debug("url %s is already worked on, keeping status the same...", url)
        ## inefficient resetting of this key - extra unneccesary transaction but makes code cleaner
        return status

    return Status.PENDING


async def worker(
    queue: asyncio.Queue,
    client: httpx.AsyncClient,
    settings: ScrapeEventSettings,
    shutdown_event: asyncio.Event,
):
    """
    Run workers to scrape links
    """
    db = get_db()
    while not shutdown_event.is_set():
        try:
            url, depth = queue.get_nowait()  # syncronous operation
        except (
            asyncio.QueueEmpty
        ):  # allows sigterm and siging to shutdown worker when no messages are on queue
            await asyncio.sleep(1)  # prevents cpu hogging
            continue
        db.set_url_status(settings.id_, url, Status.IN_PROGRESS)
        html = await _fetch_page(url, client, settings, db)
        links = []
        for extracted_url in _extract_links(html, url):
            links.append(extracted_url.encoded_string())
            status = validate_next_steps(settings, extracted_url, depth)
            db.set_url_status(settings.id_, extracted_url, status)
            if status != Status.PENDING:
                continue  # don't add to queue if already worked on or ignored

            queue.put_nowait((extracted_url, depth + 1))

        logging.info("\033[1;32mvisited %s\033[0m", url.encoded_string())
        logging.info("\033[1;33mLinks found: %s\033[0m", links)
        queue.task_done()


async def begin(
    base_url: HttpUrl, max_depth: int, httpx_client: httpx.AsyncClient | None = None
):
    """
    Begin function to create and pass in the httpx client
    """
    event_settings = get_db().add_scrape_event(uuid4(), base_url, max_depth)
    core_settings = get_core_settings()

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()
    loop.add_signal_handler(signal.SIGTERM, shutdown_event.set)
    loop.add_signal_handler(signal.SIGINT, shutdown_event.set)
    ## Do initial validation - have to duplicate this logic twice, but improves efficiency
    status = validate_next_steps(event_settings, event_settings.base_url, 0)
    get_db().set_url_status(event_settings.id_, event_settings.base_url, status)
    ##
    queue.put_nowait((event_settings.base_url, 0))

    httpx_client = httpx_client or get_httpx_client()
    async with httpx_client as client:
        workers = [
            asyncio.create_task(worker(queue, client, event_settings, shutdown_event))
            for _ in range(core_settings.num_workers)
        ]
        await queue.join()

    shutdown_event.set()

    await asyncio.gather(*workers)

    return event_settings.id_


def get_results(id_: UUID):
    """get scrape event status"""
    return get_db().get_scrape_stats(id_)
