"""
Test configuration
"""

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from .mocks.site import app


@pytest_asyncio.fixture
async def client():
    """
    Fastapi test client
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as cli:
        try:
            yield cli
        finally:
            try:
                await cli.aclose()
            except RuntimeError:
                ...


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup():
    """
    Cleanup between tests
    """
    yield
