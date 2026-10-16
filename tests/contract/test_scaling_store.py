from __future__ import annotations

import pytest

from indo_malay_anki.scaling.store import RunError, RunStore


def test_create_validates_and_preserves_unique_identity(tmp_path):
    store = RunStore(tmp_path, "corpus-004-001")
    manifest = store.create(requested_count=100, proposal_cap=200, baseline_count=137)
    assert manifest["run_id"] == "corpus-004-001"
    assert manifest["requested_count"] == 100
    assert manifest["state"] == "draft"
    with pytest.raises(RunError, match="already exists"):
        store.create(requested_count=100, proposal_cap=200, baseline_count=137)
    with pytest.raises(RunError, match="requested_count"):
        RunStore(tmp_path, "bad-count").create(
            requested_count=0, proposal_cap=20, baseline_count=137
        )


def test_atomic_manifest_and_conflicting_revision(tmp_path):
    store = RunStore(tmp_path, "run-one")
    original = store.create(requested_count=3, proposal_cap=6, baseline_count=1)
    changed = {**original, "state": "allocation-approved"}
    store.save(changed, expected_digest=store.manifest_digest())
    assert store.load()["state"] == "allocation-approved"
    with pytest.raises(RunError, match="conflicting"):
        store.save({**changed, "state": "generating"}, expected_digest="stale")


def test_event_sequence_and_idempotent_checkpoint(tmp_path):
    store = RunStore(tmp_path, "run-one")
    store.create(requested_count=2, proposal_cap=4, baseline_count=1)
    first = store.append_event("generate", "started", input_digest="a")
    second = store.append_event("generate", "complete", input_digest="a", output_digest="b")
    assert first.name == "000001.json"
    assert second.name == "000002.json"
    assert [event["status"] for event in store.events()] == ["started", "complete"]
    assert store.completed_checkpoint("generate", "a", "b") is not None
    assert store.completed_checkpoint("generate", "different", "b") is None
