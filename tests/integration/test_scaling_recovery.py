from __future__ import annotations

import pytest
from tests.integration.test_scaling_curation import _curated_fixture

import indo_malay_anki.scaling.audit as audit_module
from indo_malay_anki.scaling.promotion import promote_run
from indo_malay_anki.scaling.qa import record_finding, select_sample
from indo_malay_anki.scaling.store import RunError


def _clearance(_root, _role, _prompt):
    return {
        "response": {
            "schema_version": 1,
            "verdict": "cleared",
            "finding_class": "none",
            "rationale": "Both answers and the shared sense align.",
            "claim_reviews": [
                {
                    "subject": "both learner answers",
                    "conclusion": "Supported for the cue",
                    "material_risk": False,
                    "evidence_limitation": "Fixture review",
                }
            ],
        },
        "model": "independent-fixture",
        "elapsed_ms": 1,
        "model_calls": 1,
    }


def test_audit_reuses_captured_response_after_interrupted_validation(repo_factory, monkeypatch):
    store = _curated_fixture(repo_factory(rows=[]), risky=True)
    original = audit_module._validate_response
    interrupted = False
    calls = 0

    def provider(*args):
        nonlocal calls
        calls += 1
        return _clearance(*args)

    def fail_once(response):
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise OSError("interrupted after audit response capture")
        return original(response)

    monkeypatch.setattr(audit_module, "_validate_response", fail_once)
    with pytest.raises(OSError, match="interrupted after audit response capture"):
        audit_module.audit_run(store, provider=provider)
    monkeypatch.setattr(audit_module, "_validate_response", original)
    assert len(list((store.path / "audits").glob("*/*.response.json"))) == 1
    assert audit_module.audit_run(store, provider=provider)["cleared"] == 1
    assert calls == 1


def test_failed_audit_provider_can_resume_without_prior_record(repo_factory):
    store = _curated_fixture(repo_factory(rows=[]), risky=True)
    with pytest.raises(RunError, match="retrieval failed"):
        audit_module.audit_run(
            store, provider=lambda *_args: (_ for _ in ()).throw(RunError("retrieval failed"))
        )
    assert not list((store.path / "audits").glob("*/*.response.json"))
    assert audit_module.audit_run(store, provider=_clearance)["cleared"] == 1


def test_qa_finding_replay_is_idempotent_and_conflict_is_rejected(repo_factory):
    store = _curated_fixture(repo_factory(rows=[]))
    audit_module.audit_run(store)
    promote_run(store)
    item = select_sample(store)["sample"][0]
    clean = {"finding_class": "none", "rationale": "Both answers checked."}
    first = record_finding(store, item["slice_id"], item["candidate_id"], clean)
    assert record_finding(store, item["slice_id"], item["candidate_id"], clean) == first
    with pytest.raises(RunError, match="conflicting QA finding replay"):
        record_finding(
            store,
            item["slice_id"],
            item["candidate_id"],
            {"finding_class": "metadata-only", "rationale": "Different outcome."},
        )
