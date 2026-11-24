"""Channel publisher: Wadifa-style Arabic posts sent to a public Telegram channel.

The bot (admin of the channel) posts with ``sendPhoto`` + caption when a logo exists and
falls back to ``sendMessage``. Telegram allows about 20 messages per minute to a channel,
so sends are spaced and 429 answers are retried after ``retry_after``.
"""
from __future__ import annotations

import html
import logging
import time
from datetime import date

import httpx

from app.db.models import RawAnnouncement
from app.matching.it_filter import mentions_it
from app.notify.telegram import _post

log = logging.getLogger("channel")

PLACEHOLDER_CHANNEL = "@RaqibEmploi"  # only used to print the footer in dry runs
EXAM_TBD = "سيتم الإعلان عنه لاحقا"
SEND_INTERVAL_SECONDS = 3.5  # about 17 messages per minute
CAPTION_LIMIT = 1024
MAX_SPECIALTIES = 10
_MAX_RETRIES = 3


def _clean(text: str | None) -> str:
    """Escape for Telegram HTML. No em dash ever reaches a post (sources use them)."""
    value = (text or "").replace("\u2014", "-")
    return html.escape(" ".join(value.split()), quote=False)


def _fmt_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def channel_footer(channel_id: str | None, dry_run: bool = False) -> str | None:
    """'📢 t.me/RaqibEmploi' from TELEGRAM_CHANNEL_ID; None when unset (dry runs use a placeholder)."""
    channel = (channel_id or "").strip()
    if not channel and dry_run:
        channel = PLACEHOLDER_CHANNEL
    if not channel:
        return None
    return f"📢 t.me/{channel.lstrip('@')}"


def best_link(ann: RawAnnouncement) -> str:
    """Official link first, then the source page."""
    return ann.official_url or ann.detail_url or ann.source_url


def format_channel_post(
    ann: RawAnnouncement, channel_id: str | None = None, max_specialties: int = MAX_SPECIALTIES
) -> str:
    lines = ["🟢 إعلان توظيف جديد"]
    if ann.administration:
        lines.append(f"🏛 {_clean(ann.administration)}")
    if ann.post_count:
        lines.append(f"👥 عدد المناصب: {ann.post_count}")
    if ann.grade:
        lines.append(f"💼 الدرجة: {_clean(ann.grade)}")
    specialties = [s.strip() for s in (ann.specialty or "").split(" / ") if s.strip()]
    if specialties:
        lines.append("🛠 التخصصات المطلوبة:")
        if len(specialties) > max_specialties:
            # Truncating: keep the IT specialties visible (stable sort, IT first).
            specialties = sorted(specialties, key=lambda s: not mentions_it(s))
        for spec in specialties[:max_specialties]:
            lines.append(f"🔷 {_clean(spec)}")
        if len(specialties) > max_specialties:
            lines.append("🔷 ...")
    if ann.deadline:
        lines.append(f"⏳ آخر أجل للتسجيل: {_fmt_date(ann.deadline)}")
    lines.append(f"📅 تاريخ الاختبار الكتابي: {_fmt_date(ann.exam_date) or EXAM_TBD}")
    lines.append(f"🔗 اضغط هنا للتفاصيل: {html.escape(best_link(ann), quote=False)}")
    footer = channel_footer(channel_id)
    if footer:
        lines += ["", footer]
    return "\n".join(lines)


def format_for_send(ann: RawAnnouncement, channel_id: str | None = None) -> str:
    """Post text; trims the specialty list so a photo caption stays within 1024 characters."""
    text = format_channel_post(ann, channel_id)
    if ann.logo_url and len(text) > CAPTION_LIMIT:
        for keep in (5, 3, 1, 0):
            text = format_channel_post(ann, channel_id, max_specialties=keep)
            if len(text) <= CAPTION_LIMIT:
                break
    return text


def format_update_post(ann: RawAnnouncement, changes: dict[str, date], footer: str | None) -> str:
    lines = ["🔄 تحديث للإعلان"]
    if ann.administration:
        lines.append(f"🏛 {_clean(ann.administration)}")
    if "deadline" in changes:
        lines.append(f"⏳ آخر أجل للتسجيل: {_fmt_date(changes['deadline'])}")
    if "exam_date" in changes:
        lines.append(f"📅 تاريخ الاختبار الكتابي: {_fmt_date(changes['exam_date'])}")
    if footer:
        lines += ["", footer]
    return "\n".join(lines)


def _call(method: str, payload: dict) -> dict:
    """Bot API call, retrying on 429 after the delay Telegram asks for."""
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return _post(method, payload)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429 and attempt < _MAX_RETRIES:
                try:
                    wait = int(exc.response.json().get("parameters", {}).get("retry_after", 5))
                except Exception:  # noqa: BLE001
                    wait = 5
                log.warning("Telegram 429, waiting %ss", wait)
                time.sleep(wait + 1)
                continue
            raise
    raise RuntimeError("unreachable")


def send_post(
    ann: RawAnnouncement,
    text: str,
    channel_id: str,
    reply_to: int | None = None,
    with_button: bool = True,
) -> int:
    """Send one post and return its Telegram message id."""
    base: dict = {"chat_id": channel_id, "parse_mode": "HTML"}
    if with_button:
        base["reply_markup"] = {
            "inline_keyboard": [[{"text": "التفاصيل", "url": best_link(ann)}]]
        }
    if reply_to:
        base["reply_to_message_id"] = reply_to
        base["allow_sending_without_reply"] = True
    if ann.logo_url and with_button and len(text) <= CAPTION_LIMIT:
        try:
            res = _call("sendPhoto", {**base, "photo": ann.logo_url, "caption": text})
            return res["result"]["message_id"]
        except httpx.HTTPStatusError as exc:
            log.warning("sendPhoto failed (%s), falling back to text", exc.response.status_code)
    res = _call(
        "sendMessage", {**base, "text": text, "disable_web_page_preview": True}
    )
    return res["result"]["message_id"]
