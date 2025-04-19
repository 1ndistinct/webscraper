"""
Settings and setup
"""

from functools import lru_cache
import logging
import os
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings"""

    log_level: str = "INFO"


@lru_cache
def get_settings():
    """cached app settings"""
    return Settings()


def setup_logging():
    """
    Setup a stream handler to stdout and a file handler
    to write to ./logs/logfile.log from the root logger for convenience
    """
    settings = get_settings()
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
