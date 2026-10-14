"""Telegram notifications sent from the backend jobs (digest + urgent alerts).

The interactive bot (onboarding, buttons) lives in the Supabase Edge Function. This
module only *pushes* messages from the cron jobs via the Bot API.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.db.models import Competition, RollCallHit

_API = "https://api.telegram.org"


def _post(method: str, payload: dict[str, Any]) -> dict:
    settings = get_settings()
    url = f"{_API}/bot{settings.telegram_bot_token}/{method}"
    with httpx.Client(timeout=settings.request_timeout_seconds) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def send_message(
    chat_id: int, text: str, reply_markup: dict | None = None, disable_preview: bool = True
) -> dict:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _post("sendMessage", payload)


def _track_button(competition_id: int) -> dict:
    """Inline keyboard with the one-click tracking button."""
    return {
        "inline_keyboard": [
            [{"text": "📌 Suivre ce concours", "callback_data": f"track:{competition_id}"}]
        ]
    }


def format_competition(comp: Competition) -> str:
    title = comp.title_fr or comp.title_ar or comp.administration
    lines = [
        f"<b>{title}</b>",
        f"🏛 Administration: {comp.administration}",
    ]
    if comp.grade:
        lines.append(f"🎯 Grade: {comp.grade}")
    if comp.specialty:
        lines.append(f"🧩 Spécialité: {comp.specialty}")
    if comp.post_count:
        lines.append(f"🔢 Postes: {comp.post_count}")
    if comp.deadline:
        lines.append(f"⏳ Date limite: {comp.deadline.isoformat()}")
    if comp.submission_link:
        lines.append(f'📎 <a href="{comp.submission_link}">Déposer le dossier</a>')
    if comp.early_signal:
        lines.append("⚡ <i>Signal précoce (non encore confirmé sur le portail officiel)</i>")
    return "\n".join(lines)


def send_digest(chat_id: int, competitions: list[Competition]) -> None:
    """Send the daily digest: one message per matched competition with a track button."""
    if not competitions:
        return
    header = f"📬 <b>Votre veille concours</b> — {len(competitions)} nouveau(x) résultat(s)"
    send_message(chat_id, header)
    for comp in competitions:
        send_message(
            chat_id,
            format_competition(comp),
            reply_markup=_track_button(comp.id) if comp.id else None,
        )


def send_urgent_convocation(chat_id: int, comp: Competition, hit: RollCallHit) -> dict:
    """The critical alert: candidate's CIN found on a convocation/results PDF."""
    poste = comp.grade or ""
    if comp.specialty:
        poste = f"{poste} ({comp.specialty})".strip()
    text = "\n".join(
        [
            "🚨 <b>CONVOCATION OFFICIELLE TROUVÉE !</b>",
            "",
            f"Administration: {comp.administration}",
            f"Poste: {poste}" if poste else "",
            "",
            f"Candidat: {hit.full_name or ''} (CIN: {hit.cin})",
            f"Centre d'examen: {hit.centre or '—'}",
            f"Salle / Amphi: {hit.salle or '—'}",
            f"N° de Table: {hit.table or '—'}",
            f"Date de l'épreuve: {hit.exam_date or '—'}",
            "",
            f'📄 <a href="{hit.pdf_url}">Télécharger la liste complète en PDF</a>'
            if hit.pdf_url
            else "",
        ]
    )
    # Drop empty lines produced by optional fields.
    text = "\n".join(line for line in text.split("\n") if line != "" or True)
    return send_message(chat_id, text)


def send_convocation_not_found(chat_id: int, comp: Competition) -> dict:
    title = comp.title_fr or comp.title_ar or comp.administration
    text = (
        f"ℹ️ La liste des convoqués pour <b>{title}</b> a été publiée, "
        "mais votre CIN n'a pas été détecté sur la liste."
    )
    return send_message(chat_id, text)
