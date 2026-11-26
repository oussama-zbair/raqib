"""Channel publisher: Raqib cards sent to the public Telegram channel.

Every post is a photo with a caption: the administration logo when we can download it,
otherwise the Moroccan coat of arms (``assets/morocco.png``). Images are downloaded and
uploaded as files, so Telegram never has to fetch an odd URL itself.

A card is written in one language only (Arabic when any source has Arabic wording,
else French), so lines never jump between right-to-left and left-to-right. Links live
in buttons, not in the text. Hashtags are always Arabic so one search finds every post.

Telegram allows about 20 messages per minute to a channel, so sends are spaced and 429
answers are retried after ``retry_after``. Errors never include the request URL, which
contains the bot token.
"""
from __future__ import annotations

import html
import logging
import time
from datetime import date
from pathlib import Path

import httpx

from app.config import get_settings
from app.db.models import CompetitionStage, RawAnnouncement
from app.matching.domains import hashtags
from app.matching.it_filter import mentions_it
from app.scrapers.base import make_client

log = logging.getLogger("channel")

PLACEHOLDER_CHANNEL = "@RaqibEmploi"  # only used to print the footer in dry runs
SEND_INTERVAL_SECONDS = 3.5  # about 17 messages per minute
CAPTION_LIMIT = 1024
MAX_SPECIALTIES = 6
MAX_IMAGE_BYTES = 5 * 1024 * 1024
EMBLEM_PATH = Path(__file__).parent / "assets" / "morocco.png"
_MAX_RETRIES = 3
_API = "https://api.telegram.org"

AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "ماي", "يونيو", "يوليوز", "غشت",
             "شتنبر", "أكتوبر", "نونبر", "دجنبر"]
AR_DAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
             "septembre", "octobre", "novembre", "décembre"]
FR_DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

LABELS = {
    "ar": {
        "new": "🟢 <b>مباراة جديدة</b>",
        "deadline": "⏳ آخر أجل:",
        "exam": "📝 الكتابي:",
        "exam_tbd": "سيعلن عنه لاحقا",
        "details": "📄 التفاصيل",
        "share": "📤 شارك",
        "update": "🔄 <b>تحديث</b>",
        "exam_date": "📅 تاريخ الاختبار:",
        "list": "📄 تحميل اللائحة",
        "result": "📄 النتائج",
    },
    "fr": {
        "new": "🟢 <b>Nouveau concours</b>",
        "deadline": "⏳ Date limite :",
        "exam": "📝 Écrit :",
        "exam_tbd": "date à annoncer",
        "details": "📄 Détails",
        "share": "📤 Partager",
        "update": "🔄 <b>Mise à jour</b>",
        "exam_date": "📅 Date de l'épreuve :",
        "list": "📄 Télécharger la liste",
        "result": "📄 Résultats",
    },
}

STAGE_TITLES = {
    CompetitionStage.CONVOQUES: ("📋 <b>لوائح المدعوين لاجتياز الاختبار الكتابي</b>",
                                 "📋 <b>Convoqués à l'examen écrit</b>"),
    CompetitionStage.CONVOQUES_ORAL: ("🎤 <b>لوائح المدعوين لاجتياز الاختبار الشفوي</b>",
                                      "🎤 <b>Convoqués à l'entretien oral</b>"),
    CompetitionStage.RESULTATS: ("🏆 <b>النتائج النهائية</b>",
                                 "🏆 <b>Résultats définitifs</b>"),
}
RESULT_WISH = ("🎉 تهانينا للناجحين، وبالتوفيق للجميع", "🎉 Félicitations aux admis")


class TelegramError(RuntimeError):
    """A Bot API failure, described without the request URL (it holds the token)."""

    def __init__(self, method: str, status: int, description: str = ""):
        super().__init__(f"Telegram {method} failed: HTTP {status} {description}".strip())
        self.method = method
        self.status = status


# ---- text helpers --------------------------------------------------------------------

def _clean(text: str | None) -> str:
    """Escape for Telegram HTML. No em dash ever reaches a post (sources use them)."""
    # Sources use em and en dashes as connectors; cards use a plain hyphen.
    value = (text or "").replace("\u2014", "-").replace(" \u2013 ", " - ").replace("،", "، ")
    value = " ".join(value.split()).rstrip(" .")
    return html.escape(value, quote=False)


def lang_of(ann: RawAnnouncement) -> str:
    text = ann.administration or ann.grade or ann.title or ""
    return "ar" if any("\u0600" <= ch <= "\u06ff" for ch in text) else "fr"


def fmt_date(value: date | None, lang: str) -> str:
    """'الأربعاء 26 نونبر 2026' or 'mercredi 26 novembre 2026'."""
    if not value:
        return ""
    if lang == "ar":
        return f"{AR_DAYS[value.weekday()]} {value.day} {AR_MONTHS[value.month - 1]} {value.year}"
    return f"{FR_DAYS[value.weekday()]} {value.day} {FR_MONTHS[value.month - 1]} {value.year}"


def fmt_posts(n: int | None, lang: str) -> str:
    """Arabic number agreement: منصب واحد, منصبان, 3 مناصب, 11 منصبا."""
    if not n:
        return ""
    if lang == "fr":
        return f"{n} poste" + ("s" if n > 1 else "")
    if n == 1:
        return "منصب واحد"
    if n == 2:
        return "منصبان"
    rest = n % 100
    if 3 <= rest <= 10:
        return f"{n} مناصب"
    if 11 <= rest <= 99:
        return f"{n} منصبا"
    return f"{n} منصب"  # 100, 200, 101, 102...


def _specialties(ann: RawAnnouncement, limit: int) -> str:
    specs = [s.strip() for s in (ann.specialty or "").split(" / ") if s.strip()]
    if ann.grade:
        specs = [s for s in specs if s != ann.grade.strip()]
    if not specs:
        return ""
    if len(specs) > limit:
        specs = sorted(specs, key=lambda s: not mentions_it(s))  # keep IT ones visible
        shown = specs[:limit]
        more = len(specs) - limit
        tail = f" (+{more})" if shown else f"{more}"
        return " · ".join(_clean(s) for s in shown) + tail
    return " · ".join(_clean(s) for s in specs)


def channel_footer(channel_id: str | None, dry_run: bool = False) -> str | None:
    """Kept for update posts printed in dry runs; cards themselves have no footer."""
    channel = (channel_id or "").strip() or (PLACEHOLDER_CHANNEL if dry_run else "")
    return f"📢 @{channel.lstrip('@')}" if channel else None


def best_link(ann: RawAnnouncement) -> str:
    """Official link first, then the source page."""
    return ann.official_url or ann.detail_url or ann.source_url


# ---- cards ---------------------------------------------------------------------------

def format_channel_post(
    ann: RawAnnouncement, channel_id: str | None = None, max_specialties: int = MAX_SPECIALTIES
) -> str:
    """New concours card."""
    lang = lang_of(ann)
    t = LABELS[lang]
    lines = [t["new"], ""]
    if ann.administration:
        lines.append(f"🏛 <b>{_clean(ann.administration)}</b>")
    if ann.grade:
        lines.append(f"💼 {_clean(ann.grade)}")
    specs = _specialties(ann, max_specialties)
    if specs:
        lines.append(f"🎓 {specs}")
    if ann.post_count:
        lines.append(f"👥 {fmt_posts(ann.post_count, lang)}")
    dates = []
    if ann.deadline:
        dates.append(f"{t['deadline']} <b>{fmt_date(ann.deadline, lang)}</b>")
    dates.append(f"{t['exam']} {fmt_date(ann.exam_date, lang) or t['exam_tbd']}")
    lines += ["", *dates, "", hashtags(ann)]
    return "\n".join(lines)


def format_stage_post(ann: RawAnnouncement, max_specialties: int = MAX_SPECIALTIES) -> str:
    """Convocation (written or oral) or results card."""
    lang = lang_of(ann)
    i = 0 if lang == "ar" else 1
    lines = [STAGE_TITLES[ann.stage][i], ""]
    if ann.administration:
        lines.append(f"🏛 <b>{_clean(ann.administration)}</b>")
    if ann.grade:
        lines.append(f"💼 {_clean(ann.grade)}")
    specs = _specialties(ann, max_specialties)
    if specs:
        lines.append(f"🎓 {specs}")
    if ann.post_count:
        lines.append(f"👥 {fmt_posts(ann.post_count, lang)}")
    if ann.stage == CompetitionStage.RESULTATS:
        lines += ["", RESULT_WISH[i]]
    elif ann.exam_date and ann.exam_date >= date.today():  # a past date is the wrong stage
        lines += ["", f"{LABELS[lang]['exam_date']} <b>{fmt_date(ann.exam_date, lang)}</b>"]
    lines += ["", hashtags(ann)]
    return "\n".join(lines)


def format_for_send(ann: RawAnnouncement, channel_id: str | None = None) -> str:
    """Card text, with the specialty list trimmed so the photo caption fits 1024 characters."""
    build = format_channel_post if ann.stage == CompetitionStage.AVIS else (
        lambda a, _c=None, max_specialties=MAX_SPECIALTIES: format_stage_post(a, max_specialties)
    )
    text = build(ann, channel_id)
    for keep in (3, 1, 0):
        if len(text) <= CAPTION_LIMIT:
            break
        text = build(ann, channel_id, max_specialties=keep)
    # Still too long (huge administration or grade text): shorten those fields, never
    # the HTML itself. Cutting the HTML can split a tag and Telegram refuses the post.
    limit = 300
    while len(text) > CAPTION_LIMIT and limit >= 40:
        short = ann.model_copy(update={
            "administration": _shorten(ann.administration, limit),
            "grade": _shorten(ann.grade, limit),
        })
        text = build(short, channel_id, max_specialties=0)
        limit //= 2
    return text


def _shorten(value: str | None, limit: int) -> str | None:
    if not value or len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def format_update_post(ann: RawAnnouncement, changes: dict[str, date], footer: str | None) -> str:
    lang = lang_of(ann)
    t = LABELS[lang]
    lines = [t["update"]]
    if ann.administration:
        lines.append(f"🏛 {_clean(ann.administration)}")
    if "deadline" in changes:
        lines.append(f"{t['deadline']} <b>{fmt_date(changes['deadline'], lang)}</b>")
    if "exam_date" in changes:
        lines.append(f"{t['exam']} <b>{fmt_date(changes['exam_date'], lang)}</b>")
    return "\n".join(lines)


def keyboard(ann: RawAnnouncement, share_url: str | None = None) -> dict:
    t = LABELS[lang_of(ann)]
    if ann.stage == CompetitionStage.AVIS:
        main = {"text": t["details"], "url": best_link(ann)}
    else:
        label = t["result"] if ann.stage == CompetitionStage.RESULTATS else t["list"]
        main = {"text": label, "url": ann.list_pdf_url or best_link(ann)}
    row = [main]
    if share_url:
        row.append({"text": t["share"], "url": share_url})
    return {"inline_keyboard": [row]}


# ---- Telegram I/O --------------------------------------------------------------------

def _request(method: str, data: dict, files: dict | None = None) -> dict:
    """One Bot API call with 429 retries. Raises TelegramError (no URL in the message)."""
    settings = get_settings()
    url = f"{_API}/bot{settings.telegram_bot_token}/{method}"
    for attempt in range(_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=settings.request_timeout_seconds) as client:
                if files:
                    resp = client.post(url, data=data, files=files)
                else:
                    resp = client.post(url, json=data)
        except httpx.HTTPError as exc:
            raise TelegramError(method, 0, type(exc).__name__) from None
        body = {}
        try:
            body = resp.json()
        except ValueError:
            pass
        if resp.status_code == 429 and attempt < _MAX_RETRIES:
            wait = int(body.get("parameters", {}).get("retry_after", 5) or 5)
            log.warning("Telegram 429, waiting %ss", wait)
            time.sleep(wait + 1)
            continue
        if resp.status_code != 200 or not body.get("ok"):
            raise TelegramError(method, resp.status_code, str(body.get("description", ""))[:120])
        return body
    raise TelegramError(method, 429, "too many retries")


def fetch_image(url: str | None) -> tuple[str, bytes, str] | None:
    """Download a logo. None when missing, not a raster image, or too big."""
    if not url:
        return None
    try:
        with make_client() as client:
            resp = client.get(url)
    except httpx.HTTPError:
        return None
    ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    if resp.status_code != 200 or not ctype.startswith("image/") or "svg" in ctype:
        return None
    if not resp.content or len(resp.content) > MAX_IMAGE_BYTES:
        return None
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(ctype, "png")
    return (f"logo.{ext}", resp.content, ctype)


def _emblem() -> tuple[str, bytes, str]:
    return ("morocco.png", EMBLEM_PATH.read_bytes(), "image/png")


def _share_url(channel_id: str, message_id: int) -> str | None:
    if not channel_id.startswith("@"):
        return None
    post = f"https://t.me/{channel_id.lstrip('@')}/{message_id}"
    return f"https://t.me/share/url?url={post}"


def send_post(
    ann: RawAnnouncement,
    text: str,
    channel_id: str,
    reply_to: int | None = None,
    with_button: bool = True,
) -> int:
    """Send one card (photo + caption) and return its Telegram message id.

    The share button needs the post's own link, so it is added right after sending.
    Update notes (``with_button=False``) are plain text replies.
    """
    import json

    base: dict = {"chat_id": channel_id, "parse_mode": "HTML"}
    if reply_to:
        base["reply_parameters"] = json.dumps(
            {"message_id": reply_to, "allow_sending_without_reply": True}
        )
    if not with_button:
        payload = {**base, "text": text, "link_preview_options": {"is_disabled": True}}
        if reply_to:
            payload["reply_parameters"] = json.loads(base["reply_parameters"])
        return _request("sendMessage", payload)["result"]["message_id"]

    data = {**base, "caption": text, "reply_markup": json.dumps(keyboard(ann))}
    message_id = None
    for image in (fetch_image(ann.logo_url), _emblem()):
        if image is None:
            continue
        try:
            res = _request("sendPhoto", data, files={"photo": image})
            message_id = res["result"]["message_id"]
            break
        except TelegramError as exc:
            if exc.status != 400:
                raise
            log.warning("logo rejected by Telegram, using the emblem")
    if message_id is None:
        raise TelegramError("sendPhoto", 400, "no image accepted")

    share = _share_url(channel_id, message_id)
    if share:
        try:
            _request("editMessageReplyMarkup", {
                "chat_id": channel_id, "message_id": message_id,
                "reply_markup": keyboard(ann, share),
            })
        except TelegramError as exc:
            log.warning("share button not added: %s", exc)
    return message_id
