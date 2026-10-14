"""Gemini Flash fallback extractor.

Most announcements are parsed directly from HTML. This module is the *fallback* for the
hard cases: unstructured text or scanned image/PDF announcements where the structured
fields (administration, grade, specialty, degree, deadline, post count, submission link)
can't be read deterministically.

Used sparingly to conserve the free-tier quota — the ingest job only calls this when
deterministic parsing yields too little.
"""

from __future__ import annotations

import json
import re
from datetime import date

from app.config import get_settings
from app.db.models import CompetitionFields
from app.matching.normalizer import normalize_deadline

_PROMPT = """You extract structured data from Moroccan public-sector competition
(concours de recrutement) announcements. The text may be in French or Arabic.

Return ONLY a JSON object with these keys (use null when unknown):
{
  "administration": string,        // ministry / public agency running the concours
  "grade": string,                 // e.g. "Ingénieur d'État 1er grade", "Échelle 11"
  "specialty": string,             // e.g. "Génie Logiciel", "Informatique"
  "required_degree": string,       // required diploma
  "deadline": string,              // application deadline, DD/MM/YYYY if possible
  "post_count": number,            // number of posts/seats
  "submission_link": string        // dossier submission URL
}

Announcement:
---
%s
---
JSON:"""


def _extract_json(raw: str) -> dict:
    """Pull the first JSON object out of a model response (handles code fences)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    candidate = fenced.group(1) if fenced else raw
    brace = re.search(r"\{.*\}", candidate, re.DOTALL)
    if not brace:
        return {}
    try:
        return json.loads(brace.group(0))
    except json.JSONDecodeError:
        return {}


def _to_fields(data: dict) -> CompetitionFields:
    def _int(v: object) -> int | None:
        try:
            return int(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    deadline_val = data.get("deadline")
    deadline: date | None = normalize_deadline(deadline_val) if deadline_val else None

    return CompetitionFields(
        administration=data.get("administration") or None,
        grade=data.get("grade") or None,
        specialty=data.get("specialty") or None,
        required_degree=data.get("required_degree") or None,
        deadline=deadline,
        post_count=_int(data.get("post_count")),
        submission_link=data.get("submission_link") or None,
    )


def extract_from_text(text: str) -> CompetitionFields:
    """Extract structured fields from raw announcement text via Gemini Flash."""
    import google.generativeai as genai  # imported lazily to keep import light

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    resp = model.generate_content(_PROMPT % text[:8000])
    return _to_fields(_extract_json(resp.text or ""))


def extract_from_image(image_bytes: bytes, mime_type: str = "image/png") -> CompetitionFields:
    """Extract structured fields from a scanned announcement image via Gemini vision."""
    import google.generativeai as genai

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    resp = model.generate_content(
        [
            _PROMPT % "(see attached image)",
            {"mime_type": mime_type, "data": image_bytes},
        ]
    )
    return _to_fields(_extract_json(resp.text or ""))


# Exposed for unit testing the parsing without a network/model call.
parse_model_json = _extract_json
build_fields = _to_fields
