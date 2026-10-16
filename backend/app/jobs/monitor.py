"""Lifecycle monitor job (cron) — the critical PDF roll-call.

For each tracked competition, check whether a convocation/results PDF is available. If
so, download it and search for the candidate's CIN (decrypted in memory only). On a hit,
send an urgent alert with the seat details; otherwise notify "not detected".

Run: ``python -m app.jobs.monitor``
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.db.client import SupabaseClient
from app.db.models import Competition, RollCallHit
from app.notify.telegram import send_convocation_not_found, send_urgent_convocation
from app.pdf.rollcall import inspect_pdf
from app.security.crypto import decrypt_cin

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("monitor")


def _telegram_id(db: SupabaseClient, user_id: int) -> int | None:
    rows = db.select(
        "users", columns="telegram_user_id", filters={"id": f"eq.{user_id}"}, limit=1
    )
    return rows[0]["telegram_user_id"] if rows else None


def _profile(db: SupabaseClient, user_id: int) -> dict | None:
    rows = db.select(
        "profiles",
        columns="cin_encrypted,full_name_fr,full_name_ar",
        filters={"user_id": f"eq.{user_id}"},
        limit=1,
    )
    return rows[0] if rows else None


def run() -> None:
    db = SupabaseClient()
    try:
        tracked = db.select(
            "tracked_competitions",
            columns="*,competitions(*)",
            filters={"notified_convocation": "eq.false"},
        )
        log.info("tracked competitions to check: %d", len(tracked))

        for t in tracked:
            comp_row = t.get("competitions")
            if not comp_row:
                continue
            comp = Competition(**comp_row)
            pdf_url = comp.convocation_pdf_url or comp.results_pdf_url
            if not pdf_url:
                continue  # no list published yet

            prof = _profile(db, t["user_id"])
            chat_id = _telegram_id(db, t["user_id"])
            # Need at least one identifier (CIN or a name) and a chat to notify.
            has_cin = bool(prof and prof.get("cin_encrypted"))
            has_name = bool(prof and (prof.get("full_name_fr") or prof.get("full_name_ar")))
            if not prof or chat_id is None or not (has_cin or has_name):
                continue

            # Decrypt CIN in memory only, at roll-call time (if present).
            cin = decrypt_cin(prof["cin_encrypted"]) if has_cin else ""
            candidates = [{
                "cin": cin,
                "full_name_fr": prof.get("full_name_fr") or "",
                "full_name_ar": prof.get("full_name_ar") or "",
            }]

            try:
                results = inspect_pdf(pdf_url, candidates)
            except Exception as exc:  # noqa: BLE001
                log.warning("roll-call failed for %s: %s", pdf_url, exc)
                continue

            result = results[0] if results else None
            now = datetime.now(timezone.utc).isoformat()

            if isinstance(result, RollCallHit) and result.found:
                send_urgent_convocation(chat_id, comp, result)
                db.update(
                    "tracked_competitions",
                    {
                        "state": "CONVOQUE",
                        "notified_convocation": True,
                        "last_checked_at": now,
                        "last_pdf_url": pdf_url,
                        "rollcall_result": result.model_dump(),
                    },
                    filters={"id": f"eq.{t['id']}"},
                )
                log.info("CONVOCATION HIT for user %s (table %s)", t["user_id"], result.table)
            else:
                send_convocation_not_found(chat_id, comp)
                db.update(
                    "tracked_competitions",
                    {
                        "notified_convocation": True,
                        "last_checked_at": now,
                        "last_pdf_url": pdf_url,
                        "rollcall_result": {"found": False},
                    },
                    filters={"id": f"eq.{t['id']}"},
                )
                log.info("not detected for user %s", t["user_id"])
    finally:
        db.close()


if __name__ == "__main__":
    run()
