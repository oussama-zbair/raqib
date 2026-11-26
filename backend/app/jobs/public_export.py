"""state/public.json: the website's data, written after each real run.

Only public facts about concours (no Telegram ids, no internal bookkeeping). The site
reads this file straight from GitHub in the browser, so it is always as fresh as the
last run and needs no database or server.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.db.models import CompetitionStage, RawAnnouncement, SourceType
from app.jobs.dedup import canonical_url, url_keys
from app.jobs.posted_state import PostedState
from app.matching.domains import field_tags
from app.matching.job_title import job_family, job_title, scale_of

KEEP_CLOSED_DAYS = 30  # closed concours stay listed this long (their stages still matter)
UPDATES_DAYS = 30
STAGE_ORDER = [s.value for s in CompetitionStage]


def _tags(entry: dict) -> list[str]:
    ann = RawAnnouncement(
        source_name="x", source_type=SourceType.PORTAL, source_url="x",
        grade=entry.get("grade"), specialty=entry.get("specialty"), title=entry.get("grade"),
    )
    return field_tags(ann)


def build(state: PostedState, last_run: dict) -> dict:
    today = date.today()
    keep_from = (today - timedelta(days=KEEP_CLOSED_DAYS)).isoformat()
    stages_by_key: dict[str, list[dict]] = {}
    for s in state.stages:
        stages_by_key.setdefault(s["key"].split("#")[0], []).append(s)

    concours = []
    for e in state.posted:
        if (e.get("deadline") or "9999") < keep_from:
            continue
        keys = url_keys(e.get("urls", []))
        key = next((k for k in keys if k.startswith("ep:")), None)
        timeline = sorted({s["stage"] for k in keys for s in stages_by_key.get(k, [])},
                          key=STAGE_ORDER.index)
        concours.append({
            "id": key or e.get("id"),
            "code": e.get("reference_code"),
            "administration": e.get("administration"),
            "grade": e.get("grade"),
            "title": job_title(e.get("grade")),
            "family": job_family(job_title(e.get("grade"))),
            "scale": scale_of(e.get("grade")),
            "specialty": e.get("specialty"),
            "posts": e.get("post_count"),
            "deadline": e.get("deadline"),
            "exam_date": e.get("exam_date"),
            "city": e.get("city"),
            "logo": e.get("logo_url"),
            "url": e.get("official_url") or next(iter(e.get("urls", [])), None),
            "tags": _tags(e),
            "stages": ["AVIS", *timeline],
            "posted_at": e.get("posted_at"),
        })
    concours.sort(key=lambda c: c.get("posted_at") or "", reverse=True)

    since = (datetime.now(timezone.utc) - timedelta(days=UPDATES_DAYS)).isoformat()
    updates = [
        {
            "id": s["key"].split("#")[0],
            "stage": s["stage"],
            "administration": s.get("administration"),
            "grade": s.get("grade"),
            "title": job_title(s.get("grade")),
            "family": job_family(job_title(s.get("grade"))),
            "exam_date": s.get("exam_date"),
            "city": s.get("city"),
            "logo": s.get("logo_url"),
            "pdf": s.get("list_pdf_url"),
            "url": s.get("url"),
            "posted_at": s.get("posted_at"),
        }
        for s in state.stages
        if not s.get("seeded") and (s.get("posted_at") or "") >= since
    ]
    updates.sort(key=lambda u: u.get("posted_at") or "", reverse=True)

    open_count = sum(1 for c in concours if (c.get("deadline") or "9999") >= today.isoformat())
    return {
        "updated_at": last_run.get("finished_at"),
        "channel": "https://t.me/RaqibEmploi",
        "sources": [
            {"name": name, "url": f"https://www.{name}", "status": status}
            for name, status in (last_run.get("sources") or {}).items()
        ],
        "stats": {
            "open": open_count,
            "posted_total": len(state.posted),
            "stage_posts_total": sum(1 for s in state.stages if not s.get("seeded")),
            "followed": len(state.tracked),
        },
        "concours": concours,
        "updates": updates,
    }


def write(state: PostedState, last_run: dict, path: Path) -> None:
    payload = json.dumps(build(state, last_run), ensure_ascii=False, indent=1)
    Path(path).write_text(payload + "\n", encoding="utf-8")


__all__ = ["build", "write", "canonical_url"]
