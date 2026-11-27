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
from app.jobs.dedup import Fingerprint, canonical_url, fingerprint, same_competition, url_keys
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
        self.seeded_sources: list[str] = []
        self.tracked: dict[str, dict] = {}
        self.last_discovery: str | None = None
        self.send_failures: dict[str, int] = {}
        self.last_digest_slot: str | None = None  # WhatsApp digest, e.g. "2026-11-26-am"
        self.last_digest_at: str | None = None
        if self.path.exists() and self.path.read_text(encoding="utf-8").strip():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.posted = data.get("posted", [])
            self.stages = data.get("stages", [])
            self.rejected = data.get("rejected", {})
            self.seeded_sources = data.get("seeded_sources", [])
            self.tracked = data.get("tracked", {})
            self.last_discovery = data.get("last_discovery")
            self.send_failures = data.get("send_failures", {})
            self.last_digest_slot = data.get("last_digest_slot")
            self.last_digest_at = data.get("last_digest_at")

    # ---- send failures (a post Telegram refuses is retried, then dropped) -------------
    MAX_SEND_FAILURES = 3

    def note_failure(self, key: str) -> int:
        self.send_failures[key] = self.send_failures.get(key, 0) + 1
        return self.send_failures[key]

    def clear_failure(self, key: str) -> None:
        self.send_failures.pop(key, None)

    def gave_up(self, key: str) -> bool:
        if self.send_failures.get(key, 0) >= self.MAX_SEND_FAILURES:
            self.send_failures.pop(key, None)
            return True
        return False

    # ---- followed concours (their page is re-read for new documents) ------------------
    TRACK_DAYS = 200
    RECHECK_HOURS = 2

    def track(self, key: str, baseline_known: bool) -> None:
        """Follow a concours. ``baseline_known``: we know it has no stage document yet
        (a fresh announcement), so anything found later is new and gets posted."""
        if not key.startswith("ep:") or key in self.tracked:
            return
        self.tracked[key] = {
            "added": date.today().isoformat(),
            "checked": datetime.now(timezone.utc).isoformat(timespec="seconds")
            if baseline_known else None,
        }

    def due_tracked(self, limit: int) -> list[str]:
        """Concours to re-read now: never checked first, then the oldest check."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=self.RECHECK_HOURS)).isoformat()
        due = [k for k, v in self.tracked.items() if not v.get("checked") or v["checked"] < cutoff]
        due.sort(key=lambda k: self.tracked[k].get("checked") or "")
        return due[:limit]

    def first_check(self, key: str) -> bool:
        return not self.tracked.get(key, {}).get("checked")

    def mark_checked(self, key: str) -> None:
        if key in self.tracked:
            self.tracked[key]["checked"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _expire_tracked(self) -> None:
        cutoff = (date.today() - timedelta(days=self.TRACK_DAYS)).isoformat()
        done = {s["key"].split("#")[0] for s in self.stages if s.get("stage") == "RESULTATS"}
        self.tracked = {k: v for k, v in self.tracked.items()
                        if v.get("added", "") >= cutoff and k not in done}

    # ---- stage posts (convocations, results) ----------------------------------------
    @staticmethod
    def stage_key(ann: RawAnnouncement) -> str:
        """Stable before and after the detail fetch: the portal id, never the code."""
        return f"{canonical_url(ann.source_url)}#{ann.stage.value}"

    def knows_stage(self, ann: RawAnnouncement) -> bool:
        key = self.stage_key(ann)
        return any(s.get("key") == key for s in self.stages)

    def add_stage(self, ann: RawAnnouncement, message_id: int | None, seeded: bool = False) -> dict:
        entry = {
            "key": self.stage_key(ann),
            "reference_code": ann.reference_code,
            "stage": ann.stage.value,
            "administration": ann.administration,
            "url": ann.source_url,
            "telegram_message_id": message_id,
            "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        if not seeded:  # posted stages appear on the website
            entry.update({"grade": ann.grade, "list_pdf_url": ann.list_pdf_url,
                          "exam_date": _iso(ann.exam_date), "city": ann.city,
                          "logo_url": ann.logo_url})
        if seeded:
            entry["seeded"] = True  # already online before we watched: never posted
        self.stages.append(entry)
        return entry

    def thread_parent(self, ann: RawAnnouncement) -> int | None:
        """Message to reply to: the latest stage post of this concours, else its announcement."""
        code = ann.reference_code
        key = canonical_url(ann.source_url)

        def same(entry_code, entry_urls) -> bool:
            return bool((code and entry_code == code) or key in url_keys(entry_urls))

        for s in reversed(self.stages):
            if s.get("telegram_message_id") and same(s.get("reference_code"), [s.get("url")]):
                return s["telegram_message_id"]
        for e in self.posted:
            if e.get("telegram_message_id") and same(e.get("reference_code"), e.get("urls", [])):
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
            urls=url_keys(entry.get("urls", [])),
        )

    def find(self, ann: RawAnnouncement) -> dict | None:
        fp = fingerprint(ann)
        for entry in self.posted:
            if same_competition(fp, self._fp(entry)):
                return entry
        return None

    def knows_url(self, url: str) -> bool:
        if url in self.rejected:
            return True
        key = canonical_url(url)
        return any(key in url_keys(e.get("urls", [])) for e in self.posted)

    def is_rejected(self, url: str) -> bool:
        return url in self.rejected

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
            # Shown on the website (state/public.json).
            "specialty": ann.specialty,
            "city": ann.city,
            "logo_url": ann.logo_url,
            "official_url": ann.official_url or ann.detail_url or ann.source_url,
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
        self._expire_tracked()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"version": 1, "posted": self.posted, "stages": self.stages,
             "seeded_sources": self.seeded_sources, "tracked": self.tracked,
             "last_discovery": self.last_discovery, "send_failures": self.send_failures,
             "last_digest_slot": self.last_digest_slot, "last_digest_at": self.last_digest_at,
             "rejected": self.rejected},
            ensure_ascii=False,
            indent=2,
        )
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload + "\n")
        os.replace(tmp, self.path)
