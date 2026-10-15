import random

from scripts.audit_prospective_preference_batch import select
from scripts.calibrate_operational_audit_budget import build_dataset, choose, deterministic_reasons


def test_frozen_deterministic_reasons_match_current_router():
    rows = {
        "risky": {
            "candidate_ref": "risky",
            "outcome": "accepted",
            "relation": "different-common-word",
            "confidence_tier": "medium",
            "review_flags": ["credible-competing-form", "borrowed-form-competition"],
        }
    }
    assert deterministic_reasons(rows["risky"]) == select(rows)["risky"]


def test_random_selection_never_uses_audit_label():
    rows = [
        {
            "candidate_ref": f"card-{number}",
            "audit_category": "critical" if number == 0 else "confirmed-good",
            "production_features": {
                "relation": "different-common-word" if number % 2 else "similar",
                "confidence_tier": "medium" if number % 3 else "high",
            },
        }
        for number in range(12)
    ]
    before = choose(rows, 4, random.Random(77), "stratified")
    for row in rows:
        row["audit_category"] = "critical"
    after = choose(rows, 4, random.Random(77), "stratified")
    assert len(before) == 4
    assert before == after


def test_frozen_cohort_retains_unlabeled_accepts():
    dataset = build_dataset()
    rows = list(dataset["records"].values())
    assert len(rows) == 182
    assert sum(row["audit_category"] == "critical" for row in rows) == 20
    assert sum(row["audit_category"] is None for row in rows) == 29
    assert sum(bool(row["deterministic_reasons"]) for row in rows) == 107
