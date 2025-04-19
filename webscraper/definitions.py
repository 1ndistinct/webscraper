"""
Consts, enums and structs
"""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class Status(StrEnum):
    """
    Scrape Status
    """

    IN_PROGRESS = "inprogress"
    FAILED = "failed"
    SUCCESS = "success"
    MISSING = "missing"
    IGNORED = "ignored"


class ScrapeEventSettings(BaseModel):
    """Scrape event settings"""

    id_: UUID
    max_depth: int
    base_url: HttpUrl


class ScrapeEvent(BaseModel):
    """Scrape Event definition"""

    settings: ScrapeEventSettings
    status: dict[HttpUrl, Status] = Field(default_factory=dict)
