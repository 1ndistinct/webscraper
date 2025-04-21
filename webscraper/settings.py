"""
Settings and setup
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class HttpClientSettings(BaseSettings):
    """
    Http Client Settings
    """

    connection_retries: int = 3
    pool_timeout: int = 60
    timeout: int = 15
    max_connections: int = 100
    max_keepalive_connections: int = 50


class CoreSettings(BaseSettings):
    """App settings"""

    log_level: str = "INFO"
    num_workers: int = 10


@lru_cache
def get_core_settings():
    """cached app global base settings"""
    return CoreSettings()


@lru_cache
def get_http_client_settings():
    """cached app global http client settings"""
    return HttpClientSettings()
