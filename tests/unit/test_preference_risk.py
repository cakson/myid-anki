"""Preference signals guide review and do not constitute linguistic evidence."""

import pytest

from indo_malay_anki.curation.preference_risk import (
    audit_selection,
    validate_preference_risk,
)


def test_preference_signal_requires_named_competitor_for_credible_claim():
    with pytest.raises(ValueError, match="named"):
        validate_preference_risk(
            {
                "signal": "credible-everyday-alternative",
                "form": "",
                "language": "malaysian",
                "rationale": "An unnamed alternative may compete.",
            }
        )


def test_audit_routes_strong_medium_flag_and_samples_unflagged_high():
    rows = [
        {
            "candidate_ref": "a",
            "outcome": "accepted",
            "relation": "different-common-word",
            "confidence_tier": "medium",
            "review_flags": ["credible-competing-form"],
        },
        {
            "candidate_ref": "b",
            "outcome": "accepted",
            "relation": "similar",
            "confidence_tier": "high",
            "review_flags": [],
        },
        {
            "candidate_ref": "c",
            "outcome": "accepted",
            "relation": "similar",
            "confidence_tier": "low",
            "review_flags": [],
        },
        {
            "candidate_ref": "d",
            "outcome": "hold",
            "relation": "similar",
            "confidence_tier": None,
            "review_flags": [],
        },
    ]
    selected = audit_selection(rows, seed=7, medium_sample=0, high_sample=1)
    assert selected == {
        "a": ["flag:credible-competing-form"],
        "b": ["stratified-sample:high"],
        "c": ["confidence:low"],
    }
