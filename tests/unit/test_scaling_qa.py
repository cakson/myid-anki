from __future__ import annotations

from tests.integration.test_scaling_curation import _curated_fixture

from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.scaling import qa
from indo_malay_anki.scaling.audit import audit_run
from indo_malay_anki.scaling.promotion import promote_run
from indo_malay_anki.scaling.store import RunStore


def test_random_qa_sample_is_reproducible_and_has_minimum_five(tmp_path, monkeypatch):
    store = RunStore(tmp_path, "qa-fixture")
    store.create(requested_count=100, proposal_cap=120, baseline_count=0)
    population = [
        {
            "slice_id": "slice-1",
            "candidate_id": f"candidate-{number:03d}",
            "confidence": "high" if number % 2 else "medium",
            "risk_path": "ordinary-fast" if number % 2 else "escalated",
            "decision_digest": str(number),
        }
        for number in range(40)
    ]
    monkeypatch.setattr(qa, "clean_population", lambda _store: population)
    first = qa.select_sample(store)
    assert first["sample_count"] == 5
    assert qa.select_sample(store) == first
    assert len({item["risk_path"] for item in first["sample"]}) == 2
    population.append({**population[-1], "candidate_id": "candidate-040"})
    second = qa.select_sample(store)
    assert second["population_digest"] != first["population_digest"]
    assert (store.path / "qa" / f"roster-{first['population_digest'][:12]}.json").exists()
    population.pop()
    assert qa.select_sample(store)["population_digest"] == first["population_digest"]


def test_metadata_only_qa_finding_does_not_set_safety_brake(tmp_path):
    store = RunStore(tmp_path, "metadata-fixture")
    store.create(requested_count=1, proposal_cap=2, baseline_count=0)
    atomic_json(
        store.path / "qa" / "findings" / "slice--candidate.json",
        {"finding_class": "metadata-only", "error_category": "minor-label"},
    )
    atomic_json(
        store.path / "qa" / "findings" / "slice--candidate.response.json",
        {"response": {"finding_class": "metadata-only"}},
    )
    assert qa.evaluate_brakes(store) == []


def test_new_critical_finding_reapplies_disposed_promotion_brake(tmp_path):
    store = RunStore(tmp_path, "critical-fixture")
    store.create(requested_count=1, proposal_cap=2, baseline_count=0)
    folder = store.path / "qa" / "findings"
    for number in (1, 2):
        atomic_json(
            folder / f"finding-{number}.json",
            {"finding_class": "learner-critical-answer"},
        )
    assert any(item["active"] for item in qa.evaluate_brakes(store))
    qa.dispose_brake(store, "two-learner-critical-errors", "Both cards withheld.")
    assert not any(item["active"] for item in qa.evaluate_brakes(store))
    atomic_json(folder / "finding-3.json", {"finding_class": "learner-critical-answer"})
    brakes = qa.evaluate_brakes(store)
    assert sum(item["active"] for item in brakes) == 1
    assert brakes[-1]["reason"] == "two-learner-critical-errors"


def test_material_random_qa_finding_withdraws_promoted_card(repo_factory):
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
    promote_run(store)
    item = qa.select_sample(store)["sample"][0]
    finding = qa.record_finding(
        store,
        item["slice_id"],
        item["candidate_id"],
        {"finding_class": "learner-critical-answer", "rationale": "Fixture mismatch."},
    )
    assert finding["withdrawal"]["status"] == "withdrawn"
    assert len((root / "data" / "vocabulary.tsv").read_text(encoding="utf-8").splitlines()) == 2
    retry = promote_run(store)
    assert retry["active_promoted_count"] == 0
    assert retry["blocked_slices"]
