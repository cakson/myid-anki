"""Deterministic comparison keys and conservative overlap screening."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from typing import Any


def comparison_key(value: str) -> str:
    """Normalize an English comparison key, never learner display text."""
    cleaned = unicodedata.normalize("NFKC", value).casefold()
    words = re.findall(r"\w+", cleaned, flags=re.UNICODE)
    normalized = []
    for word in words:
        if len(word) > 4 and word.endswith("ies"):
            word = word[:-3] + "y"
        elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        normalized.append(word)
    return " ".join(normalized)


def find_deterministic_overlaps(
    candidate: Mapping[str, Any], others: Iterable[Mapping[str, Any]]
) -> list[dict[str, str]]:
    """Surface certain form matches for semantic resolution before assigning IDs."""
    result = []
    english = comparison_key(str(candidate.get("english", "")))
    answers = (
        str(candidate.get("indonesian", "")).casefold(),
        str(candidate.get("malaysian", "")).casefold(),
    )
    for other in others:
        other_id = str(other.get("candidate_id") or other.get("id") or "")
        if not other_id or other_id == candidate.get("candidate_id"):
            continue
        cue_match = english and english == comparison_key(str(other.get("english", "")))
        answer_match = answers == (
            str(other.get("indonesian", "")).casefold(),
            str(other.get("malaysian", "")).casefold(),
        )
        if cue_match or answer_match:
            result.append(
                {
                    "other_id": other_id,
                    "type": "exact" if cue_match else "morphology",
                    "resolution": "unresolved",
                    "rationale": "Deterministic cue or answer match requires semantic review",
                }
            )
    return result


def overlap_allows_new_id(
    overlaps: Iterable[Mapping[str, Any]], *, legacy_id: str | None = None
) -> bool:
    """Allow only distinct senses or an explicitly reviewed retained legacy ID."""
    return all(
        (
            overlap.get("resolution") == "distinct"
            or (
                legacy_id is not None
                and overlap.get("other_id") == legacy_id
                and overlap.get("resolution") == "retrospective"
            )
        )
        and bool(str(overlap.get("rationale", "")).strip())
        for overlap in overlaps
    )


def has_self_overlap(
    overlaps: Iterable[Mapping[str, Any]], batch_id: str, candidate_id: str
) -> bool:
    """Catch a bundled reviewer accidentally comparing a candidate with itself."""
    return any(
        item.get("other_id") in {candidate_id, f"{batch_id}:{candidate_id}"} for item in overlaps
    )
