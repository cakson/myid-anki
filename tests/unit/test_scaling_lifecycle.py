from __future__ import annotations

import pytest

from indo_malay_anki.scaling.store import RunError, RunStore
from indo_malay_anki.scaling.workflow import pause, reconcile_artifacts, resume, transition


def test_state_guards_and_pause_resume(tmp_path):
    store = RunStore(tmp_path, "lifecycle")
    store.create(requested_count=2, proposal_cap=4, baseline_count=1)
    with pytest.raises(RunError, match="invalid transition"):
        transition(store, "promoting")
    transition(store, "allocation-approved")
    pause(store, "model unavailable")
    assert store.load()["state"] == "paused"
    assert store.load()["prior_state"] == "allocation-approved"
    resume(store, "provider restored")
    assert store.load()["state"] == "allocation-approved"


def test_complete_is_terminal(tmp_path):
    store = RunStore(tmp_path, "lifecycle")
    store.create(requested_count=1, proposal_cap=2, baseline_count=1)
    manifest = store.load()
    store.save({**manifest, "state": "complete"})
    with pytest.raises(RunError, match="terminal"):
        pause(store, "later")


def test_reconcile_detects_changed_canonical_input(tmp_path):
    store = RunStore(tmp_path, "lifecycle")
    store.create(requested_count=1, proposal_cap=2, baseline_count=1)
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text("first")
    manifest = store.load()
    store.save({**manifest, "source_digest": "invalid"})
    assert reconcile_artifacts(store)["source_digest"] == str(source)
