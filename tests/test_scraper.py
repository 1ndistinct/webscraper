"""
Test Scraper functionality
"""

from uuid import uuid4
from httpx import ASGITransport, AsyncClient
from pydantic import HttpUrl
import pytest
from webscraper.datastore import get_db
from webscraper.scraper import (
    _extract_links,
    _fetch_page,
    begin,
    get_results,
    validate_next_steps,
)
from webscraper.definitions import Status
from .mocks.site import app


@pytest.mark.asyncio
async def test_db_interface():
    """
    Test db interface
    """
    db = get_db()
    url = HttpUrl("http://random")
    id_ = uuid4()
    with pytest.raises(KeyError):
        db.get_scrape_event_settings(id_)
    with pytest.raises(KeyError):
        db.get_scrape_stats(id_)
    with pytest.raises(KeyError):
        db.get_url_status(id_, url)

    settings = db.add_scrape_event(id_, url, 1000)
    settings2 = db.get_scrape_event_settings(id_)
    assert settings == settings2
    assert db.get_url_status(id_, url) == Status.MISSING
    db.set_url_status(id_, url, Status.SUCCESS)
    assert db.get_scrape_stats(id_)["total_count"] == 1
    assert db.get_scrape_stats(id_)["counts"]["success"] == 1
    assert db.get_scrape_stats(id_)["status"]["success"] == [url.encoded_string()]


@pytest.mark.asyncio
async def test_fetch_page(client: AsyncClient):
    """
    Test fetching page
    """
    db = get_db()
    id_ = uuid4()
    working_url = HttpUrl(str(client.base_url))
    settings = db.add_scrape_event(id_, working_url, 1000)

    resp = await _fetch_page(working_url, client, settings, db)
    assert resp != ""
    status = db.get_url_status(settings.id_, working_url)
    assert status == Status.SUCCESS
    broken_url = HttpUrl(f"{working_url}/fake")
    resp = await _fetch_page(broken_url, client, settings, db)
    assert resp == ""
    status = db.get_url_status(settings.id_, broken_url)
    assert status == Status.FAILED


@pytest.mark.asyncio
async def test_validate_next_steps(client: AsyncClient):
    """
    Test validating url
    """
    db = get_db()
    id_ = uuid4()
    working_url = str(client.base_url)
    settings = db.add_scrape_event(id_, working_url, 2)
    assert validate_next_steps(settings, working_url, 0) == Status.IN_PROGRESS
    db.set_url_status(settings.id_, working_url, Status.FAILED)
    # test already worked on
    assert validate_next_steps(settings, working_url, 0) == Status.FAILED

    # test different host
    different_host_url = HttpUrl("https://google.com")
    assert validate_next_steps(settings, different_host_url, 0) == Status.IGNORED
    # test max depth reached
    assert validate_next_steps(settings, working_url, 3) == Status.IGNORED
    # test url is invalid
    assert validate_next_steps(settings, "ftp://google.com", 3) == Status.IGNORED


@pytest.mark.asyncio
async def test_extract_urls(client: AsyncClient):
    """
    Test fetching page
    """
    db = get_db()
    id_ = uuid4()
    working_url = HttpUrl(str(client.base_url))
    settings = db.add_scrape_event(id_, working_url, 1000)

    resp = await _fetch_page(working_url, client, settings, db)
    assert [link.encoded_string() for link in _extract_links(resp, working_url)] == [
        "https://twitter.com/example",
        "https://facebook.com/example",
        "https://linkedin.com/company/example",
        "http://test/about",
        "http://test/blog",
        "http://test/blog",
        "http://test/blog",
        "http://test/contact",
        "http://test/search",
    ]


@pytest.mark.asyncio
async def test_scrape():
    """
    Integration test running on the mock app
    """
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    base_url = HttpUrl(str(client.base_url))
    id_ = await begin(base_url, 10, client)
    results = get_results(id_)
    assert results == {
        "counts": {
            Status.IN_PROGRESS: 0,
            Status.FAILED: 1,
            Status.SUCCESS: 5,
            Status.MISSING: 0,
            Status.IGNORED: 3,
        },
        "total_count": 9,
        "status": {
            Status.IN_PROGRESS: [],
            Status.FAILED: ["http://test/search"],
            Status.SUCCESS: [
                "http://test/",
                "http://test/about",
                "http://test/blog",
                "http://test/contact",
                "http://test/payments",
            ],
            Status.MISSING: [],
            Status.IGNORED: [
                "https://twitter.com/example",
                "https://facebook.com/example",
                "https://linkedin.com/company/example",
            ],
        },
    }
