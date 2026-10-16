from __future__ import annotations

import pytest

from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json
from indo_malay_anki.scaling.audit import audit_run
from indo_malay_anki.scaling.coverage import approve_allocation, inventory
from indo_malay_anki.scaling.promotion import promote_run, withdraw_candidate
from indo_malay_anki.scaling.qa import record_finding, select_sample
from indo_malay_anki.scaling.store import RunError, RunStore
from indo_malay_anki.scaling.workflow import build_run, close_run, curate_run, generate_run


def _curated_fixture(root, *, risky=False):
    store = RunStore(root, "curation-fixture")
    snapshot = inventory(root)
    store.create(requested_count=1, proposal_cap=2, baseline_count=snapshot["card_count"])
    counts = {key: 0 for key in snapshot["counts"]}
    counts["food-cooking"] = 1
    approve_allocation(store, counts, snapshot, reason="fixture")

    def generate(_root, role, _prompt):
        assert role == "generate"
        return {
            "response": {
                "schema_version": 1,
                "role": role,
                "model": "fixture",
                "result": {
                    "candidates": [
                        {
                            "candidate_id": "biscuit-01",
                            "english": "biscuit",
                            "indonesian": "biskuit",
                            "malaysian": "biskut",
                            "sense": "small baked snack",
                            "tags": ["food-cooking"],
                        }
                    ]
                },
            },
            "model": "fixture",
            "elapsed_ms": 1,
            "input_tokens": 10,
            "output_tokens": 10,
            "model_calls": 1,
            "retrievals": 0,
        }

    generate_run(store, provider=generate)
    calls = []

    def curate(_root, role, _prompt):
        calls.append(role)
        result = (
            {"overlaps": []}
            if role == "normalize-and-dedupe"
            else {
                "verdict": "agree",
                "relation": "similar",
                "concerns": [],
                "material_concerns": [],
                "objection_assessments": [],
                "rationale": "The forms differ in useful everyday spelling.",
                "cue_alignment": "aligned",
                "cue_rewrite": "",
                "cue_rationale": "Both mean the same baked snack.",
                "shared_synonym_case": "none",
                "shared_synonym_rationale": "No shared synonym.",
                "nonblocking_risk": "concrete" if risky else "none",
                "risk_rationale": "A variant may compete." if risky else "",
                "preference_risk": {
                    "signal": "no-preference-concern",
                    "form": "",
                    "language": "none",
                    "rationale": "No competing form identified.",
                },
            }
        )
        return {
            "response": {"schema_version": 1, "role": role, "model": "fixture", "result": result},
            "model": "fixture",
            "elapsed_ms": 1,
            "input_tokens": 10,
            "output_tokens": 10,
            "model_calls": 1,
            "retrievals": 0,
        }

    result = curate_run(store, provider=curate)
    assert result["state"] == "awaiting-risk-audit"
    assert calls == ["normalize-and-dedupe", "independent-verification"]
    slice_store = BatchStore(root, result["slices"][0]["slice_id"])
    assert read_json(slice_store.path / "report.json")["accepted"] == 1
    assert curate_run(store, provider=curate)["state"] == "awaiting-risk-audit"
    assert len(calls) == 2
    return store


def test_v31_optimistic_curation_settles_one_slice_without_learner_source(tmp_path):
    _curated_fixture(tmp_path)
    assert not (tmp_path / "data" / "vocabulary.tsv").exists()


def test_clean_card_promotes_builds_and_closes_after_random_qa(repo_factory):
    root = repo_factory(rows=[])
    store = _curated_fixture(root)
    assert audit_run(store) == {"required": 0, "cleared": 0, "withheld": 0, "pending": 0}
    promotion = promote_run(store)
    assert promotion["active_promoted_count"] == 1
    assert promote_run(store)["active_promoted_count"] == 0
    assert store.load()["state"] == "qa-monitoring"
    built = build_run(store)
    assert built["notes"] == built["cards"] == 1
    roster = select_sample(store)
    assert roster["sample_count"] == 1
    with pytest.raises(RunError, match="sample is incomplete"):
        close_run(store)
    item = roster["sample"][0]
    record_finding(
        store,
        item["slice_id"],
        item["candidate_id"],
        {"finding_class": "none", "rationale": "No issue observed."},
    )
    report = close_run(store)
    assert report["state"] == "complete"
    assert report["promotion"]["active_new"] == 1
    assert report["qa"]["reviewed_count"] == 1


def test_withdrawal_and_guarded_restoration_keep_permanent_id(repo_factory):
    root = repo_factory()
    atomic_json(
        root / "curation" / "id-ledger.json",
        {
            "schema_version": 1,
            "assignments": [
                {
                    "id": "000001",
                    "batch_id": "legacy",
                    "candidate_id": "car",
                    "assigned_at": "2026-10-01",
                    "semantic_concept_key": "road vehicle",
                }
            ],
        },
    )
    store = _curated_fixture(root)
    audit_run(store)
    first = promote_run(store)
    concept_id = first["new_ids"][0]
    slice_id = store.load()["slices"][0]["slice_id"]
    assert withdraw_candidate(store, slice_id, "biscuit-01", reason="fixture finding") == {
        "id": concept_id,
        "status": "withdrawn",
    }
    assert withdraw_candidate(store, slice_id, "biscuit-01", reason="fixture retry") == {
        "id": concept_id,
        "status": "already-withdrawn",
    }
    restored = promote_run(store)
    assert restored["new_ids"] == []
    from indo_malay_anki.curation.ids import assigned_id, load_ledger

    assert assigned_id(load_ledger(root), slice_id, "biscuit-01") == concept_id


def test_risk_selected_card_needs_independent_clearance_before_promotion(repo_factory):
    root = repo_factory(rows=[])
    store = _curated_fixture(root, risky=True)
    with pytest.raises(RunError, match="settled risk-audit dispositions"):
        select_sample(store)
    from indo_malay_anki.scaling.workflow import transition

    transition(store, "promotion-ready")
    blocked = promote_run(store)
    assert blocked["active_promoted_count"] == 0
    assert blocked["blocked_slices"]

    def reviewer(_root, role, _prompt):
        assert role == "independent-verification"
        return {
            "response": {
                "schema_version": 1,
                "verdict": "cleared",
                "finding_class": "none",
                "rationale": "The reviewed sense and both spellings align.",
                "claim_reviews": [
                    {
                        "subject": "biscuit spellings",
                        "conclusion": "Both supported",
                        "material_risk": False,
                        "evidence_limitation": "Fixture review",
                    }
                ],
            },
            "model": "independent-fixture",
            "elapsed_ms": 1,
            "input_tokens": 10,
            "output_tokens": 10,
            "model_calls": 1,
            "retrievals": 0,
        }

    result = audit_run(store, provider=reviewer)
    assert result["required"] == result["cleared"] == 1
    promoted = promote_run(store)
    assert promoted["active_promoted_count"] == 1


def test_captured_curation_response_is_reused_after_interrupted_ingest(repo_factory, monkeypatch):
    import indo_malay_anki.scaling.workflow as workflow

    root = repo_factory(rows=[])
    store = RunStore(root, "curation-capture")
    snapshot = inventory(root)
    store.create(requested_count=1, proposal_cap=2, baseline_count=0)
    counts = {key: 0 for key in snapshot["counts"]}
    counts["food-cooking"] = 1
    approve_allocation(store, counts, snapshot, reason="fixture")

    def generate(_root, _role, _prompt):
        return {
            "response": {
                "candidates": [
                    {
                        "candidate_id": "biscuit-01",
                        "english": "biscuit",
                        "indonesian": "biskuit",
                        "malaysian": "biskut",
                        "sense": "small baked snack",
                        "tags": ["food-cooking"],
                    }
                ]
            },
            "model": "fixture",
            "elapsed_ms": 1,
        }

    generate_run(store, provider=generate)
    calls = []

    def curate(_root, role, _prompt):
        calls.append(role)
        return {"response": {"overlaps": []}, "model": "fixture", "elapsed_ms": 1}

    original_ingest = workflow.ingest_response
    interrupted = False

    def fail_once(*args, **kwargs):
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise OSError("interrupted after response capture")
        return original_ingest(*args, **kwargs)

    monkeypatch.setattr(workflow, "ingest_response", fail_once)
    with pytest.raises(OSError, match="interrupted after response capture"):
        curate_run(store, provider=curate)
    monkeypatch.setattr(workflow, "ingest_response", original_ingest)
    captured = list((store.path / "curation-responses").glob("*/*/*.json"))
    assert len(captured) == 1

    def resumed(_root, role, _prompt):
        assert role == "independent-verification"
        calls.append(role)
        return {
            "response": {
                "verdict": "agree",
                "relation": "similar",
                "concerns": [],
                "material_concerns": [],
                "objection_assessments": [],
                "rationale": "The forms have a useful spelling difference.",
                "cue_alignment": "aligned",
                "cue_rewrite": "",
                "cue_rationale": "Both refer to the same snack.",
                "shared_synonym_case": "none",
                "shared_synonym_rationale": "No shared synonym.",
                "nonblocking_risk": "none",
                "risk_rationale": "",
                "preference_risk": {
                    "signal": "no-preference-concern",
                    "form": "",
                    "language": "none",
                    "rationale": "No competing form.",
                },
            },
            "model": "fixture",
            "elapsed_ms": 1,
        }

    assert curate_run(store, provider=resumed)["state"] == "awaiting-risk-audit"
    assert calls == ["normalize-and-dedupe", "independent-verification"]
