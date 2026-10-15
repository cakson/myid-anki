"""Export guardrails and permanent ID assignment tests."""

import hashlib
import json

import pytest

from indo_malay_anki.curation import export as export_module
from indo_malay_anki.curation.export import ExportError, export_batches, recover_export
from indo_malay_anki.curation.ids import allocate_id, validate_ledger
from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.curation.workflow import init_batch


def test_id_ledger_never_reuses_retired_id():
    ledger = {
        "schema_version": 1,
        "assignments": [
            {
                "id": "000001",
                "batch_id": "legacy-car-001",
                "candidate_id": "car-01",
                "assigned_at": "2026-10-02",
                "semantic_concept_key": "road passenger vehicle",
            }
        ],
    }
    validate_ledger(ledger)
    assert allocate_id(ledger) == "000002"


def test_pending_batch_cannot_export_or_mutate_learner_source(tmp_path):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text("old data\n", encoding="utf-8")
    before = source.read_bytes()
    init_batch(tmp_path, "home-001", "home", 2)
    with pytest.raises(ExportError):
        export_batches(tmp_path, ["home-001"])
    assert source.read_bytes() == before
    assert not (tmp_path / "curation" / "id-ledger.json").exists()


def test_export_recovery_refuses_broken_journal(tmp_path):
    journal = tmp_path / "curation" / "export-journal.json"
    journal.parent.mkdir()
    journal.write_text(json.dumps({"schema_version": 1, "phase": "replacing"}), encoding="utf-8")
    with pytest.raises(ExportError):
        recover_export(tmp_path)


def accepted_fixture(tmp_path, monkeypatch):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text(
        "id\tenglish\tindonesian\tmalaysian\timage\ttags\n"
        "000001\tcar\tmobil\tkereta\t\ttransport\n",
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "home-001", "home", 1)
    store.save_candidate(
        "house-01",
        {
            "candidate_id": "house-01",
            "english": "sauce",
            "indonesian": "saus",
            "malaysian": "sos",
            "sense": "condiment served with food",
            "tags": ["home"],
        },
    )
    manifest = store.manifest()
    store.save_manifest(
        type(manifest)(
            manifest.batch_id,
            manifest.topic,
            manifest.scope,
            manifest.candidate_limit,
            manifest.prompt_set_version,
            manifest.created_at,
            "closed",
        )
    )
    atomic_json(
        store.path / "report.json",
        {
            "status": "closed",
            "pending": 0,
            "decisions": [{"candidate_id": "house-01", "outcome": "accepted"}],
        },
    )
    ledger = tmp_path / "curation" / "id-ledger.json"
    atomic_json(
        ledger,
        {
            "schema_version": 1,
            "assignments": [
                {
                    "id": "000001",
                    "batch_id": "legacy-car-001",
                    "candidate_id": "car-01",
                    "assigned_at": "2026-10-02",
                    "semantic_concept_key": "road passenger vehicle",
                }
            ],
        },
    )
    monkeypatch.setattr(
        export_module,
        "current_results",
        lambda *args: {
            "normalize-and-dedupe": {"overlaps": []},
            "relation-proposal": {"relation": "similar", "english": "sauce"},
        },
    )

    def accepted(*args, **kwargs):
        return {"outcome": "accepted"}

    monkeypatch.setattr(export_module, "decide_candidate", accepted)
    return source, ledger


@pytest.mark.parametrize("failed_target", ["id-ledger.json", "vocabulary.tsv"])
def test_export_replaces_both_files_or_rolls_back(tmp_path, monkeypatch, failed_target):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    before_source, before_ledger = source.read_bytes(), ledger.read_bytes()
    original_replace = export_module.os.replace
    failed = False

    def replace_once(src, dst):
        nonlocal failed
        if not failed and str(dst).endswith(failed_target):
            failed = True
            raise OSError("injected replacement failure")
        return original_replace(src, dst)

    monkeypatch.setattr(export_module.os, "replace", replace_once)
    with pytest.raises(OSError, match="injected"):
        export_batches(tmp_path, ["home-001"])
    assert failed
    assert source.read_bytes() == before_source
    assert ledger.read_bytes() == before_ledger
    assert not (tmp_path / "curation" / "export-journal.json").exists()


def test_interrupted_journal_restores_old_pair_before_next_export(tmp_path, monkeypatch):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    old_source, old_ledger = source.read_bytes(), ledger.read_bytes()
    (tmp_path / "curation" / "source.backup").write_bytes(old_source)
    (tmp_path / "curation" / "ledger.backup").write_bytes(old_ledger)
    new_ledger = b'{"schema_version":1,"assignments":[]}'
    ledger.write_bytes(new_ledger)

    def sha(data):
        return hashlib.sha256(data).hexdigest()

    atomic_json(
        tmp_path / "curation" / "export-journal.json",
        {
            "schema_version": 1,
            "phase": "replacing",
            "old_source_digest": sha(old_source),
            "old_ledger_digest": sha(old_ledger),
            "new_source_digest": sha(b"new TSV"),
            "new_ledger_digest": sha(new_ledger),
        },
    )
    assert recover_export(tmp_path)
    assert source.read_bytes() == old_source
    assert ledger.read_bytes() == old_ledger
    assert not (tmp_path / "curation" / "export-journal.json").exists()


def test_final_overlap_screen_blocks_new_id_for_duplicate_in_other_batch(tmp_path, monkeypatch):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    other = init_batch(tmp_path, "food-001", "food", 1)
    other.save_candidate(
        "home-duplicate",
        {
            "candidate_id": "home-duplicate",
            "english": "sauces",
            "indonesian": "saus",
            "malaysian": "sos",
            "sense": "condiment served with food",
        },
    )
    with pytest.raises(ExportError, match="overlap"):
        export_batches(tmp_path, ["home-001"])
    assert b"000002" not in source.read_bytes()
    assert b"000002" not in ledger.read_bytes()


def test_repeat_export_rechecks_closed_report_before_reusing_id(tmp_path, monkeypatch):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    report = tmp_path / "curation" / "batches" / "home-001" / "report.json"
    atomic_json(
        report,
        {
            "status": "closed",
            "pending": 0,
            "decisions": [{"candidate_id": "house-01", "outcome": "hold"}],
        },
    )
    before_source, before_ledger = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match="stale decision"):
        export_batches(tmp_path, ["home-001"])
    assert source.read_bytes() == before_source
    assert ledger.read_bytes() == before_ledger


def test_export_blocks_shared_relation_even_if_report_claims_acceptance(tmp_path, monkeypatch):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        export_module,
        "current_results",
        lambda *args: {
            "normalize-and-dedupe": {"overlaps": []},
            "relation-proposal": {"relation": "same", "english": "sauce"},
        },
    )
    before_source, before_ledger = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match="shared vocabulary"):
        export_batches(tmp_path, ["home-001"])
    assert source.read_bytes() == before_source
    assert ledger.read_bytes() == before_ledger


def test_later_rejected_duplicate_does_not_invalidate_existing_export(tmp_path, monkeypatch):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    source_before, ledger_before = source.read_bytes(), ledger.read_bytes()
    later = init_batch(tmp_path, "growth-audit-001", "duplicate audit", 1)
    later.save_candidate(
        "house-plural",
        {
            "candidate_id": "house-plural",
            "english": "sauces",
            "indonesian": "saus",
            "malaysian": "sos",
            "sense": "plural cue for a sauce",
        },
    )
    later.append_event(
        "house-plural",
        {"role": "explicit-final", "decision": {"outcome": "rejected", "reason": "duplicate"}},
    )
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    assert source.read_bytes() == source_before
    assert ledger.read_bytes() == ledger_before
