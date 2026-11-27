"""WhatsApp digest: a ready-to-paste summary sent to the owner on Telegram.

WhatsApp has no API to post to a Channel, so the job prepares the post and the owner
pastes it (one tap copies a Telegram code block). Twice a day, Morocco time:

* from 09:00: everything published since the previous digest (the night's items);
* from 18:00: everything published during the day.

A slot that was missed (no run, Telegram down) is sent by the next run. Nothing new
means no message. WhatsApp formatting: *bold*, plain links (Telegram links are useless
to people without Telegram, so every line points to the official concours page).
"""
from __future__ import annotations

import html
import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.jobs.dedup import canonical_url, url_keys
from app.jobs.posted_state import PostedState
from app.matching.job_title import job_title
from app.notify.channel import AR_DAYS, AR_MONTHS, fmt_posts

log = logging.getLogger("whatsapp_digest")

TZ = ZoneInfo("Africa/Casablanca")
MORNING_HOUR, EVENING_HOUR = 9, 18
FIRST_DIGEST_HOURS = 12  # the very first digest covers the last 12 hours
PART_LIMIT = 3500  # Telegram allows 4096 characters per message
OFFICIAL = "https://www.emploi-public.ma/fr/concours/details/{uuid}"

STAGE_SECTIONS = [
    ("CONVOQUES", "📋 *لوائح المدعوين للكتابي*"),
    ("CONVOQUES_ORAL", "🎤 *لوائح المدعوين للشفوي*"),
    ("RESULTATS", "🏆 *النتائج النهائية*"),
]


def due_slot(now: datetime) -> str:
    """The latest digest slot that has started, e.g. '2026-11-26-am'."""
    local = now.astimezone(TZ)
    if local.hour >= EVENING_HOUR:
        return f"{local.date().isoformat()}-pm"
    if local.hour >= MORNING_HOUR:
        return f"{local.date().isoformat()}-am"
    return f"{(local.date() - timedelta(days=1)).isoformat()}-pm"


def _link(urls) -> str | None:
    key = next((k for k in url_keys(urls) if k.startswith("ep:")), None)
    return OFFICIAL.format(uuid=key[3:]) if key else next(iter(urls), None)


def _short_date(iso: str | None) -> str:
    if not iso:
        return ""
    d = date.fromisoformat(iso)
    return f"{d.day} {AR_MONTHS[d.month - 1]}"


def _one_line(text: str | None) -> str:
    return " ".join((text or "").split())


def _announcement_block(e: dict) -> str:
    title = job_title(e.get("grade")) or _one_line(e.get("grade"))
    lines = [f"💼 *{title}* · {_one_line(e.get('administration'))}"]
    facts = []
    if e.get("deadline"):
        facts.append(f"⏳ آخر أجل: {_short_date(e['deadline'])}")
    if e.get("post_count"):
        facts.append(f"👥 {fmt_posts(e['post_count'], 'ar')}")
    if e.get("city"):
        facts.append(f"📍 {e['city']}")
    if facts:
        lines.append(" · ".join(facts))
    link = _link(e.get("urls", []))
    if link:
        lines.append(f"🔗 {link}")
    return "\n".join(lines)


def _stage_block(s: dict) -> str:
    title = job_title(s.get("grade")) or _one_line(s.get("grade"))
    first = f"🏛 {_one_line(s.get('administration'))}"
    if title:
        first += f" · {title}"
    lines = [first]
    if s.get("exam_date") and s.get("stage") != "RESULTATS":
        lines.append(f"📅 تاريخ الاختبار: {_short_date(s['exam_date'])}")
    link = _link([s.get("url")] if s.get("url") else [])
    if link:
        lines.append(f"🔗 {link}")
    return "\n".join(lines)


def build_parts(state: PostedState, since: str, now: datetime, site: str, telegram: str) -> list[str]:
    """Digest text split into paste-sized parts. Empty list when nothing is new."""
    today = now.astimezone(TZ).date().isoformat()
    new = [e for e in state.posted
           if (e.get("posted_at") or "") > since and (e.get("deadline") or "9999") >= today]
    stages = [s for s in state.stages
              if not s.get("seeded") and s.get("telegram_message_id") is not None
              and (s.get("posted_at") or "") > since]
    if not new and not stages:
        return []
    new.sort(key=lambda e: e.get("deadline") or "9999")  # closing soonest first

    local = now.astimezone(TZ)
    moment = "الصباح" if local.hour < EVENING_HOUR else "المساء"
    header = (f"👁 *رقيب | ملخص المباريات*\n"
              f"📅 {AR_DAYS[local.weekday()]} {local.day} {AR_MONTHS[local.month - 1]} "
              f"{local.year} · {moment}")
    footer = (f"🌐 كل المباريات مع البحث: {site}/competitions\n"
              f"✈️ تيليجرام: {telegram}\n"
              f"🤝 شارك القناة مع من يبحث عن عمل")

    blocks: list[str] = []
    if new:
        blocks.append(f"🟢 *مباريات جديدة ({len(new)})*")
        blocks += [_announcement_block(e) for e in new]
    for stage, title in STAGE_SECTIONS:
        items = [s for s in stages if s.get("stage") == stage]
        if items:
            blocks.append(f"{title} ({len(items)})")
            blocks += [_stage_block(s) for s in items]

    parts: list[list[str]] = [[header]]
    size = len(header)
    for block in blocks:
        if size + len(block) + 2 > PART_LIMIT - len(footer):
            parts.append([])
            size = 0
        parts[-1].append(block)
        size += len(block) + 2
    parts[-1].append(footer)
    return ["\n\n".join(p) for p in parts]


def _send(chat_id: str, parts: list[str]) -> None:
    from app.notify.channel import _request

    total = len(parts)
    for i, part in enumerate(parts, 1):
        intro = ("📲 <b>ملخص واتساب</b>" + (f" ({i}/{total})" if total > 1 else "")
                 + "\nانسخ النص أسفله والصقه في قناة واتساب.")
        _request("sendMessage", {
            "chat_id": chat_id,
            "parse_mode": "HTML",
            "text": f"{intro}\n\n<pre>{html.escape(part, quote=False)}</pre>",
            "link_preview_options": {"is_disabled": True},
        })


def maybe_send(state: PostedState, chat_id: str, site: str, telegram: str,
               now: datetime | None = None, sender=_send) -> int:
    """Send the digest when a new slot has started. Returns the number of parts sent."""
    if not chat_id:
        return 0
    now = now or datetime.now(timezone.utc)
    slot = due_slot(now)
    if state.last_digest_slot == slot:
        return 0
    since = state.last_digest_at or (now - timedelta(hours=FIRST_DIGEST_HOURS)).isoformat(
        timespec="seconds")
    parts = build_parts(state, since, now, site, telegram)
    if parts:
        sender(chat_id, parts)
        log.info("whatsapp digest sent: %d part(s)", len(parts))
    # Advance even when empty: the next digest starts from here.
    state.last_digest_slot = slot
    state.last_digest_at = now.isoformat(timespec="seconds")
    state.save()
    return len(parts)


__all__ = ["build_parts", "due_slot", "maybe_send", "canonical_url"]
