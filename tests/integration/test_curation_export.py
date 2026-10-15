"""Export guardrails and permanent ID assignment tests."""

import hashlib
import json
import stat
from dataclasses import replace

import pytest

from indo_malay_anki.curation import export as export_module
from indo_malay_anki.curation.export import ExportError, export_batches, recover_export
from indo_malay_anki.curation.ids import allocate_id, validate_ledger
from indo_malay_anki.curation.packets import digest
from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.curation.workflow import init_batch
from indo_malay_anki.model import stable_guid


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
        return {"outcome": "accepted", "relation": "similar"}

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


def test_export_preserves_source_and_ledger_file_modes(tmp_path, monkeypatch):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    source.chmod(0o644)
    ledger.chmod(0o644)
    export_batches(tmp_path, ["home-001"])
    assert stat.S_IMODE(source.stat().st_mode) == 0o644
    assert stat.S_IMODE(ledger.stat().st_mode) == 0o644


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
        "decide_candidate",
        lambda *args, **kwargs: {"outcome": "accepted", "relation": "same"},
    )
    monkeypatch.setattr(
        export_module,
        "current_results",
        lambda *args: {
            "normalize-and-dedupe": {"overlaps": []},
            "relation-proposal": {"relation": "same", "english": "sauce"},
        },
    )
    before_source, before_ledger = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match="shared or unresolved relation"):
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


def v31_fixture(tmp_path, monkeypatch, *, relation="similar", risk_path="ordinary-fast"):
    source, ledger = accepted_fixture(tmp_path, monkeypatch)
    store = export_module.BatchStore(tmp_path, "home-001")
    store.save_manifest(replace(store.manifest(), decision_policy_version="3.1.0"))
    decision = {"outcome": "accepted", "relation": relation, "risk": {"path": risk_path}}
    monkeypatch.setattr(export_module, "decide_candidate", lambda *args, **kwargs: decision)
    stages = {
        "normalize-and-dedupe": {"overlaps": []},
        "relation-proposal": {"relation": "different-common-word", "english": "sauce"},
        "independent-verification": {"relation": relation, "verdict": "agree"},
    }
    monkeypatch.setattr(export_module, "current_results", lambda *args: stages)
    atomic_json(
        store.path / "report.json",
        {"status": "closed", "pending": 0, "decisions": [{**decision, "candidate_id": "house-01"}]},
    )
    row = export_module._projected_row(store.candidate("house-01"), stages, decision)
    item = {
        "status": "eligible",
        "audit_route": "none",
        "audit_verdict": "not-required",
        "decision_digest": digest(decision),
        "content_digest": digest(row),
    }
    record = {
        "schema_version": 1,
        "batch_id": "home-001",
        "batch_safety_brake": False,
        "candidates": {"house-01": item},
    }
    return source, ledger, store, decision, stages, record


def test_v31_export_requires_current_eligibility_and_allows_clean_unaudited(tmp_path, monkeypatch):
    source, ledger, store, _, _, record = v31_fixture(tmp_path, monkeypatch)
    before = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match="missing promotion eligibility"):
        export_batches(tmp_path, ["home-001"])
    assert (source.read_bytes(), ledger.read_bytes()) == before
    atomic_json(store.path / "promotion-eligibility.json", record)
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"status": "withheld"}, "not promotion eligible"),
        ({"status": "unresolved"}, "not promotion eligible"),
        ({"audit_route": "risk-based", "audit_verdict": "not-required"}, "not cleared"),
        (
            {"audit_route": "random-monitoring", "audit_verdict": "withheld"},
            "withheld or unresolved",
        ),
        ({"content_digest": "stale"}, "stale promotion"),
    ],
)
def test_v31_export_refuses_ineligible_or_stale_clearance(tmp_path, monkeypatch, change, message):
    source, ledger, store, _, _, record = v31_fixture(tmp_path, monkeypatch)
    record["candidates"]["house-01"].update(change)
    atomic_json(store.path / "promotion-eligibility.json", record)
    before = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match=message):
        export_batches(tmp_path, ["home-001"])
    assert (source.read_bytes(), ledger.read_bytes()) == before


def test_v31_risk_based_review_must_be_cleared(tmp_path, monkeypatch):
    _, _, store, _, _, record = v31_fixture(tmp_path, monkeypatch, risk_path="escalated")
    atomic_json(store.path / "promotion-eligibility.json", record)
    with pytest.raises(ExportError, match="risk-based independent audit"):
        export_batches(tmp_path, ["home-001"])
    record["candidates"]["house-01"].update(audit_route="risk-based", audit_verdict="cleared")
    atomic_json(store.path / "promotion-eligibility.json", record)
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]


def test_v31_batch_safety_brake_blocks_export(tmp_path, monkeypatch):
    source, ledger, store, _, _, record = v31_fixture(tmp_path, monkeypatch)
    record["batch_safety_brake"] = True
    atomic_json(store.path / "promotion-eligibility.json", record)
    before = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match="safety brake"):
        export_batches(tmp_path, ["home-001"])
    assert (source.read_bytes(), ledger.read_bytes()) == before


def test_v31_strong_review_flag_requires_risk_audit(tmp_path, monkeypatch):
    _, _, store, decision, _, record = v31_fixture(tmp_path, monkeypatch)
    decision["review_flags"] = ["cue-sense-ambiguity"]
    record["candidates"]["house-01"]["decision_digest"] = digest(decision)
    atomic_json(store.path / "promotion-eligibility.json", record)
    atomic_json(
        store.path / "report.json",
        {"status": "closed", "pending": 0, "decisions": [{**decision, "candidate_id": "house-01"}]},
    )
    with pytest.raises(ExportError, match="risk-based independent audit"):
        export_batches(tmp_path, ["home-001"])


@pytest.mark.parametrize("outcome", ["hold", "rejected", "pending"])
def test_v31_nonaccepted_candidate_cannot_export(tmp_path, monkeypatch, outcome):
    source, ledger, store, decision, _, record = v31_fixture(tmp_path, monkeypatch)
    decision["outcome"] = outcome
    atomic_json(
        store.path / "report.json",
        {"status": "closed", "pending": 0, "decisions": [{**decision, "candidate_id": "house-01"}]},
    )
    atomic_json(store.path / "promotion-eligibility.json", record)
    before = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError):
        export_batches(tmp_path, ["home-001"])
    assert (source.read_bytes(), ledger.read_bytes()) == before


def test_v31_export_uses_final_verified_relation_without_changing_guid(tmp_path, monkeypatch):
    source, _, store, _, _, record = v31_fixture(tmp_path, monkeypatch)
    atomic_json(store.path / "promotion-eligibility.json", record)
    original_guid = stable_guid("000002")
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    assert b"sauce\tsaus\tsos\tsimilar" in source.read_bytes()
    assert stable_guid("000002") == original_guid


def test_v31_export_uses_verified_cue_correction(tmp_path, monkeypatch):
    source, _, store, decision, stages, record = v31_fixture(tmp_path, monkeypatch)
    decision["cue_correction"] = {"from": "sauce", "to": "condiment sauce"}
    row = export_module._projected_row(store.candidate("house-01"), stages, decision)
    record["candidates"]["house-01"].update(
        decision_digest=digest(decision), content_digest=digest(row)
    )
    atomic_json(store.path / "promotion-eligibility.json", record)
    atomic_json(
        store.path / "report.json",
        {"status": "closed", "pending": 0, "decisions": [{**decision, "candidate_id": "house-01"}]},
    )
    assert export_batches(tmp_path, ["home-001"]) == ["000002"]
    assert b"condiment sauce\tsaus\tsos\tsimilar" in source.read_bytes()


def test_v31_export_rejects_stale_report_before_id_assignment(tmp_path, monkeypatch):
    source, ledger, store, _, _, record = v31_fixture(tmp_path, monkeypatch)
    atomic_json(store.path / "promotion-eligibility.json", record)
    report = export_module.read_json(store.path / "report.json")
    report["decisions"][0]["relation"] = "different-common-word"
    atomic_json(store.path / "report.json", report)
    before = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match="stale decision/report"):
        export_batches(tmp_path, ["home-001"])
    assert (source.read_bytes(), ledger.read_bytes()) == before


def test_v31_export_rejects_changed_candidate_content(tmp_path, monkeypatch):
    source, ledger, store, _, _, record = v31_fixture(tmp_path, monkeypatch)
    atomic_json(store.path / "promotion-eligibility.json", record)
    changed = store.candidate("house-01")
    changed["malaysian"] = "kuah"
    atomic_json(store.candidate_path("house-01") / "proposal.json", changed)
    before = source.read_bytes(), ledger.read_bytes()
    with pytest.raises(ExportError, match="stale promotion"):
        export_batches(tmp_path, ["home-001"])
    assert (source.read_bytes(), ledger.read_bytes()) == before
