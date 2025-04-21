"""
helper functions and enums
"""

import asyncio
from functools import lru_cache
import logging
import os
import random
import sys

import httpx
from .settings import get_http_client_settings, get_core_settings


class RetryTransport(httpx.AsyncBaseTransport):
    """
    Retry transport that uses the async http transport under the hood
    """

    def __init__(
        self,
        async_transport: httpx.AsyncBaseTransport,
        status_retries: int = 3,
        backoff_factor: float = 0.5,
        jitter_range: float = 1,
    ):
        self._status_retries = status_retries
        self._backoff_factor = backoff_factor
        self._retry_statuses = (429,)
        self._transport = async_transport
        self._jitter = jitter_range

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """
        Try this request, and retry up to x times if getting rate limited
        """
        for attempt in range(self._status_retries + 1):  # retries plus first attempt
            request.headers.update({"Attempt": str(attempt)})
            response = await self._transport.handle_async_request(request)
            if response.status_code not in self._retry_statuses:
                return response

            await response.aread()  # reads body and closes stream
            delay = random.uniform(0, self._jitter) + self._backoff_factor * pow(
                2, attempt
            )  # exponential backoff
            await asyncio.sleep(delay)

        return response


@lru_cache
def get_httpx_client():
    """
    return consistent and global httpx client
    to prevent too many connections
    """
    settings = get_http_client_settings()
    return httpx.AsyncClient(
        follow_redirects=True,
        transport=RetryTransport(
            async_transport=httpx.AsyncHTTPTransport(
                # this only retries on connection failures, not on bad status codes
                retries=settings.connection_retries,
                limits=httpx.Limits(
                    max_connections=settings.max_connections,
                    max_keepalive_connections=settings.max_keepalive_connections,
                ),
            ),
            # retries on bad status codes
            status_retries=settings.status_retries,
            backoff_factor=settings.backoff_factor,
            jitter_range=settings.jitter_range,
        ),
        timeout=httpx.Timeout(
            pool=settings.pool_timeout,
            timeout=settings.timeout,
        ),
    )


def setup_logging():
    """
    Setup a stream handler to stdout and a file handler
    to write to ./logs/logfile.log from the root logger for convenience
    """
    settings = get_core_settings()
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())
    stream_handler = logging.StreamHandler(stream=sys.stdout)

    logfolder, logfile = os.path.join(os.getcwd(), "logs"), "logfile.log"
    if not os.path.exists(logfolder):
        os.makedirs(logfolder)
    file_handler = logging.FileHandler(f"{logfolder}/{logfile}")

    formatter = logging.Formatter(
        "%(asctime)s | %(processName)-10s | %(levelname)-8s | %(funcName)s | %(message)s"
    )
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger
