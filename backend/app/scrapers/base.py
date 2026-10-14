"""Scraper protocol + shared HTTP helper.

Every source (portal, ministry, aggregator, telegram) implements ``Scraper`` and
returns a list of ``RawAnnouncement``. The rest of the pipeline is source-agnostic, so
adding a new source is contained to a single module.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.db.models import RawAnnouncement


@runtime_checkable
class Scraper(Protocol):
    #: Must match a row name in ``announcement_sources``.
    source_name: str

    def fetch(self) -> list[RawAnnouncement]:
        """Return raw announcements discovered on this source."""
        ...


def make_client() -> httpx.Client:
    settings = get_settings()
    return httpx.Client(
        headers={"User-Agent": settings.http_user_agent},
        timeout=settings.request_timeout_seconds,
        follow_redirects=True,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def get_html(client: httpx.Client, url: str) -> str:
    """GET with retry/backoff, returning decoded text."""
    resp = client.get(url)
    resp.raise_for_status()
    return resp.text
