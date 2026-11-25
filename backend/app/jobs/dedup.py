"""Cross-source dedup for the channel publisher.

A ``Fingerprint`` is the small identity of one competition. It is built from a
``RawAnnouncement`` or from a ``state/posted.json`` entry, so a new item can be compared
with both the other items of the same run and everything posted earlier.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import unquote

from app.db.models import RawAnnouncement
from app.matching.normalizer import canonical_hash, normalize_admin, normalize_text

# Priority when merging fields from several sources (first wins).
SOURCE_PRIORITY = ["emploi-public.ma", "wadifapublic.ma", "dreamjob.ma"]
_MIN_FUZZY_ADMIN_LEN = 10


@dataclass
class Fingerprint:
    reference_code: str | None = None
    admin_norm: str = ""
    grade_norm: str = ""
    deadline: date | None = None
    post_count: int | None = None
    urls: set[str] = field(default_factory=set)

    @property
    def hash(self) -> str | None:
        if not (self.admin_norm and self.grade_norm and self.deadline):
            return None
        return canonical_hash(self.admin_norm, self.grade_norm, self.deadline)


_EP_UUID = re.compile(
    r"emploi-public\.ma/.*?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
)


def canonical_url(url: str) -> str:
    """emploi-public.ma pages of one concours (FR, AR, any stage) share one id."""
    m = _EP_UUID.search(unquote(url or ""))
    return f"ep:{m.group(1)}" if m else url


def url_keys(urls) -> set[str]:
    return {canonical_url(u) for u in urls if u}


def fingerprint(ann: RawAnnouncement) -> Fingerprint:
    return Fingerprint(
        reference_code=ann.reference_code,
        admin_norm=normalize_admin(ann.administration),
        grade_norm=normalize_text(ann.grade),
        deadline=ann.deadline,
        post_count=ann.post_count,
        urls=url_keys((ann.source_url, ann.detail_url, ann.official_url)),
    )


def _admin_close(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = sorted((a, b), key=len)
    return len(short) >= _MIN_FUZZY_ADMIN_LEN and short in long_


def same_competition(a: Fingerprint, b: Fingerprint) -> bool:
    if a.urls & b.urls:
        return True
    if a.reference_code and b.reference_code:
        return a.reference_code == b.reference_code
    if a.hash and a.hash == b.hash:
        return True
    if a.deadline and a.deadline == b.deadline and _admin_close(a.admin_norm, b.admin_norm):
        # Same administration and same deadline: only a different grade tells them apart.
        if a.grade_norm and b.grade_norm and a.grade_norm != b.grade_norm:
            return False
        return a.post_count is None or b.post_count is None or a.post_count == b.post_count
    if (a.deadline is None) != (b.deadline is None) or a.deadline is None:
        # One side has no deadline (dreamjob feed): administration + post count.
        return (
            a.post_count is not None
            and a.post_count == b.post_count
            and _admin_close(a.admin_norm, b.admin_norm)
        )
    return False


def _rank(ann: RawAnnouncement) -> int:
    try:
        return SOURCE_PRIORITY.index(ann.source_name)
    except ValueError:
        return len(SOURCE_PRIORITY)


# Facts: the official portal wins.
_MERGE_FIELDS = (
    "post_count", "deadline", "exam_date", "reference_code", "official_url",
    "published", "list_pdf_url",
)
# Wording: taken from one source so a post never mixes French and Arabic. Arabic first
# (the channel is Arabic), the logo too (wadifapublic.ma logos are the cleanest).
_TEXT_FIELDS = ("administration", "grade", "specialty", "title", "city", "logo_url")
TEXT_PRIORITY = ["wadifapublic.ma", "emploi-public.ma", "dreamjob.ma"]


def _is_arabic(text: str | None) -> bool:
    return any("\u0600" <= ch <= "\u06ff" for ch in (text or ""))


def _text_rank(ann: RawAnnouncement) -> int:
    try:
        return TEXT_PRIORITY.index(ann.source_name)
    except ValueError:
        return len(TEXT_PRIORITY)


def merge_group(items: list[RawAnnouncement]) -> RawAnnouncement:
    """Merge duplicates into one announcement; the best-ranked source wins per field."""
    ordered = sorted(items, key=_rank)
    primary = ordered[0]
    update: dict = {}
    for name in _MERGE_FIELDS:
        for it in ordered:
            value = getattr(it, name)
            if value not in (None, ""):
                update[name] = value
                break
    by_text = sorted(items, key=_text_rank)
    wording = next((it for it in by_text if it.administration), by_text[0])
    arabic = _is_arabic(wording.administration)
    for name in _TEXT_FIELDS:
        value = getattr(wording, name)
        if value in (None, "") and name != "logo_url":
            # Fill a gap only with text in the same script as the chosen wording.
            value = next(
                (getattr(it, name) for it in by_text
                 if getattr(it, name) and _is_arabic(getattr(it, name)) == arabic),
                None,
            )
        if value in (None, "") and name == "logo_url":
            value = next((it.logo_url for it in by_text if it.logo_url), None)
        update[name] = value
    update["lang"] = "ar" if arabic else "fr"
    # Best link to the official page: an explicit official_url, else the portal's own page.
    if not update.get("official_url"):
        portal = next((it for it in ordered if it.source_name == "emploi-public.ma"), None)
        if portal:
            update["official_url"] = portal.detail_url or portal.source_url
    return primary.model_copy(update=update)


def dedup_items(items: list[RawAnnouncement]) -> list[list[RawAnnouncement]]:
    """Group items that describe the same competition. Group order follows first sight."""
    groups: list[list[RawAnnouncement]] = []
    prints: list[list[Fingerprint]] = []
    for it in items:
        fp = fingerprint(it)
        for g, gp in zip(groups, prints):
            if any(same_competition(fp, other) for other in gp):
                g.append(it)
                gp.append(fp)
                break
        else:
            groups.append([it])
            prints.append([fp])
    return groups
