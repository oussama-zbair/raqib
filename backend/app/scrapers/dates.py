"""Date and number parsing shared by the scrapers (French and Moroccan Arabic month names)."""
from __future__ import annotations

import re
import unicodedata
from datetime import date

_MONTHS: dict[str, int] = {
    # French (accents stripped by _fold)
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
    # Arabic, Moroccan press spelling plus the common alternatives
    "يناير": 1, "فبراير": 2, "مارس": 3, "ابريل": 4, "أبريل": 4, "ماي": 5, "مايو": 5,
    "يونيو": 6, "يوليوز": 7, "يوليو": 7, "غشت": 8, "اغسطس": 8, "أغسطس": 8,
    "شتنبر": 9, "سبتمبر": 9, "اكتوبر": 10, "أكتوبر": 10, "نونبر": 11, "نوفمبر": 11,
    "دجنبر": 12, "ديسمبر": 12,
}
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_DATE_RE = re.compile(r"(\d{1,2})\s+([^\W\d_]+)\s+(\d{4})")


def _fold(s: str) -> str:
    """Lowercase and strip Latin accents; Arabic letters are left untouched."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def parse_date(text: str | None) -> date | None:
    """Parse the first 'D <month name> YYYY' found in ``text``; None when absent or unknown."""
    if not text:
        return None
    for day, month, year in _DATE_RE.findall(text.translate(_ARABIC_DIGITS)):
        m = _MONTHS.get(_fold(month))
        if m is None:
            continue
        try:
            return date(int(year), m, int(day))
        except ValueError:
            continue
    return None


def parse_int(text: str | None) -> int | None:
    """First integer in ``text`` (Arabic-Indic digits accepted), else None."""
    if not text:
        return None
    m = re.search(r"\d+", text.translate(_ARABIC_DIGITS))
    return int(m.group()) if m else None
