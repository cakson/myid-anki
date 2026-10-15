"""Nonblocking preference signals and reproducible audit routing."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any

PREFERENCE_SIGNALS = frozenset(
    {
        "no-preference-concern",
        "named-alternative-exists",
        "credible-everyday-alternative",
        "shared-common-form",
        "preference-strength-uncertain",
        "regional-or-register-competition",
        "same-sense-competition",
        "different-sense-only",
        "verifier-explicitly-questions-preference",
    }
)
STRONG_PREFERENCE_SIGNALS = frozenset(
    {
        "credible-everyday-alternative",
        "shared-common-form",
        "preference-strength-uncertain",
        "regional-or-register-competition",
        "same-sense-competition",
        "verifier-explicitly-questions-preference",
    }
)
STRONG_AUDIT_FLAGS = frozenset(
    {
        "credible-competing-form",
        "shared-common-form",
        "preference-uncertainty",
        "regional-register-risk",
        "cue-sense-ambiguity",
        "relation-instability",
        "verifier-disagreement",
        "historical-objection",
        "concrete-nonblocking-risk",
        "substantial-nonblocking-risk",
        "cue-corrected",
        "relation-corrected",
    }
)


def validate_preference_risk(value: Any) -> dict[str, Any]:
    """Validate a compact claim-level signal; it is not an acceptance veto."""
    if not isinstance(value, Mapping):
        raise ValueError("preference_risk must be an object")
    signal = value.get("signal")
    if signal not in PREFERENCE_SIGNALS:
        raise ValueError("invalid preference_risk signal")
    form = value.get("form")
    if not isinstance(form, str):
        raise ValueError("preference_risk form must be a string")
    language = value.get("language")
    if language not in {"none", "indonesian", "malaysian", "both"}:
        raise ValueError("invalid preference_risk language")
    rationale = value.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("preference_risk rationale is required")
    if (
        signal in {"credible-everyday-alternative", "shared-common-form", "same-sense-competition"}
        and not form.strip()
    ):
        raise ValueError("a concrete competing form must be named")
    if signal == "no-preference-concern" and (form.strip() or language != "none"):
        raise ValueError("no-preference-concern cannot name a competing form")
    return dict(value)


def preference_flags(value: Mapping[str, Any] | None) -> set[str]:
    if not value:
        return set()
    signal = value.get("signal")
    return {
        "credible-everyday-alternative": {"credible-competing-form"},
        "shared-common-form": {"shared-common-form"},
        "preference-strength-uncertain": {"preference-uncertainty"},
        "regional-or-register-competition": {"regional-register-risk"},
        "same-sense-competition": {"credible-competing-form"},
        "verifier-explicitly-questions-preference": {"preference-uncertainty"},
    }.get(signal, set())


def legacy_preference_flags(verifier: Mapping[str, Any]) -> set[str]:
    """Read existing Batch 2 outputs without inventing a new model judgment."""
    synonym = verifier.get("shared_synonym_case")
    risk = verifier.get("nonblocking_risk")
    if synonym == "weak-contrast":
        return {"preference-uncertainty"}
    if synonym == "useful-preference" and risk in {"minor", "concrete", "substantial"}:
        return {"preference-uncertainty"}
    return set()


def audit_selection(
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    medium_sample: int = 2,
    high_sample: int = 1,
) -> dict[str, list[str]]:
    """Return stable candidate-ref → selection reasons; sample only unflagged cards."""
    selected: dict[str, list[str]] = {}
    accepted = [row for row in rows if row.get("outcome") == "accepted"]
    for row in accepted:
        ref = str(row["candidate_ref"])
        reasons = []
        if row.get("relation") == "false-friend":
            reasons.append("false-friend")
        if row.get("confidence_tier") in {"low", "very-low"}:
            reasons.append(f"confidence:{row['confidence_tier']}")
        strong = STRONG_AUDIT_FLAGS.intersection(row.get("review_flags", []))
        reasons.extend(f"flag:{flag}" for flag in sorted(strong))
        if reasons:
            selected[ref] = reasons
    rng = random.Random(seed)
    for tier, limit in (("medium", medium_sample), ("high", high_sample)):
        pool = sorted(
            (
                row
                for row in accepted
                if row.get("confidence_tier") == tier and str(row["candidate_ref"]) not in selected
            ),
            key=lambda row: str(row["candidate_ref"]),
        )
        for row in rng.sample(pool, min(limit, len(pool))):
            selected[str(row["candidate_ref"])] = [f"stratified-sample:{tier}"]
    return dict(sorted(selected.items()))
