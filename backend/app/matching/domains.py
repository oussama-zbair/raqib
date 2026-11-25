"""Channel hashtags: field of the post, stage, and city.

Tags are always Arabic, whatever the language of the post, so one search
("#معلوميات") finds every matching post in the channel.
"""
from __future__ import annotations

import re

from app.db.models import CompetitionStage, RawAnnouncement
from app.matching.it_filter import is_it_related
from app.matching.normalizer import normalize_text

MAX_FIELD_TAGS = 2

# Order matters: the first matches are kept. Keywords are compared after normalize_text.
_FIELDS: list[tuple[str, tuple[str, ...]]] = [
    ("صحة", ("ممرض", "طبيب", "صحة", "صيدل", "قابلة", "infirmier", "medecin", "sante",
             "pharmac", "sage femme", "paramedic")),
    ("تعليم", ("استاذ", "تعليم", "مكون", "professeur", "enseignant", "education",
               "formateur", "maitre de conferences")),
    ("أمن", ("شرطة", "امن", "سجون", "حارس", "الدرك", "القوات المساعدة", "الوقاية المدنية",
             "surveillant", "penitentiaire", "police", "gendarmerie", "pompier",
             "forces auxiliaires", "protection civile")),
    ("قضاء", ("قضائي", "قضاء", "الضبط", "judiciaire", "justice", "greffier")),
    ("مالية", ("مالية", "محاسب", "اقتصاد", "finance", "comptab", "econom", "fiscal")),
    ("فلاحة", ("فلاح", "زراع", "agricol", "agronom", "veterinaire", "بيطري")),
    ("هندسة", ("مهندس", "ingenieur")),
    ("تقني", ("تقني", "technicien")),
    ("إدارة", ("متصرف", "محرر", "ملحق", "اداري", "administrateur", "redacteur",
               "adjoint administratif", "secretaire", "attache")),
]
_IT_TAG = "معلوميات"

STAGE_TAGS = {
    CompetitionStage.AVIS: "مباراة",
    CompetitionStage.CONVOQUES: "استدعاء_الكتابي",
    CompetitionStage.CONVOQUES_ORAL: "استدعاء_الشفوي",
    CompetitionStage.RESULTATS: "نتائج",
}

_NOT_A_CITY = {"المغرب", "maroc", "morocco", "national", "وطني"}
_TAG_CHARS = re.compile(r"[^\w]+", re.UNICODE)


def _norm_keywords() -> list[tuple[str, tuple[str, ...]]]:
    return [(tag, tuple(normalize_text(k) for k in kws)) for tag, kws in _FIELDS]


_FIELDS_NORM = _norm_keywords()


def field_tags(ann: RawAnnouncement) -> list[str]:
    """Up to two field tags. IT first when the post is IT related."""
    tags: list[str] = []
    if is_it_related(ann)[0]:
        tags.append(_IT_TAG)
    # Grade and specialty describe the job; the administration only as a last resort.
    job = normalize_text(" ".join(filter(None, (ann.grade, ann.specialty, ann.title))))
    words = [_strip_prefix(w) for w in job.split()]
    padded = f" {' '.join(words)} "
    for tag, kws in _FIELDS_NORM:
        if len(tags) >= MAX_FIELD_TAGS:
            break
        if tag not in tags and any(_has(words, padded, k) for k in kws):
            tags.append(tag)
    return tags


def _strip_prefix(word: str) -> str:
    """Drop the Arabic article and the 'and' prefix so 'والامن' compares as 'امن'."""
    for p in ("وال", "بال", "لل", "ال"):
        if word.startswith(p) and len(word) > len(p) + 2:
            return word[len(p):]
    return word


def _has(words: list[str], padded: str, kw: str) -> bool:
    """Whole words only: a keyword matches the start of a word, never its middle."""
    if not kw:
        return False
    if " " in kw:
        kw_words = " ".join(_strip_prefix(w) for w in kw.split())
        return f" {kw_words}" in padded
    return any(w.startswith(_strip_prefix(kw)) for w in words)


def city_tag(city: str | None) -> str | None:
    if not city:
        return None
    c = city.strip()
    if normalize_text(c) in {normalize_text(x) for x in _NOT_A_CITY}:
        return None
    tag = _TAG_CHARS.sub("_", c).strip("_")
    return tag or None


def hashtags(ann: RawAnnouncement) -> str:
    """'#معلوميات #تقني #مباراة #تاونات' (field tags, stage tag, city)."""
    tags = field_tags(ann)
    tags.append(STAGE_TAGS.get(ann.stage, "مباراة"))
    city = city_tag(ann.city)
    if city:
        tags.append(city)
    return " ".join(f"#{t}" for t in tags)
