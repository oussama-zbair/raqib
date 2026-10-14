"""Match a competition to a candidate profile (FR/AR), with negative filtering."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.db.models import Competition, Profile
from app.matching.normalizer import (
    normalize_grade,
    normalize_specialty,
    normalize_text,
)
from app.matching.taxonomy import NEGATIVE_TERMS


@dataclass
class MatchResult:
    matched: bool
    reasons: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # allow `if match:`
        return self.matched


def _has_negative_term(text_norm: str) -> str | None:
    for term in NEGATIVE_TERMS:
        if normalize_text(term) in text_norm:
            return term
    return None


def matches_profile(competition: Competition, profile: Profile) -> MatchResult:
    """Decide whether a competition is relevant to a candidate.

    Rules:
    - The competition's grade must be one of the profile's target grades.
    - The competition's specialty must be one of the profile's target specialties.
    - Off-target/sub-bac+5 postings are rejected UNLESS the profile opts in via
      ``include_off_target``.
    - Grade/specialty can come from already-normalized competition fields, or be
      inferred from the competition text (title + raw) as a fallback.
    """
    reasons: list[str] = []

    haystack = normalize_text(
        " ".join(
            filter(
                None,
                [
                    competition.title_fr,
                    competition.title_ar,
                    competition.administration,
                    competition.grade,
                    competition.specialty,
                    competition.required_degree,
                ],
            )
        )
    )

    # Negative filtering (default on).
    if not profile.include_off_target:
        neg = _has_negative_term(haystack)
        if neg:
            return MatchResult(False, [f"rejected: negative term '{neg}'"])

    # Resolve competition grade & specialty (prefer explicit fields, else infer).
    comp_grade = normalize_grade(competition.grade) or normalize_grade(haystack)
    comp_specialty = normalize_specialty(competition.specialty) or normalize_specialty(
        haystack
    )

    # Grade check.
    if profile.target_grades:
        if comp_grade and comp_grade in profile.target_grades:
            reasons.append(f"grade match: {comp_grade}")
        else:
            return MatchResult(
                False, [f"grade mismatch (comp={comp_grade}, want={profile.target_grades})"]
            )

    # Specialty check.
    if profile.target_specialties:
        if comp_specialty and comp_specialty in profile.target_specialties:
            reasons.append(f"specialty match: {comp_specialty}")
        else:
            return MatchResult(
                False,
                [
                    f"specialty mismatch (comp={comp_specialty}, "
                    f"want={profile.target_specialties})"
                ],
            )

    return MatchResult(True, reasons or ["profile has no grade/specialty constraints"])
