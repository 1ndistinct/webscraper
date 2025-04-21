"""
Test Scraper functionality
"""

import json
import logging
import os
from uuid import uuid4
from httpx import ASGITransport, AsyncClient
import httpx
from pydantic import HttpUrl, ValidationError
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
from webscraper.settings import get_core_settings, get_http_client_settings
from webscraper.utils import get_httpx_client, setup_logging, RetryTransport
from webscraper.__main__ import scrape
from .mocks.site import app


def test_main_runs():
    """
    test that main runs and writes to file
    """
    results_filename = "results.json"
    with pytest.raises(ValidationError):
        scrape("ftp://test", results_filename=results_filename)
    scrape("http://test")
    assert os.path.exists(results_filename)
    with open(results_filename, "r", encoding="utf-8") as f:
        results = json.loads(f.read())
    assert results["counts"]["failed"] == 1
    assert results["total_count"] == 1
    assert results["status"]["failed"] == ["http://test/"]


def test_root_logger_config():
    """
    Test root logger configuration
    """
    settings = get_core_settings()
    settings.log_level = "DEBUG"
    setup_logging()
    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG
    types = [type(handler) for handler in root_logger.handlers]
    assert logging.StreamHandler in types
    assert logging.FileHandler in types


def test_get_httpx_client():
    """
    test fetch httpx client with desired config
    """
    settings = get_http_client_settings()

    client = get_httpx_client()
    assert client.follow_redirects is True
    assert client.timeout.pool == settings.pool_timeout
    assert client.timeout.read == settings.timeout
    assert client.timeout.write == settings.timeout
    assert client.timeout.connect == settings.timeout
    transport = client._transport
    assert isinstance(transport, RetryTransport)

    assert transport._backoff_factor == settings.backoff_factor
    assert transport._status_retries == settings.status_retries

    wrapped_transport = transport._transport
    assert isinstance(wrapped_transport, httpx.AsyncHTTPTransport)
    assert wrapped_transport._pool._retries == settings.connection_retries
    assert wrapped_transport._pool._max_connections == settings.max_connections
    assert (
        wrapped_transport._pool._max_keepalive_connections
        == settings.max_keepalive_connections
    )


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
    results = db.get_scrape_stats(id_)
    assert results["total_count"] == 1
    assert results["counts"]["success"] == 1
    assert results["status"]["success"] == [url.encoded_string()]


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
    assert validate_next_steps(settings, working_url, 0) == Status.PENDING
    db.set_url_status(settings.id_, working_url, Status.FAILED)
    # test already worked on
    assert validate_next_steps(settings, working_url, 0) == Status.FAILED

    # test different host
    different_host_url = HttpUrl("https://google.com")
    assert (
        validate_next_steps(settings, different_host_url.encoded_string(), 0)
        == Status.IGNORED
    )
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
        "http://abc.test/about?a=b",
        "http://test/about",
        "http://test/blog",
        "http://test/blog",
        "http://test/blog",
        "http://test/contact",
        "http://test/search",
    ]


@pytest.mark.asyncio
async def test_retry_transport(client: AsyncClient):
    """
    Test retry_transport
    """
    client = AsyncClient(
        transport=RetryTransport(ASGITransport(app=app), 5, 0.1), base_url="http://test"
    )
    resp = await client.get("/rate")  ## this endpoint only returns 200 after 3 attempts
    assert resp.status_code == 500
    assert resp.json() == {"detail": "failed"}


@pytest.mark.asyncio
async def test_scrape():
    """
    Integration test running on the mock app
    """
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    base_url = HttpUrl(str(client.base_url))
    id_ = await begin(base_url, 10, client)
    results = get_results(id_)
    counts = results["counts"]
    status = results["status"]
    assert results["total_count"] == 11
    assert counts[Status.FAILED] == 1
    assert counts[Status.SUCCESS] == 5
    assert counts[Status.IGNORED] == 5
    assert status[Status.FAILED] == ["http://test/search"]
    assert status[Status.SUCCESS] == [
        "http://test/",
        "http://test/about",
        "http://test/blog",
        "http://test/contact",
        "http://test/payments",
    ]
    assert status[Status.IGNORED] == [
        "https://twitter.com/example",
        "https://facebook.com/example",
        "https://linkedin.com/company/example",
        "http://abc.test/about?a=b",
        "http://abc.test/about?b=c",
    ]
