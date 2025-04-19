"""
In memory database interface
"""

from functools import lru_cache
from uuid import UUID

from pydantic import HttpUrl
from .definitions import Status, ScrapeEvent, ScrapeEventSettings


class Db:
    """
    In memory db interface
    """

    def __init__(self):
        self.db: dict[UUID, ScrapeEvent] = {}

    def add_scrape_event(
        self, id_: UUID, base_url: HttpUrl, max_depth: int
    ) -> ScrapeEventSettings:
        """add a new scrape event to db"""
        settings = ScrapeEventSettings(id_=id_, max_depth=max_depth, base_url=base_url)
        self.db[id_] = ScrapeEvent(settings=settings)
        return settings

    def get_scrape_event_settings(self, id_: UUID):
        """Get scrape event"""
        if id_ not in self.db:
            raise KeyError("scrape event doesn't exist")
        return self.db[id_].settings

    def set_url_status(self, id_: UUID, url: HttpUrl, status: Status):
        """set scrape status"""
        self.db[id_].status[url] = status

    def get_url_status(self, id_: UUID, url: HttpUrl):
        """get scrape status"""
        if url not in self.db[id_].status:
            return Status.MISSING
        return self.db[id_].status[url]

    def get_scrape_stats(self, id_: UUID):
        """
        get high level stats of scrape event
        """
        event = self.db[id_]  # expected key error if scrape event doesn't exist
        outcome: dict[Status, list[str]] = {status: [] for status in Status}
        for url, status in event.status.items():
            if (
                url not in outcome[status]
            ):  # using a list instead of a set so its json serializable
                outcome[status].append(url.encoded_string())
        return outcome


@lru_cache
def get_db():
    """get in memory db,cached and global"""
    return Db()
