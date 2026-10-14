"""Digest job (cron, daily).

Drains the digest_queue: for each user with pending matched competitions, send a
Telegram digest, then mark the items as sent.

Run: ``python -m app.jobs.digest``
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from app.db.client import SupabaseClient
from app.db.models import Competition
from app.notify.telegram import send_digest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("digest")


def _telegram_id(db: SupabaseClient, user_id: int) -> int | None:
    rows = db.select(
        "users", columns="telegram_user_id", filters={"id": f"eq.{user_id}"}, limit=1
    )
    return rows[0]["telegram_user_id"] if rows else None


def run() -> None:
    db = SupabaseClient()
    try:
        pending = db.select(
            "digest_queue",
            columns="id,user_id,competition_id,competitions(*)",
            filters={"sent": "eq.false"},
        )
        if not pending:
            log.info("no pending digest items")
            return

        by_user: dict[int, list[dict]] = defaultdict(list)
        for row in pending:
            by_user[row["user_id"]].append(row)

        now = datetime.now(timezone.utc).isoformat()
        for user_id, items in by_user.items():
            chat_id = _telegram_id(db, user_id)
            if chat_id is None:
                continue
            comps = [Competition(**item["competitions"]) for item in items if item.get("competitions")]
            try:
                send_digest(chat_id, comps)
            except Exception as exc:  # noqa: BLE001
                log.warning("failed to send digest to %s: %s", chat_id, exc)
                continue
            # Mark this user's items as sent.
            for item in items:
                db.update(
                    "digest_queue",
                    {"sent": True, "sent_at": now},
                    filters={"id": f"eq.{item['id']}"},
                )
            log.info("sent %d competitions to user %s", len(comps), user_id)
    finally:
        db.close()


if __name__ == "__main__":
    run()
