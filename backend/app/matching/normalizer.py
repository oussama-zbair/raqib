"""Text normalization + canonical competition identity.

Normalization makes FR/AR matching robust to accents, case, punctuation, and Arabic
diacritics. The canonical hash is the deduplication key across all sources.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date

from dateutil import parser as date_parser

from app.matching.taxonomy import (
    FAMILY_SYNONYMS,
    LEVEL_SYNONYMS,
)

# Arabic diacritics (harakat) + tatweel to strip.
_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u0640]")


def normalize_text(text: str | None) -> str:
    """Lowercase, strip accents/diacritics, collapse whitespace & punctuation.

    Works for both Latin (FR) and Arabic. Arabic letters are preserved (they carry no
    case) while harakat and tatweel are removed so spellings compare equal.
    """
    if not text:
        return ""
    text = text.lower()
    # Decompose and drop Latin combining accents.
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # Remove Arabic diacritics/tatweel.
    text = _ARABIC_DIACRITICS.sub("", text)
    # Normalize a few Arabic letter variants.
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    # Collapse punctuation to spaces, then squeeze whitespace.
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _match_canonical(text_norm: str, table: dict[str, list[str]]) -> str | None:
    """Return the canonical key whose synonym appears in the normalized text.

    Longer synonyms are tried first so a specific term ("genie logiciel") wins over a
    broad one ("genie") when both could match.
    """
    best_key: str | None = None
    best_len = -1
    for key, synonyms in table.items():
        for syn in synonyms:
            syn_n = normalize_text(syn)
            if syn_n and syn_n in text_norm and len(syn_n) > best_len:
                best_key, best_len = key, len(syn_n)
    return best_key


def classify_family(text: str | None) -> str | None:
    """Classify text into a concours FAMILY (field/domain)."""
    return _match_canonical(normalize_text(text), FAMILY_SYNONYMS)


def classify_level(text: str | None) -> str | None:
    """Classify text into a concours LEVEL (diploma/grade)."""
    return _match_canonical(normalize_text(text), LEVEL_SYNONYMS)


# Backward-compatible aliases (old names used across the codebase/tests).
def normalize_grade(text: str | None) -> str | None:
    return classify_level(text)


def normalize_specialty(text: str | None) -> str | None:
    return classify_family(text)


def normalize_admin(text: str | None) -> str:
    """Canonical administration string used in the dedup hash."""
    return normalize_text(text)


def normalize_deadline(value: str | date | None) -> date | None:
    """Parse a deadline from a string or pass through a date. Day-first (FR/AR)."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date_parser.parse(str(value), dayfirst=True, fuzzy=True).date()
    except (ValueError, OverflowError):
        return None


def canonical_hash(
    administration: str | None,
    grade: str | None,
    deadline: str | date | None,
) -> str:
    """Stable dedup identity: hash(normalized_admin + grade + deadline).

    Two announcements from different sources for the same competition collapse to the
    same hash regardless of language or formatting.
    """
    admin_n = normalize_admin(administration)
    grade_n = normalize_grade(grade) or normalize_text(grade)
    deadline_d = normalize_deadline(deadline)
    deadline_s = deadline_d.isoformat() if deadline_d else ""
    basis = f"{admin_n}|{grade_n}|{deadline_s}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()
