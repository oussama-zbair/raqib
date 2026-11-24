"""IT / software engineering filter for the channel publisher.

Matches on the title, grade, specialty and body text of an announcement. The
administration name is not used on purpose (a digital ministry also hires nurses).
"""
from __future__ import annotations

import logging

from app.db.models import RawAnnouncement
from app.matching.normalizer import normalize_text
from app.matching.taxonomy import IT_EXCLUDE_PHRASES, IT_PHRASES, IT_WORDS

log = logging.getLogger("it_filter")

_PHRASES = [(p, normalize_text(p)) for p in IT_PHRASES]
_WORDS = [(w, normalize_text(w)) for w in IT_WORDS]
_EXCLUDE = [normalize_text(p) for p in IT_EXCLUDE_PHRASES]


def _first_hit(text: str) -> str | None:
    norm = normalize_text(text)
    if not norm:
        return None
    for raw, kw in _PHRASES:
        if kw and kw in norm:
            return raw
    for ex in _EXCLUDE:
        norm = norm.replace(ex, " ")
    padded = f" {norm} "
    for raw, kw in _WORDS:
        if kw and f" {kw} " in padded:
            return raw
    return None


def mentions_it(text: str | None) -> bool:
    return _first_hit(text or "") is not None


def is_it_related(ann: RawAnnouncement) -> tuple[bool, str]:
    """Return (matched, reason). The reason names the field and keyword, or why not."""
    for field, value in (
        ("title", ann.title),
        ("grade", ann.grade),
        ("specialty", ann.specialty),
        ("text", ann.text),
    ):
        hit = _first_hit(value or "")
        if hit:
            return True, f"{field}: {hit}"
    return False, "no IT keyword in title, grade, specialty or text"


def log_rejected(ann: RawAnnouncement, reason: str) -> None:
    """Every rejected item is logged with its title so the keyword lists can be tuned."""
    log.info("rejected [%s] %s (%s)", ann.source_name, ann.title, reason)
