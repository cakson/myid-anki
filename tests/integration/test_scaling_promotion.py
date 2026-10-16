from __future__ import annotations

import json
from dataclasses import replace

import pytest
from tests.integration.test_scaling_curation import _curated_fixture
from tests.integration.test_scaling_recovery import _clearance

from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.curation.workflow import init_batch
from indo_malay_anki.scaling import promotion
from indo_malay_anki.scaling.audit import audit_run
from indo_malay_anki.scaling.store import RunError, RunStore


def test_clean_accept_is_eligible_before_random_qa(repo_factory, monkeypatch):
    root = repo_factory()
    run = RunStore(root, "promotion-fixture")
    manifest = run.create(requested_count=1, proposal_cap=2, baseline_count=1)
    slice_store = init_batch(root, "promotion-fixture-s001", "food", 1)
    slice_store.save_candidate(
        "sauce-01",
        {
            "candidate_id": "sauce-01",
            "english": "sauce",
            "indonesian": "saus",
            "malaysian": "sos",
            "sense": "condiment",
            "tags": ["food"],
        },
    )
    slice_store.save_manifest(replace(slice_store.manifest(), status="closed"))
    decision = {
        "candidate_id": "sauce-01",
        "outcome": "accepted",
        "relation": "similar",
        "risk": {"path": "ordinary-fast"},
        "confidence_tier": "high",
        "review_flags": [],
    }
    atomic_json(
        slice_store.path / "report.json",
        {"status": "closed", "pending": 0, "decisions": [decision]},
    )
    manifest["slices"] = [
        {
            "slice_id": slice_store.batch_id,
            "candidate_ids": ["sauce-01"],
            "screened": [],
            "admitted": 1,
            "proposed": 1,
            "requested": 1,
            "category": "food-cooking",
        }
    ]
    run.save(manifest, expected_digest=run.manifest_digest())
    monkeypatch.setattr(
        promotion,
        "current_results",
        lambda *_args: {"relation-proposal": {"relation": "similar", "english": "sauce"}},
    )
    record = promotion.write_eligibility(run, slice_store.batch_id)
    assert record["candidates"]["sauce-01"]["status"] == "eligible"
    assert record["candidates"]["sauce-01"]["audit_route"] == "none"
    assert not (run.path / "qa" / "roster.json").exists()


def test_active_batch_brake_blocks_guarded_promotion(repo_factory):
    store = _curated_fixture(repo_factory(rows=[]))
    audit_run(store)
    store.add_brake("fixture-identity-brake", detail="check source identity")
    with pytest.raises(RunError, match="active promotion brake"):
        promotion.promote_run(store)
    assert len(promotion._rows(store.root)) == 0


def test_stale_audit_digest_withholds_risk_selected_card(repo_factory):
    store = _curated_fixture(repo_factory(rows=[]), risky=True)
    audit_run(store, provider=_clearance)
    path = next(
        item
        for item in (store.path / "audits").glob("*/*.json")
        if not item.name.endswith((".packet.json", ".response.json"))
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    record["decision_digest"] = "stale"
    atomic_json(path, record)
    result = promotion.promote_run(store)
    assert result["active_promoted_count"] == 0
    assert result["blocked_slices"]
    assert len(promotion._rows(store.root)) == 0
