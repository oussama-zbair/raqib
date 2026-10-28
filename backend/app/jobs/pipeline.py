"""Source-agnostic ingestion pipeline helpers.

Turns raw announcements into canonical competition records: normalize -> compute
canonical hash -> merge duplicates (in-batch) -> shape rows for upsert. Kept separate
from I/O so it is unit-testable.
"""

from __future__ import annotations

from app.db.models import (
    Competition,
    CompetitionFields,
    CompetitionStage,
    RawAnnouncement,
)
from app.matching.normalizer import (
    canonical_hash,
    classify_family,
    classify_level,
)


def raw_to_competition(
    raw: RawAnnouncement, fields: CompetitionFields | None = None
) -> Competition:
    """Build a canonical Competition from a raw announcement + optional extracted fields.

    ``fields`` come either from deterministic parsing or the Gemini fallback. When
    absent, we infer grade/specialty directly from the announcement text so a bare
    listing still gets a canonical identity.
    """
    text = f"{raw.title or ''} {raw.text or ''}"
    admin = (fields.administration if fields else None) or (raw.title or "")[:200]
    # grade column holds the LEVEL key, specialty column holds the FAMILY key.
    grade = (fields.grade if fields else None) or classify_level(text)
    specialty = (fields.specialty if fields else None) or classify_family(text)
    deadline = fields.deadline if fields else None

    ch = canonical_hash(admin, grade, deadline)

    comp = Competition(
        canonical_hash=ch,
        administration=admin or "Inconnu",
        grade=grade,
        specialty=specialty,
        required_degree=fields.required_degree if fields else None,
        deadline=deadline,
        post_count=fields.post_count if fields else None,
        submission_link=(fields.submission_link if fields else None) or raw.detail_url,
        stage=raw.stage,
        early_signal=raw.source_type.value in ("TELEGRAM", "AGGREGATOR"),
        title_fr=raw.title if raw.lang == "fr" else None,
        title_ar=raw.title if raw.lang == "ar" else None,
        source_urls=[raw.source_url],
        raw={"source": raw.source_name, "text": raw.text[:1000], "lang": raw.lang},
    )
    if raw.stage == CompetitionStage.CONVOQUES and raw.pdf_urls:
        comp.convocation_pdf_url = raw.pdf_urls[0]
    if raw.stage == CompetitionStage.RESULTATS and raw.pdf_urls:
        comp.results_pdf_url = raw.pdf_urls[0]
    return comp


def dedup_batch(competitions: list[Competition]) -> list[Competition]:
    """Merge competitions that share a canonical hash within a single batch.

    An official-portal record clears the early_signal flag on a matching community one;
    source URLs and PDF links are unioned.
    """
    merged: dict[str, Competition] = {}
    for comp in competitions:
        existing = merged.get(comp.canonical_hash)
        if existing is None:
            merged[comp.canonical_hash] = comp
            continue
        # union source urls
        for url in comp.source_urls:
            if url not in existing.source_urls:
                existing.source_urls.append(url)
        # prefer the more advanced lifecycle stage
        stage_order = {
            CompetitionStage.AVIS: 0,
            CompetitionStage.CONVOQUES: 1,
            CompetitionStage.RESULTATS: 2,
        }
        if stage_order[comp.stage] > stage_order[existing.stage]:
            existing.stage = comp.stage
        # official portal confirmation clears early signal
        if not comp.early_signal:
            existing.early_signal = False
        # fill gaps
        existing.grade = existing.grade or comp.grade
        existing.specialty = existing.specialty or comp.specialty
        existing.deadline = existing.deadline or comp.deadline
        existing.post_count = existing.post_count or comp.post_count
        existing.submission_link = existing.submission_link or comp.submission_link
        existing.convocation_pdf_url = (
            existing.convocation_pdf_url or comp.convocation_pdf_url
        )
        existing.results_pdf_url = existing.results_pdf_url or comp.results_pdf_url
        existing.title_fr = existing.title_fr or comp.title_fr
        existing.title_ar = existing.title_ar or comp.title_ar
    return list(merged.values())


def competition_to_row(comp: Competition) -> dict:
    """Shape a Competition for the Supabase competitions upsert."""
    return {
        "canonical_hash": comp.canonical_hash,
        "administration": comp.administration,
        "grade": comp.grade,
        "specialty": comp.specialty,
        "required_degree": comp.required_degree,
        "deadline": comp.deadline.isoformat() if comp.deadline else None,
        "post_count": comp.post_count,
        "submission_link": comp.submission_link,
        "reference_code": comp.reference_code,
        "stage": comp.stage.value,
        "early_signal": comp.early_signal,
        "title_fr": comp.title_fr,
        "title_ar": comp.title_ar,
        "source_urls": comp.source_urls,
        "convocation_pdf_url": comp.convocation_pdf_url,
        "results_pdf_url": comp.results_pdf_url,
        "raw": comp.raw,
    }
