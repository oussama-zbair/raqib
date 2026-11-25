"""Channel publish job (cron): scrape, filter IT, dedup, post to the Telegram channel.

Run: ``python -m app.jobs.publish_channel [--dry-run] [--state PATH] [--save-state]``

* Posted state lives in ``state/posted.json`` (no database).
* ``--dry-run`` prints the posts instead of sending them and leaves the state file
  untouched unless ``--save-state`` is given (use it with a temporary ``--state`` file).
* One failing source never stops the run.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from datetime import date
from pathlib import Path

from app.config import get_settings
from app.db.models import CompetitionStage, RawAnnouncement
from app.jobs.dedup import dedup_items, merge_group
from app.jobs.posted_state import DEFAULT_STATE_PATH, PostedState
from app.matching.it_filter import is_it_related, log_rejected
from app.notify.channel import (
    SEND_INTERVAL_SECONDS,
    channel_footer,
    format_for_send,
    format_update_post,
    send_post,
)
from app.scrapers.base import Scraper, make_client
from app.scrapers.dreamjob_ma import DreamjobScraper
from app.scrapers.emploi_public import EmploiPublicScraper
from app.scrapers.wadifapublic_ma import WadifaPublicScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# httpx logs full request URLs at INFO, and Telegram URLs contain the bot token.
for _noisy in ("httpx", "httpcore"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
log = logging.getLogger("publish_channel")

# wadifapublic.ma and dreamjob.ma answer GitHub's servers with HTTP 403 (bot protection),
# so they are not in the registry; their scrapers stay for local use and tests.
SCRAPERS: list[Scraper] = [EmploiPublicScraper()]
_UNUSED_IN_CI = (WadifaPublicScraper, DreamjobScraper)
MAX_POSTS_PER_RUN = 15
DETAIL_DELAY_SECONDS = 1.0
_SEP = "-" * 40


_NOT_AN_ANNOUNCEMENT = re.compile(
    r"liste\s+des\s+convoqu|candidats?\s+convoqu|convocation|r[eé]sultats?\b|liste\s+(principale|d.attente)"
    r"|لائحة|لوائح|نتائج|المدعوين|الناجحين|المقبولين",
    re.IGNORECASE,
)


def _is_announcement(it: RawAnnouncement) -> bool:
    """Convocation lists and results are not job announcements (later stage)."""
    if it.stage != CompetitionStage.AVIS:
        return False
    return not _NOT_AN_ANNOUNCEMENT.search(it.title or "")


STAGE_MAX_AGE_DAYS = 2  # sources with a publication date: never post older stage items


def _is_stage_item(it: RawAnnouncement) -> bool:
    return it.stage != CompetitionStage.AVIS


def _select_stages(
    items: list[RawAnnouncement], state: PostedState, scrapers: list[Scraper]
) -> list[RawAnnouncement]:
    """New stage items (convocations, results), enriched, oldest first.

    The first time a source is watched, every stage item it lists is recorded as seen
    and nothing is posted: those lists were published before the channel existed.
    A convocation whose exam date is already past is recorded and skipped.
    """
    by_source = {s.source_name: s for s in scrapers}
    cutoff = date.fromordinal(date.today().toordinal() - STAGE_MAX_AGE_DAYS)
    picked: dict[str, RawAnnouncement] = {}
    for it in items:
        key = state.stage_key(it)
        if key in picked or state.knows_stage(it):
            continue
        if (it.feed or it.source_name) not in state.seeded_sources:
            state.add_stage(it, None, seeded=True)
            continue
        if it.published is not None and it.published < cutoff:
            continue
        if (it.stage == CompetitionStage.CONVOQUES and it.exam_date
                and it.exam_date < date.today()):
            state.add_stage(it, None, seeded=True)
            continue
        picked[key] = it
    for name in {it.feed or it.source_name for it in items}:
        if name not in state.seeded_sources:
            state.seeded_sources.append(name)
            log.info("first watch of %s stages: recorded without posting", name)
    out: list[RawAnnouncement] = []
    with make_client() as client:
        for it in picked.values():
            enrich = getattr(by_source.get(it.source_name), "enrich", None)
            if enrich:
                it = enrich(it, client)
                time.sleep(DETAIL_DELAY_SECONDS)
            out.append(it)
    # Listings are newest first; keep that order reversed so the channel reads in time order.
    out.reverse()
    return out


def _why(exc: Exception) -> str:
    """Short failure reason, e.g. 'HTTP 403' (unwraps tenacity's RetryError)."""
    last = getattr(exc, "last_attempt", None)
    if last is not None and last.exception() is not None:
        exc = last.exception()
    resp = getattr(exc, "response", None)
    if resp is not None:
        return f"HTTP {resp.status_code}"
    return type(exc).__name__


def _scrape(scrapers: list[Scraper]) -> tuple[list[RawAnnouncement], dict[str, str]]:
    """Fetch every source in isolation. Returns items and a per-source status."""
    items: list[RawAnnouncement] = []
    status: dict[str, str] = {}
    for scraper in scrapers:
        try:
            found = scraper.fetch()
            # Listing pages can repeat items. One concours page serves every stage on
            # emploi-public.ma, so an item is its URL *and* its stage.
            seen = {(i.source_url, i.stage) for i in items}
            for i in found:
                if (i.source_url, i.stage) not in seen:
                    seen.add((i.source_url, i.stage))
                    items.append(i)
            status[scraper.source_name] = f"ok ({len(found)} items)"
        except Exception as exc:  # noqa: BLE001
            log.exception("source %s failed", scraper.source_name)
            status[scraper.source_name] = f"FAILED ({_why(exc)})"
    return items, status


def _select_it(
    items: list[RawAnnouncement],
    state: PostedState,
    scrapers: list[Scraper],
    it_only: bool = False,
) -> tuple[list[RawAnnouncement], list[RawAnnouncement]]:
    """Return (IT items to consider, items already posted by URL).

    Items whose URL is known (posted or rejected earlier) cost nothing. New items are
    filtered on listing data; those the listing cannot judge (no specialty) are enriched
    from the detail page first. Items that pass are enriched for exam date and links.
    """
    by_source = {s.source_name: s for s in scrapers}
    fresh: list[RawAnnouncement] = []
    known_posted: list[RawAnnouncement] = []
    for it in items:
        if state.knows_url(it.source_url) or (it.detail_url and state.knows_url(it.detail_url)):
            if it.source_url not in state.rejected:
                known_posted.append(it)
            continue
        if not _is_announcement(it):
            state.reject(it.source_url)
            continue
        if it.deadline and it.deadline < date.today():
            state.reject(it.source_url)  # deadline passed, never post
            continue
        if not (it.grade or it.deadline):
            # Too thin for a card (dreamjob feed): kept only to confirm other sources.
            known_posted.append(it)
            continue
        fresh.append(it)

    selected: list[RawAnnouncement] = []
    with make_client() as client:
        for it in fresh:
            scraper = by_source.get(it.source_name)
            enrich = getattr(scraper, "enrich", None)
            enriched = it
            fetched = False
            ok, reason = is_it_related(it)
            if not ok and it.specialty is None and enrich and it.source_name != "dreamjob.ma":
                enriched = enrich(it, client)
                fetched = True
                time.sleep(DETAIL_DELAY_SECONDS)
                if enriched == it:
                    log.info("detail fetch gave nothing for %s, will retry next run", it.source_url)
                    continue
                ok, reason = is_it_related(enriched)
            if not ok and it_only:
                log_rejected(enriched, reason)
                state.reject(it.source_url)
                continue
            if enrich and not fetched:
                enriched = enrich(it, client)
                time.sleep(DETAIL_DELAY_SECONDS)
            log.info("%s item [%s] %s (%s)", "IT" if ok else "other", it.source_name, it.title, reason)
            selected.append(enriched)
    return selected, known_posted


def run(
    dry_run: bool = False,
    state_path: Path = DEFAULT_STATE_PATH,
    save_state: bool = False,
    scrapers: list[Scraper] | None = None,
    sender=send_post,
    max_posts: int = MAX_POSTS_PER_RUN,
) -> dict:
    scrapers = scrapers if scrapers is not None else SCRAPERS
    settings = get_settings()
    channel = settings.telegram_channel_id.strip()
    if not dry_run and not (channel and settings.telegram_bot_token):
        raise SystemExit("TELEGRAM_CHANNEL_ID and TELEGRAM_BOT_TOKEN are required (or use --dry-run)")
    footer = channel_footer(channel, dry_run=dry_run)
    footer_channel = channel or ("@RaqibEmploi" if dry_run else "")

    state = PostedState(state_path)
    items, status = _scrape(scrapers)
    stage_items = [it for it in items if _is_stage_item(it)]
    items = [it for it in items if not _is_stage_item(it)]
    selected, known_posted = _select_it(items, state, scrapers, it_only=settings.publish_it_only)

    # Convocations and results first: their dates are close, they cannot wait a run.
    sent = 0
    for ann in _select_stages(stage_items, state, scrapers)[:max_posts]:
        text = format_for_send(ann)
        reply_to = state.thread_parent(ann)
        if dry_run:
            print(f"{text}\n[button: {ann.list_pdf_url or ann.source_url}] "
                  f"[reply to: {reply_to}] [image: {ann.logo_url or 'emblem'}]\n{_SEP}")
            message_id = None
        else:
            message_id = sender(ann, text, channel, reply_to=reply_to)
            time.sleep(SEND_INTERVAL_SECONDS)
        state.add_stage(ann, message_id)
        if not dry_run:
            state.save()
        sent += 1

    new_posts: list[RawAnnouncement] = []
    updates: list[tuple[dict, RawAnnouncement, dict]] = []
    for group in dedup_items(selected + known_posted):
        merged = merge_group(group)
        entry = state.find(merged)
        if entry is None:
            if any(g in selected for g in group):
                new_posts.append(merged)
            continue
        for g in group:
            state.absorb(entry, g)
        changes = state.changes(entry, merged)
        if changes:
            updates.append((entry, merged, changes))

    # Listings are newest first: post oldest first so the channel reads chronologically.
    new_posts.reverse()
    stage_sent = sent
    budget = max(0, max_posts - sent)
    for ann in new_posts[:budget]:
        text = format_for_send(ann, footer_channel)
        if dry_run:
            print(f"{text}\n[button: {ann.official_url or ann.source_url}] "
                  f"[image: {ann.logo_url or 'emblem'}] [sources: {ann.source_name}]\n{_SEP}")
            message_id = None
        else:
            message_id = sender(ann, text, channel)
            time.sleep(SEND_INTERVAL_SECONDS)
        state.add_posted(ann, message_id)
        if not dry_run:
            state.save()  # persist after every send so a later failure never causes a re-post
        sent += 1
    if len(new_posts) > budget:
        log.info("%d more items wait for the next run", len(new_posts) - budget)

    for entry, ann, changes in updates:
        text = format_update_post(ann, changes, footer)
        if dry_run:
            print(f"{text}\n[reply to message {entry.get('telegram_message_id')}]\n{_SEP}")
        else:
            reply_to = entry.get("telegram_message_id")
            sender(ann, text, channel, reply_to=reply_to, with_button=False)
            time.sleep(SEND_INTERVAL_SECONDS)
        state.apply_changes(entry, changes)
        if not dry_run:
            state.save()

    if (not dry_run) or save_state:
        state.save()
    summary = {
        "sources": status,
        "posts": sent,
        "stage_posts": stage_sent,
        "updates": len(updates),
        "dry_run": dry_run,
    }
    log.info("done: %s", summary)
    if not dry_run:
        _write_last_run(state_path, summary, items)
    return summary


def _write_last_run(state_path: Path, summary: dict, items: list[RawAnnouncement]) -> None:
    """state/last_run.json: what the last real run saw, readable without GitHub logs."""
    import json
    from datetime import datetime, timezone

    by_source: dict[str, dict[str, int]] = {}
    for it in items:
        s = by_source.setdefault(it.source_name, {})
        s[it.stage.value] = s.get(it.stage.value, 0) + 1
    payload = {
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **summary,
        "items_by_source_and_stage": by_source,
    }
    path = Path(state_path).with_name("last_run.json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Publish new concours to the Telegram channel.")
    parser.add_argument("--dry-run", action="store_true", help="print posts instead of sending")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH, help="posted state file")
    parser.add_argument(
        "--save-state", action="store_true", help="with --dry-run, still write the state file"
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run(dry_run=args.dry_run, state_path=args.state, save_state=args.save_state)


if __name__ == "__main__":
    main()
