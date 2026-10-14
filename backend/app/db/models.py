"""Pydantic models mirroring the Supabase tables.

These are lightweight domain objects used across scraping, matching, and monitoring.
They intentionally avoid ORM coupling — the DB layer talks to Supabase over REST.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PORTAL = "PORTAL"
    MINISTRY = "MINISTRY"
    TELEGRAM = "TELEGRAM"
    AGGREGATOR = "AGGREGATOR"


class CompetitionStage(str, Enum):
    AVIS = "AVIS"
    CONVOQUES = "CONVOQUES"
    RESULTATS = "RESULTATS"


class TrackingState(str, Enum):
    APPLIED = "APPLIED"
    EN_ATTENTE_CONVOCATION = "EN_ATTENTE_CONVOCATION"
    CONVOQUE = "CONVOQUE"
    RESULTAT = "RESULTAT"


class OnboardingState(str, Enum):
    NEW = "NEW"
    AWAIT_NAME_FR = "AWAIT_NAME_FR"
    AWAIT_NAME_AR = "AWAIT_NAME_AR"
    AWAIT_CIN = "AWAIT_CIN"
    AWAIT_GRADE = "AWAIT_GRADE"
    AWAIT_SPECIALTY = "AWAIT_SPECIALTY"
    COMPLETE = "COMPLETE"


class Profile(BaseModel):
    id: int | None = None
    user_id: int
    full_name_fr: str | None = None
    full_name_ar: str | None = None
    cin_encrypted: str | None = None
    cin_last4: str | None = None
    target_grades: list[str] = Field(default_factory=list)
    target_specialties: list[str] = Field(default_factory=list)
    include_off_target: bool = False
    onboarding_state: OnboardingState = OnboardingState.NEW


class RawAnnouncement(BaseModel):
    """Unnormalized announcement as produced by a scraper, before extraction/dedup."""

    source_name: str
    source_type: SourceType
    source_url: str
    title: str | None = None
    text: str = ""
    lang: str = "fr"  # 'fr' | 'ar'
    stage: CompetitionStage = CompetitionStage.AVIS
    pdf_urls: list[str] = Field(default_factory=list)
    detail_url: str | None = None


class CompetitionFields(BaseModel):
    """Structured competition fields, whether parsed directly or via Gemini fallback."""

    administration: str | None = None
    grade: str | None = None
    specialty: str | None = None
    required_degree: str | None = None
    deadline: date | None = None
    post_count: int | None = None
    submission_link: str | None = None


class Competition(BaseModel):
    id: int | None = None
    canonical_hash: str
    administration: str
    grade: str | None = None
    specialty: str | None = None
    required_degree: str | None = None
    deadline: date | None = None
    post_count: int | None = None
    submission_link: str | None = None
    reference_code: str | None = None
    stage: CompetitionStage = CompetitionStage.AVIS
    early_signal: bool = False
    title_fr: str | None = None
    title_ar: str | None = None
    source_ids: list[int] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    convocation_pdf_url: str | None = None
    results_pdf_url: str | None = None
    raw: dict | None = None
    first_seen_at: datetime | None = None


class TrackedCompetition(BaseModel):
    id: int | None = None
    user_id: int
    competition_id: int
    state: TrackingState = TrackingState.APPLIED
    last_checked_at: datetime | None = None
    last_pdf_url: str | None = None
    rollcall_result: dict | None = None
    notified_convocation: bool = False
    notified_result: bool = False


class RollCallHit(BaseModel):
    """A candidate found on a convocation/results PDF."""

    found: bool = True
    cin: str
    full_name: str | None = None
    centre: str | None = None
    salle: str | None = None
    table: str | None = None
    exam_date: str | None = None
    pdf_url: str | None = None


class RollCallMiss(BaseModel):
    found: bool = False
    cin: str
    pdf_url: str | None = None
