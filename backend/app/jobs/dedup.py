"""Cross-source dedup for the channel publisher.

A ``Fingerprint`` is the small identity of one competition. It is built from a
``RawAnnouncement`` or from a ``state/posted.json`` entry, so a new item can be compared
with both the other items of the same run and everything posted earlier.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

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


def fingerprint(ann: RawAnnouncement) -> Fingerprint:
    return Fingerprint(
        reference_code=ann.reference_code,
        admin_norm=normalize_admin(ann.administration),
        grade_norm=normalize_text(ann.grade),
        deadline=ann.deadline,
        post_count=ann.post_count,
        urls={u for u in (ann.source_url, ann.detail_url, ann.official_url) if u},
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


_MERGE_FIELDS = (
    "administration", "grade", "specialty", "post_count", "deadline", "exam_date",
    "logo_url", "reference_code", "official_url", "title",
)


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
