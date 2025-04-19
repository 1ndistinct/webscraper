"""
Test Scraper functionality
"""

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_thing(client: AsyncClient):
    """
    Test thing
    """
    resp = await client.get("")
    assert resp.status_code == 200
