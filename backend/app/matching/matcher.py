"""Match a competition to a candidate profile (FR/AR), across all concours families.

Model:
- A competition is classified into a FAMILY (field) and a LEVEL (diploma/grade).
- A profile stores target families + target levels (stored in the existing
  ``target_specialties`` and ``target_grades`` columns respectively, to avoid a DB
  migration; semantically they are families and levels now).
- A competition matches if its family is among the profile's families AND its level is
  among the profile's levels (each axis only enforced when the profile constrains it).
- Low-level support roles (agent de service, adjoint, ...) are rejected unless the
  profile opts in via ``include_off_target``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.db.models import Competition, Profile
from app.matching.normalizer import (
    classify_family,
    classify_level,
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


def _profile_families(profile: Profile) -> list[str]:
    # families live in target_specialties (kept for DB compatibility)
    return profile.target_specialties or []


def _profile_levels(profile: Profile) -> list[str]:
    # levels live in target_grades (kept for DB compatibility)
    return profile.target_grades or []


def matches_profile(competition: Competition, profile: Profile) -> MatchResult:
    """Decide whether a competition is relevant to a candidate."""
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

    # Negative filtering (default on): low-level support roles.
    if not profile.include_off_target:
        neg = _has_negative_term(haystack)
        if neg:
            return MatchResult(False, [f"rejected: negative term '{neg}'"])

    # Classify the competition (prefer explicit fields, else infer from text).
    comp_family = classify_family(competition.specialty) or classify_family(haystack)
    comp_level = classify_level(competition.grade) or classify_level(haystack)

    want_families = _profile_families(profile)
    want_levels = _profile_levels(profile)

    # Family axis.
    if want_families:
        if comp_family and comp_family in want_families:
            reasons.append(f"family match: {comp_family}")
        else:
            return MatchResult(
                False, [f"family mismatch (comp={comp_family}, want={want_families})"]
            )

    # Level axis.
    if want_levels:
        if comp_level and comp_level in want_levels:
            reasons.append(f"level match: {comp_level}")
        else:
            return MatchResult(
                False, [f"level mismatch (comp={comp_level}, want={want_levels})"]
            )

    return MatchResult(True, reasons or ["profile has no family/level constraints"])
