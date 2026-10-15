"""The frozen first fresh audit permits only the corrected, safe cohort."""

from pathlib import Path

from scripts.promote_fresh_benchmark import corrected_items, load_inputs

ROOT = Path(__file__).resolve().parents[2]


def test_complete_audit_and_correction_overlay_preserve_candidate_identity():
    production, audits = load_inputs(ROOT)
    items = corrected_items(ROOT, production, audits)

    assert len(items) == 44
    assert sum(item["promotion_status"] == "ready" for item in items) == 41
    assert {item["candidate_ref"] for item in items if item["promotion_status"] == "withheld"} == {
        "fresh-actions-001:action-07",
        "fresh-home-001:home-10",
        "fresh-travel-001:travel-03",
    }
    by_ref = {item["candidate_ref"]: item for item in items}
    receipt = by_ref["fresh-food-001:food-07"]
    assert receipt["original_candidate"]["english"] == "receipt"
    assert receipt["candidate"]["english"] == "printed receipt"
    comb = by_ref["fresh-home-001:home-08"]
    assert comb["original_candidate"]["malaysian"] == "sikat rambut"
    assert comb["candidate"]["malaysian"] == "sikat"
    assert all(
        item["candidate"]["candidate_id"] == item["original_candidate"]["candidate_id"]
        for item in items
    )
    assert all(
        item["relation"] in {"similar", "different-common-word"}
        for item in items
        if item["promotion_status"] == "ready"
    )
