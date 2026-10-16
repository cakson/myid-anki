from __future__ import annotations

import pytest
from tests.integration.test_scaling_curation import _curated_fixture

from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.scaling.audit import audit_run
from indo_malay_anki.scaling.promotion import promote_run
from indo_malay_anki.scaling.qa import record_finding, select_sample
from indo_malay_anki.scaling.store import RunError
from indo_malay_anki.scaling.workflow import build_run, close_run, resolve_candidate


def _ready(repo_factory):
    root = repo_factory(rows=[])
    store = _curated_fixture(root)
    audit_run(store)
    promote_run(store)
    build_run(store)
    roster = select_sample(store)
    return store, roster


def _baseline_repo(repo_factory):
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
    return root


def test_close_requires_completed_current_qa_and_current_build(repo_factory):
    store, roster = _ready(repo_factory)
    with pytest.raises(RunError, match="sample is incomplete"):
        close_run(store)
    item = roster["sample"][0]
    record_finding(
        store,
        item["slice_id"],
        item["candidate_id"],
        {"finding_class": "none", "rationale": "Both answers and cue were checked."},
    )
    store.add_brake("fixture-brake", detail="identity check")
    with pytest.raises(RunError, match="active safety brake"):
        close_run(store)
    from indo_malay_anki.scaling.qa import dispose_brake

    dispose_brake(store, "fixture-brake", "Identity check passed.")
    source = store.root / "data" / "vocabulary.tsv"
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RunError, match="no valid offline build"):
        close_run(store)


def test_close_rejects_stale_qa_population(repo_factory, monkeypatch):
    import indo_malay_anki.scaling.qa as qa

    store, roster = _ready(repo_factory)
    item = roster["sample"][0]
    record_finding(
        store,
        item["slice_id"],
        item["candidate_id"],
        {"finding_class": "none", "rationale": "No issue found."},
    )
    actual = qa.clean_population(store)
    monkeypatch.setattr(
        qa,
        "clean_population",
        lambda _store: [*actual, {**actual[0], "candidate_id": "new-member"}],
    )
    with pytest.raises(RunError, match="roster is stale"):
        close_run(store)


def test_close_rejects_unresolved_material_qa_finding(repo_factory):
    store = _curated_fixture(_baseline_repo(repo_factory))
    audit_run(store)
    promote_run(store)
    build_run(store)
    item = select_sample(store)["sample"][0]
    record_finding(
        store,
        item["slice_id"],
        item["candidate_id"],
        {"finding_class": "learner-critical-answer", "rationale": "Fixture mismatch."},
    )
    with pytest.raises(RunError, match="unresolved material QA finding"):
        close_run(store)


def test_zero_clean_accepted_population_can_close_with_empty_qa_sample(repo_factory):
    store = _curated_fixture(_baseline_repo(repo_factory))
    item = store.load()["slices"][0]
    resolve_candidate(
        store,
        f"{item['slice_id']}:biscuit-01",
        "hold",
        "Fixture card lacks enough evidence to promote.",
    )
    audit_run(store)
    assert promote_run(store)["active_promoted_count"] == 0
    build_run(store)
    roster = select_sample(store)
    assert roster["population_count"] == roster["sample_count"] == 0
    assert close_run(store)["state"] == "complete"
