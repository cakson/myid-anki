from __future__ import annotations

import json
from pathlib import Path

from tests.integration.test_scaling_curation import _curated_fixture

from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.scaling.audit import audit_run
from indo_malay_anki.scaling.promotion import promote_run, withdraw_candidate
from indo_malay_anki.scaling.report import run_report


def test_report_reconciles_active_ever_assigned_and_separate_work(repo_factory):
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
    report = run_report(store)
    assert report["baseline_count"] == 1
    assert report["requested_count"] == report["admitted_count"] == 1
    assert report["proposed_count"] == 1
    assert sum(report["generated_category_distribution"].values()) == 1
    assert sum(report["admitted_category_distribution"].values()) == 1
    assert report["decision_counts"] == {"accepted": 1}
    assert report["promotion"]["active_new"] == 1
    assert report["promotion"]["promotable"] == 1
    assert report["promotion"]["ever_assigned"] == 1
    assert report["promotion"]["withdrawn"] == 0
    assert report["active_promoted_yield"] == 1
    assert report["work"]["generation"]["model_calls"] == 1
    assert report["work"]["production"]["model_calls"] == 2
    assert report["work"]["risk_audit"]["model_calls"] is None
    assert report["risk_audit"]["performed"] == 0
    assert report["risk_audit"]["finding_classes"] == {}
    assert report["work"]["random_qa"]["model_calls"] is None
    assert report["throughput"]["production_decisions_per_hour"] is not None
    assert report["coverage_before"] is not None
    assert report["coverage_after"] is not None

    slice_id = store.load()["slices"][0]["slice_id"]
    withdraw_candidate(store, slice_id, "biscuit-01", reason="fixture material correction")
    withdrawn = run_report(store)
    assert withdrawn["final_corpus_count"] == 1
    assert withdrawn["promotion"]["active_new"] == 0
    assert withdrawn["promotion"]["ever_assigned"] == 1
    assert withdrawn["promotion"]["withdrawn"] == 1
    assert withdrawn["active_promoted_yield"] == 0


def test_first_operational_report_reconciles_100_candidates_and_costs():
    root = Path(__file__).resolve().parents[2]
    report = json.loads(
        (root / "curation/production-runs/corpus-004-001/report.json").read_text(encoding="utf-8")
    )
    assert report["state"] == "complete"
    assert report["requested_count"] == report["admitted_count"] == 100
    assert sum(report["decision_counts"].values()) == 100
    assert sum(report["generated_category_distribution"].values()) == report["proposed_count"]
    assert sum(report["admitted_category_distribution"].values()) == 100
    assert report["promotion"]["active_new"] == 68
    assert report["promotion"]["ever_assigned"] == 68
    assert report["promotion"]["withdrawn"] == 0
    assert report["promotion"]["withheld_candidates"] == 29
    assert report["active_promoted_yield"] == 0.68
    assert sum(report["coverage_after"].values()) - sum(report["coverage_before"].values()) == 68
    assert report["risk_audit"]["performed"] == 60
    assert report["qa"]["reviewed_count"] == report["qa"]["sample_count"] == 7
    assert report["work"]["production"]["model_calls"] == 199
    assert report["work"]["risk_audit"]["model_calls"] == 60
    assert report["work"]["random_qa"]["model_calls"] == 7
    assert report["throughput"]["production_decision_denominator"] == 100
    assert report["throughput"]["active_promoted_denominator"] == 68
    assert report["work"]["usage_unavailable_reasons"]["retrievals"]
