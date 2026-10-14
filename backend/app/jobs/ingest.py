"""Ingest job (cron).

scrape -> (Gemini fallback when needed) -> normalize -> dedup -> upsert competitions
-> match against profiles -> enqueue digest items.

Run: ``python -m app.jobs.ingest``
"""

from __future__ import annotations

import logging

from app.db.client import SupabaseClient
from app.db.models import Competition, CompetitionStage, Profile
from app.jobs.pipeline import (
    competition_to_row,
    dedup_batch,
    raw_to_competition,
)
from app.matching.matcher import matches_profile
from app.scrapers.base import Scraper
from app.scrapers.emploi_public import EmploiPublicScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest")

# Registry of active scrapers. Add ministry/telegram scrapers here as they land.
SCRAPERS: list[Scraper] = [EmploiPublicScraper()]

# When deterministic parsing yields nothing useful, escalate to Gemini.
_MIN_USEFUL_TEXT = 40


def _load_profiles(db: SupabaseClient) -> list[tuple[int, Profile]]:
    """Return (telegram_user_id, Profile) for completed profiles."""
    rows = db.select(
        "profiles",
        columns="*,users(telegram_user_id)",
        filters={"onboarding_state": "eq.COMPLETE"},
    )
    out: list[tuple[int, Profile]] = []
    for r in rows:
        tg = (r.get("users") or {}).get("telegram_user_id")
        if tg is None:
            continue
        out.append((tg, Profile(**{k: v for k, v in r.items() if k != "users"})))
    return out


def run() -> None:
    db = SupabaseClient()
    try:
        # 1. Scrape all sources.
        raw_all = []
        for scraper in SCRAPERS:
            try:
                found = scraper.fetch()
                log.info("scraped %s: %d announcements", scraper.source_name, len(found))
                raw_all.extend(found)
            except Exception as exc:  # noqa: BLE001
                log.warning("scraper %s failed: %s", scraper.source_name, exc)

        # 2. Build canonical competitions (Gemini fallback for thin announcements).
        comps: list[Competition] = []
        for raw in raw_all:
            fields = None
            if len(raw.text.strip()) < _MIN_USEFUL_TEXT and raw.text.strip():
                try:
                    from app.extractors.gemini import extract_from_text

                    fields = extract_from_text(raw.text)
                except Exception as exc:  # noqa: BLE001 — fallback is best-effort
                    log.debug("gemini fallback skipped: %s", exc)
            comps.append(raw_to_competition(raw, fields))

        # 3. Deduplicate within the batch.
        comps = dedup_batch(comps)
        log.info("canonical competitions: %d", len(comps))

        # 4. Upsert (merge-duplicates on canonical_hash) and read back ids.
        if not comps:
            return
        rows = [competition_to_row(c) for c in comps]
        saved = db.upsert("competitions", rows, on_conflict="canonical_hash")
        by_hash = {r["canonical_hash"]: r for r in saved}
        for c in comps:
            r = by_hash.get(c.canonical_hash)
            if r:
                c.id = r["id"]

        # 5. Match new AVIS competitions to profiles -> digest queue.
        profiles = _load_profiles(db)
        log.info("profiles to match: %d", len(profiles))
        queued = 0
        for comp in comps:
            if comp.stage != CompetitionStage.AVIS or comp.id is None:
                continue
            for tg_user_id, profile in profiles:
                if matches_profile(comp, profile):
                    try:
                        db.upsert(
                            "digest_queue",
                            {
                                "user_id": profile.user_id,
                                "competition_id": comp.id,
                            },
                            on_conflict="user_id,competition_id",
                        )
                        queued += 1
                    except Exception as exc:  # noqa: BLE001
                        log.debug("digest enqueue skipped: %s", exc)
        log.info("digest items queued: %d", queued)
    finally:
        db.close()


if __name__ == "__main__":
    run()
