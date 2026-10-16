from __future__ import annotations

import pytest

from indo_malay_anki.scaling.audit import _validate_response, selection_reasons
from indo_malay_anki.scaling.store import RunError


def test_risk_selection_matches_frozen_export_predicate():
    assert selection_reasons({"risk": {"path": "ordinary-fast"}, "confidence_tier": "high"}) == []
    assert selection_reasons({"risk": {"path": "false-friend"}, "confidence_tier": "medium"}) == [
        "risk-path:false-friend"
    ]
    assert "confidence:low" in selection_reasons(
        {"risk": {"path": "ordinary-fast"}, "confidence_tier": "low"}
    )


def test_independent_audit_rejects_material_clearance_and_unexplained_claims():
    base = {
        "schema_version": 1,
        "verdict": "cleared",
        "finding_class": "none",
        "rationale": "Both answers match the intended sense.",
        "claim_reviews": [
            {
                "subject": "both answers",
                "conclusion": "Supported",
                "material_risk": False,
                "evidence_limitation": "No direct citation available",
            }
        ],
    }
    assert _validate_response(base) == base
    with pytest.raises(RunError, match="material risk"):
        _validate_response(
            {**base, "claim_reviews": [{**base["claim_reviews"][0], "material_risk": True}]}
        )
    with pytest.raises(RunError, match="claim-specific"):
        _validate_response(
            {**base, "claim_reviews": [{**base["claim_reviews"][0], "evidence_limitation": ""}]}
        )
