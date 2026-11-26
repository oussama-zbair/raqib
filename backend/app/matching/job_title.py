"""Job title and salary scale from a grade line, for the website filters.

"تقني من الدرجة الثالثة - سُلمْ 9"          -> ("تقني", 9)
"مهندس دولة من الدرجة الأولى - سُلمْ 11"    -> ("مهندس دولة", 11)
"متصرف من الدرجة الثانية لفائدة كلية ..."  -> ("متصرف", None)
"Technicien de 3ème grade - Echelle 9"     -> ("Technicien", 9)

Generic rules (where the grade, the scale or the posting place starts), no job list.
"""
from __future__ import annotations

import re

_DIACRITICS = re.compile(r"[\u064b-\u065f\u0670\u0640]")
_SCALE = re.compile(r"(?:سلم|echelle|échelle)\s*(\d{1,2})", re.IGNORECASE)
# Where the job title ends: the grade, the scale, a dash, a bracket, the posting place.
_CUT = re.compile(
    r"\s+(?:من\s+)?الدرجة|\s+الصنف|\s*[-–—(:/]|\s+سلم\b|\s+لفائدة|\s+لدى|\s+في\s+إطار"
    r"|\s+ب(?:ال|كلية|رئاسة|مديرية|جامعة|معهد|مدرسة|عمالة|إقليم|جماعة)"
    r"|\s+de\s+\d|\s+\d|\s+(?:1er|premier|deuxième|troisième|principal)\b|\s+grade\b"
    r"|\s+(?:au|à la|à l'|pour|auprès)\b",
    re.IGNORECASE,
)
_PREFIX = re.compile(r"^(?:مباراة\s+)?(?:ل?توظيف|التوظيف)\s+(?:\d+\s+)?", re.IGNORECASE)
MAX_WORDS = 4
_DANGLING = {"في", "و", "من", "على", "عن", "مع", "إلى", "de", "du", "des", "en", "et", "d'"}


def scale_of(grade: str | None) -> int | None:
    m = _SCALE.search(_DIACRITICS.sub("", grade or ""))
    if not m:
        return None
    n = int(m.group(1))
    return n if 5 <= n <= 13 else None


_COUNT_WORD = re.compile(r"^(?:\d+\s+)?(?:منصبان|منصبا|مناصب|منصب)\s*\(?", re.IGNORECASE)


def job_family(title: str | None) -> str | None:
    """The filter value: the title's first word, without article or plural.

    "مهندس دولة", "مهندس معماري" -> "مهندس"; "مكلفين" -> "مكلف"; "Techniciens" -> "Technicien".
    """
    if not title:
        return None
    word = title.split()[0]
    if word.startswith("ال") and len(word) > 4:
        word = word[2:]
    for suffix in ("ين", "ون"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            break
    if word.isascii() and word.lower().endswith("s") and len(word) > 4:
        word = word[:-1]
    return word[0].upper() + word[1:] if word[0].isascii() else word


def job_title(grade: str | None) -> str | None:
    text = " ".join(_DIACRITICS.sub("", grade or "").split())
    text = _PREFIX.sub("", text)
    text = _COUNT_WORD.sub("", text).rstrip(")")  # "منصبان (مهندس رئيس مشروع)"
    if not text:
        return None
    m = _CUT.search(text)
    title = (text[: m.start()] if m and m.start() > 0 else text).strip(" .،,")
    words = title.split()
    if not words:
        return None
    words = words[:MAX_WORDS]
    while len(words) > 1 and words[-1].lower() in _DANGLING:
        words.pop()  # never end on "في", "و", "de"...
    title = " ".join(words)
    # Capitalised French titles compare equal ("technicien" / "Technicien").
    return title[0].upper() + title[1:] if title[0].isascii() else title
