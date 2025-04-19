"""
helper functions and enums
"""

from functools import lru_cache
import logging
import os
import sys

import httpx
from .settings import get_http_client_settings, get_core_settings


@lru_cache
def get_httpx_client():
    """
    return consistent and global httpx client
    to prevent too many connections
    """
    settings = get_http_client_settings()
    return httpx.AsyncClient(
        follow_redirects=True,
        transport=httpx.AsyncHTTPTransport(
            retries=settings.retries,
            limits=httpx.Limits(
                max_connections=settings.max_connections,
                max_keepalive_connections=settings.max_keepalive_connections,
            ),
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
