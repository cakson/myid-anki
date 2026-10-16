from __future__ import annotations

import csv

import pytest

from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.scaling.coverage import allocation_draft, approve_allocation, inventory
from indo_malay_anki.scaling.store import RunError, RunStore


def _source(tmp_path):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    with source.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "tags"], delimiter="\t")
        writer.writeheader()
        writer.writerows(
            [
                {"id": "000001", "tags": "household kitchen"},
                {"id": "000002", "tags": "travel-vocabulary transport"},
                {"id": "000003", "tags": "unmapped-tag"},
            ]
        )
    return source


def test_one_primary_category_alias_and_unknown_visibility(tmp_path):
    _source(tmp_path)
    result = inventory(tmp_path)
    assert result["card_count"] == 3
    assert sum(result["counts"].values()) == 2
    assert result["counts"]["home"] == 1
    assert result["unmapped_rows"] == ["000003"]
    assert result["unknown_tags"] == ["unmapped-tag"]


def test_gap_draft_edit_total_and_freeze(tmp_path):
    _source(tmp_path)
    snapshot = inventory(tmp_path)
    draft = allocation_draft(snapshot, 100)
    assert sum(draft["counts"].values()) == 100
    assert draft["rationale"]
    assert draft["counts"]["home"] < draft["counts"]["common-verbs"]
    store = RunStore(tmp_path, "coverage-run")
    store.create(requested_count=100, proposal_cap=200, baseline_count=3)
    bad = {**draft["counts"], "home": draft["counts"]["home"] + 1}
    with pytest.raises(RunError, match="total"):
        approve_allocation(store, bad, snapshot, reason="bad")
    approved = approve_allocation(store, draft["counts"], snapshot, reason="draft accepted")
    assert approved["state"] == "allocation-approved"
    assert approved["allocation_digest"]
    with pytest.raises(RunError, match="draft"):
        approve_allocation(store, draft["counts"], snapshot, reason="again")


def test_promoted_category_uses_frozen_run_provenance_when_tags_are_specific(tmp_path):
    _source(tmp_path)
    store = RunStore(tmp_path, "coverage-provenance")
    manifest = store.create(requested_count=1, proposal_cap=2, baseline_count=3)
    manifest["slices"] = [{"slice_id": "coverage-provenance-s001", "category": "emotions"}]
    store.save(manifest, expected_digest=store.manifest_digest())
    atomic_json(
        tmp_path / "curation" / "id-ledger.json",
        {
            "schema_version": 1,
            "assignments": [
                {
                    "id": "000003",
                    "batch_id": "coverage-provenance-s001",
                    "candidate_id": "feel-01",
                    "assigned_at": "2026-10-15",
                    "semantic_concept_key": "a feeling",
                }
            ],
        },
    )
    result = inventory(tmp_path)
    assert result["primary_by_id"]["000003"] == "emotions"
    assert result["counts"]["emotions"] == 1
    assert result["unmapped_rows"] == []
