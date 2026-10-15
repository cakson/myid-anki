"""Every role uses the central Luna policy with separate review calls."""

import json
from pathlib import Path

import pytest

from indo_malay_anki.curation.models import role_route
from indo_malay_anki.curation.records import AI_ROLES, RecordError
from indo_malay_anki.curation.workflow import _namespace_claim_ids, init_batch, packet_for


def test_role_model_routes_use_luna_for_all_roles():
    root = Path(__file__).resolve().parents[2]
    routes = {role: role_route(root, role) for role in AI_ROLES}
    assert set(routes) == set(AI_ROLES)
    assert all(routes[role]["model"] == "gpt-5.6-luna" for role in AI_ROLES)
    assert routes["independent-verification"]["reasoning_effort"] == "medium"
    assert routes["adversarial-review"]["reasoning_effort"] == "medium"


def test_route_reads_local_config_without_mutating_prompt_packets(tmp_path):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text(
        json.dumps(
            {"role_models": {"generate": {"model": "test-model", "reasoning_effort": "low"}}}
        ),
        encoding="utf-8",
    )
    assert role_route(tmp_path, "generate")["model"] == "test-model"


def test_costly_verifier_packet_requires_evidence_gate(tmp_path, monkeypatch):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text(
        '{"prompt_set_version":"1.1.0","decision_policy_version":"2.0.0"}',
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "food-001", "food", 1)
    store.save_candidate(
        "food-01",
        {
            "candidate_id": "food-01",
            "english": "spoon",
            "indonesian": "sendok",
            "malaysian": "sudu",
            "sense": "eating utensil",
        },
    )
    stages = {
        "generate": {},
        "normalize-and-dedupe": {"overlaps": []},
        "indonesian-usage": {"claims": []},
        "malaysian-usage": {"claims": []},
        "relation-proposal": {
            "english": "spoon",
            "aligned": True,
            "relation": "different-common-word",
            "claims": [],
        },
        "evidence-audit": {"observations": []},
    }
    monkeypatch.setattr("indo_malay_anki.curation.workflow.current_results", lambda *_: stages)
    with pytest.raises(RecordError, match="independent-verification is withheld"):
        packet_for(store, "independent-verification", "food-01")


def test_v2_adversarial_packet_requires_a_risk_trigger(tmp_path, monkeypatch):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text(
        '{"prompt_set_version":"1.1.0","decision_policy_version":"2.0.0"}',
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "food-001", "food", 1)
    candidate = {
        "candidate_id": "food-01",
        "english": "spoon",
        "indonesian": "sendok",
        "malaysian": "sudu",
        "sense": "eating utensil",
    }
    store.save_candidate("food-01", candidate)
    stages = {
        "generate": {},
        "normalize-and-dedupe": {"overlaps": []},
        "indonesian-usage": {"claims": []},
        "malaysian-usage": {"claims": []},
        "relation-proposal": {
            "english": "spoon",
            "aligned": True,
            "relation": "different-common-word",
            "claims": [],
        },
        "evidence-audit": {"observations": []},
    }
    monkeypatch.setattr("indo_malay_anki.curation.workflow.current_results", lambda *_: stages)
    with pytest.raises(RecordError, match="out of order"):
        packet_for(store, "adversarial-review", "food-01")
    stages["independent-verification"] = {
        "verdict": "object",
        "relation": "different-common-word",
        "concerns": [],
    }
    assert packet_for(store, "adversarial-review", "food-01")["role"] == "adversarial-review"


def test_evidence_audit_packet_rejects_duplicate_claim_ids(tmp_path, monkeypatch):
    store = init_batch(tmp_path, "food-001", "food", 1)
    store.save_candidate(
        "food-01",
        {
            "candidate_id": "food-01",
            "english": "spoon",
            "indonesian": "sendok",
            "malaysian": "sudu",
            "sense": "eating utensil",
        },
    )
    repeated = {"claim_id": "same-id", "claim_type": "meaning"}
    stages = {
        "generate": {},
        "normalize-and-dedupe": {"overlaps": []},
        "indonesian-usage": {"claims": [repeated]},
        "malaysian-usage": {"claims": [repeated]},
        "relation-proposal": {
            "english": "spoon",
            "aligned": True,
            "relation": "different-common-word",
            "claims": [],
        },
    }
    monkeypatch.setattr("indo_malay_anki.curation.workflow.current_results", lambda *_: stages)
    with pytest.raises(RecordError, match="duplicate-claim-id"):
        packet_for(store, "evidence-audit", "food-01")


def test_locale_claim_namespaces_preserve_source_lead_links():
    result = {
        "claims": [{"claim_id": "meaning", "proposition": "example"}],
        "source_leads": [{"url": "https://example.org", "claim_ids": ["meaning"]}],
    }
    indonesia = _namespace_claim_ids("indonesian-usage", result)
    malaysia = _namespace_claim_ids("malaysian-usage", result)
    assert indonesia["claims"][0]["claim_id"] == "indonesian-usage:meaning"
    assert malaysia["claims"][0]["claim_id"] == "malaysian-usage:meaning"
    assert indonesia["source_leads"][0]["claim_ids"] == ["indonesian-usage:meaning"]
    assert result["claims"][0]["claim_id"] == "meaning"
