"""Policy-v3 fast path and historical prompt pins stay separate from learner data."""

import json
from dataclasses import replace

from indo_malay_anki.curation.packets import make_packet
from indo_malay_anki.curation.report import batch_report, review_priority
from indo_malay_anki.curation.workflow import (
    check_candidate,
    finalize_hold,
    ingest_response,
    init_batch,
    packet_for,
)


def _send(store, role, result, candidate=None):
    ingest_response(
        store,
        role,
        json.dumps({"schema_version": 1, "role": role, "model": "fixture", "result": result}),
        candidate,
    )


def test_fast_path_accepts_without_source_research_or_adversary(tmp_path):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text(
        '{"prompt_set_version":"2.0.0","decision_policy_version":"3.0.0"}',
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "food-001", "food", 1)
    candidate = {
        "candidate_id": "biscuit-01",
        "english": "biscuit",
        "indonesian": "biskuit",
        "malaysian": "biskut",
        "sense": "small baked snack",
    }
    _send(store, "generate", {"candidates": [candidate]})
    _send(store, "normalize-and-dedupe", {"overlaps": []}, "biscuit-01")
    packet = packet_for(store, "independent-verification", "biscuit-01")
    assert packet["prompt_set_version"] == "2.0.0"
    assert "audited_evidence" not in packet["context"]
    assert "indonesian_usage" not in packet["context"]
    _send(
        store,
        "independent-verification",
        {
            "verdict": "agree",
            "relation": "similar",
            "concerns": [],
            "material_concerns": [],
            "rationale": "Useful ordinary spelling contrast.",
        },
        "biscuit-01",
    )
    decision = check_candidate(store, "biscuit-01")
    assert decision["outcome"] == "accepted"
    assert decision["confidence_tier"] == "medium"
    assert decision["stage_statuses"]["evidence-audit"] == "skipped-by-policy"
    report = batch_report(store)
    assert report["confidence_distribution"] == {"medium": 1}
    assert report["review_priority"] == ["biscuit-01"]
    assert not (tmp_path / "data" / "vocabulary.tsv").exists()

    held = finalize_hold(
        store,
        "biscuit-01",
        "Independent audit found a material unresolved cue-sense mismatch.",
    )
    assert held["outcome"] == "hold"
    assert held["reason_codes"] == ["material-unresolved-issue"]
    assert batch_report(store)["held"] == 1


def test_reconsideration_prompt_override_does_not_repin_manifest(tmp_path):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text(
        '{"prompt_set_version":"1.5.0","decision_policy_version":"2.0.0"}',
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "old-001", "food", 1)
    candidate = {
        "candidate_id": "item-01",
        "english": "biscuit",
        "indonesian": "biskuit",
        "malaysian": "biskut",
        "sense": "small baked snack",
    }
    normal = make_packet(
        store.root, store.manifest(), "independent-verification", candidate=candidate, stages={}
    )
    reconsidered = make_packet(
        store.root,
        replace(store.manifest()),
        "independent-verification",
        candidate=candidate,
        stages={},
        prompt_set_version="2.0.0",
    )
    assert normal["prompt_set_version"] == "1.5.0"
    assert reconsidered["prompt_set_version"] == "2.0.0"
    assert normal["input_digest"] != reconsidered["input_digest"]
    assert store.manifest().prompt_set_version == "1.5.0"


def test_review_priority_orders_accepted_confidence_tiers():
    rows = [
        {"candidate_id": "high", "outcome": "accepted", "confidence_tier": "high"},
        {"candidate_id": "low", "outcome": "accepted", "confidence_tier": "low"},
        {"candidate_id": "very", "outcome": "accepted", "confidence_tier": "very-low"},
        {"candidate_id": "held", "outcome": "hold"},
    ]
    assert review_priority(rows) == ["very", "low", "high"]
