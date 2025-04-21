"""
Test configuration
"""

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from webscraper.settings import get_http_client_settings
from webscraper.datastore import get_db
from .mocks.site import app


@pytest_asyncio.fixture
async def client():
    """
    Fastapi test client
    """
    base_url = "http://test"
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=base_url,
    ) as cli:
        try:
            yield cli
        finally:
            await cli.aclose()


@pytest_asyncio.fixture(autouse=True)
async def setup_teardown():
    """
    test setup and teardown
    """
    http_settings = get_http_client_settings()
    http_settings.pool_timeout = 0.5
    http_settings.timeout = 0.5  # adjust timeouts to test case where not working
    http_settings.connection_retries = 0
    yield


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup():
    """
    Cleanup between tests
    """
    yield
    get_db.cache_clear()
