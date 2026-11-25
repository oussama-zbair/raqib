"""Posted-state store: ``state/posted.json`` (no database).

Layout::

    {"version": 1,
     "posted": [{"id", "reference_code", "administration", "grade", "post_count",
                 "deadline", "exam_date", "urls", "telegram_message_id", "posted_at"}],
     "rejected": {"<url>": "<YYYY-MM-DD first rejected>"}}

The workflow commits this file back to the repo after each run.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.db.models import RawAnnouncement
from app.jobs.dedup import Fingerprint, fingerprint, same_competition
from app.matching.normalizer import normalize_admin, normalize_text

DEFAULT_STATE_PATH = Path(__file__).resolve().parents[3] / "state" / "posted.json"
REJECTED_TTL_DAYS = 45


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


class PostedState:
    def __init__(self, path: Path = DEFAULT_STATE_PATH):
        self.path = Path(path)
        self.posted: list[dict] = []
        self.stages: list[dict] = []
        self.rejected: dict[str, str] = {}
        if self.path.exists() and self.path.read_text(encoding="utf-8").strip():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.posted = data.get("posted", [])
            self.stages = data.get("stages", [])
            self.rejected = data.get("rejected", {})

    # ---- stage posts (convocations, results) ----------------------------------------
    @staticmethod
    def stage_key(ann: RawAnnouncement) -> str:
        return f"{ann.reference_code or ann.source_url}#{ann.stage.value}"

    def knows_stage(self, ann: RawAnnouncement) -> bool:
        key = self.stage_key(ann)
        return any(s.get("key") == key for s in self.stages)

    def add_stage(self, ann: RawAnnouncement, message_id: int | None) -> dict:
        entry = {
            "key": self.stage_key(ann),
            "reference_code": ann.reference_code,
            "stage": ann.stage.value,
            "administration": ann.administration,
            "url": ann.source_url,
            "telegram_message_id": message_id,
            "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.stages.append(entry)
        return entry

    def thread_parent(self, ann: RawAnnouncement) -> int | None:
        """Message to reply to: the latest stage post of this concours, else its announcement."""
        code = ann.reference_code
        if not code:
            return None
        for s in reversed(self.stages):
            if s.get("reference_code") == code and s.get("telegram_message_id"):
                return s["telegram_message_id"]
        for e in self.posted:
            if e.get("reference_code") == code and e.get("telegram_message_id"):
                return e["telegram_message_id"]
        return None

    # ---- lookups -------------------------------------------------------------
    @staticmethod
    def _fp(entry: dict) -> Fingerprint:
        return Fingerprint(
            reference_code=entry.get("reference_code"),
            admin_norm=normalize_admin(entry.get("administration")),
            grade_norm=normalize_text(entry.get("grade")),
            deadline=_d(entry.get("deadline")),
            post_count=entry.get("post_count"),
            urls=set(entry.get("urls", [])),
        )

    def find(self, ann: RawAnnouncement) -> dict | None:
        fp = fingerprint(ann)
        for entry in self.posted:
            if same_competition(fp, self._fp(entry)):
                return entry
        return None

    def knows_url(self, url: str) -> bool:
        return url in self.rejected or any(url in e.get("urls", []) for e in self.posted)

    # ---- mutations -----------------------------------------------------------
    def add_posted(self, ann: RawAnnouncement, message_id: int | None) -> dict:
        entry = {
            "id": ann.reference_code or ann.source_url,
            "reference_code": ann.reference_code,
            "administration": ann.administration,
            "grade": ann.grade,
            "post_count": ann.post_count,
            "deadline": _iso(ann.deadline),
            "exam_date": _iso(ann.exam_date),
            "urls": sorted({u for u in (ann.source_url, ann.detail_url, ann.official_url) if u}),
            "telegram_message_id": message_id,
            "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.posted.append(entry)
        return entry

    def absorb(self, entry: dict, ann: RawAnnouncement) -> None:
        """Remember extra URLs and codes of a duplicate so it is skipped next time."""
        urls = set(entry.get("urls", []))
        urls |= {u for u in (ann.source_url, ann.detail_url, ann.official_url) if u}
        entry["urls"] = sorted(urls)
        if not entry.get("reference_code") and ann.reference_code:
            entry["reference_code"] = ann.reference_code

    def changes(self, entry: dict, ann: RawAnnouncement) -> dict[str, date]:
        """Deadline / exam date values that differ from what was posted (new value known)."""
        out: dict[str, date] = {}
        for key in ("deadline", "exam_date"):
            new = getattr(ann, key)
            if new is not None and new != _d(entry.get(key)):
                out[key] = new
        return out

    def apply_changes(self, entry: dict, changes: dict[str, date]) -> None:
        for key, value in changes.items():
            entry[key] = value.isoformat()

    def reject(self, url: str) -> None:
        self.rejected.setdefault(url, date.today().isoformat())

    # ---- persistence ---------------------------------------------------------
    def save(self) -> None:
        cutoff = (date.today() - timedelta(days=REJECTED_TTL_DAYS)).isoformat()
        self.rejected = {u: d for u, d in self.rejected.items() if d >= cutoff}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"version": 1, "posted": self.posted, "stages": self.stages,
             "rejected": self.rejected},
            ensure_ascii=False,
            indent=2,
        )
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload + "\n")
        os.replace(tmp, self.path)
