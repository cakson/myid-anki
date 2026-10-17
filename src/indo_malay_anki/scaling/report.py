"""Reconcile parent-run counts, coverage, and measured work without estimates."""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from indo_malay_anki.curation.ids import assigned_id, load_ledger
from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json

from .audit import current_audit, selection_reasons
from .coverage import inventory
from .promotion import _rows
from .store import RunStore, utc_now


def _work(events: tuple[dict, ...], kind: str) -> dict:
    records = [
        item["details"] for item in events if item["kind"] == kind and item["status"] == "complete"
    ]
    measured = {}
    for field in ("elapsed_ms", "model_calls", "input_tokens", "output_tokens", "retrievals"):
        values = [item.get(field) for item in records]
        measured[field] = (
            sum(values) if values and all(isinstance(value, int) for value in values) else None
        )
    measured["attempts"] = len(records)
    return measured


def _sum_measured(records: list[dict], field: str) -> int | None:
    values = [item.get(field) for item in records]
    return sum(values) if values and all(isinstance(value, int) for value in values) else None


def run_report(store: RunStore, *, final: bool = False) -> dict:
    manifest = store.load()
    events = store.events()
    before_path = store.path / "coverage-before.json"
    before = read_json(before_path) if before_path.exists() else None
    after = inventory(store.root)
    decisions = []
    audit_required = audit_cleared = audit_withheld = 0
    audit_folder = store.path / "audits"
    audit_records = (
        [
            read_json(path)
            for path in audit_folder.glob("*/*.json")
            if not path.name.endswith((".packet.json", ".response.json"))
        ]
        if audit_folder.exists()
        else []
    )
    audit_findings = Counter(item.get("finding_class") for item in audit_records)
    audit_verdicts = Counter(item.get("verdict") for item in audit_records)
    for item in manifest["slices"]:
        if not item["candidate_ids"]:
            continue
        slice_store = BatchStore(store.root, item["slice_id"])
        path = slice_store.path / "report.json"
        if not path.exists():
            continue
        report = read_json(path)
        for decision in report["decisions"]:
            decisions.append({**decision, "slice_id": item["slice_id"]})
            if decision["outcome"] == "accepted" and selection_reasons(decision):
                audit_required += 1
                audit = current_audit(store, item["slice_id"], decision["candidate_id"], decision)
                if audit:
                    if audit["verdict"] == "cleared":
                        audit_cleared += 1
                    else:
                        audit_withheld += 1
    outcomes = Counter(item["outcome"] for item in decisions)
    relations = Counter(item.get("relation") for item in decisions if item["outcome"] == "accepted")
    confidence = Counter(
        item.get("confidence_tier") for item in decisions if item["outcome"] == "accepted"
    )
    risk_paths = Counter(
        item.get("risk", {}).get("path") for item in decisions if item["outcome"] == "accepted"
    )
    ledger = load_ledger(store.root)
    active_ids = {row["id"] for row in _rows(store.root)}
    assigned = [
        assigned_id(ledger, item["slice_id"], candidate_id)
        for item in manifest["slices"]
        for candidate_id in item["candidate_ids"]
    ]
    ever_assigned = {concept_id for concept_id in assigned if concept_id}
    active_new = ever_assigned & active_ids
    roster_path = store.path / "qa" / "roster.json"
    roster = read_json(roster_path) if roster_path.exists() else None
    findings_folder = store.path / "qa" / "findings"
    findings = (
        [
            read_json(path)
            for path in findings_folder.glob("*.json")
            if not path.name.endswith(".response.json")
        ]
        if findings_folder.exists()
        else []
    )
    qa_counts = Counter(item["finding_class"] for item in findings)
    material_qa = [
        item
        for item in findings
        if item.get("finding_class") in {"learner-critical-answer", "cue-content"}
    ]
    qa_resolution_counts = Counter(
        item.get("resolution_status", "unresolved") if item.get("resolved") else "unresolved"
        for item in material_qa
    )
    error_categories = Counter(
        item["error_category"] for item in findings if item.get("error_category")
    )
    screen_reasons = Counter(
        screen["reason"] for item in manifest["slices"] for screen in item["screened"]
    )
    generated_by_category = Counter()
    admitted_by_category = Counter()
    for item in manifest["slices"]:
        generated_by_category[item["category"]] += item["proposed"]
        admitted_by_category[item["category"]] += item["admitted"]
    generation = {
        field: _sum_measured(manifest["slices"], field)
        for field in ("elapsed_ms", "input_tokens", "output_tokens")
    }
    generation["model_calls"] = len(manifest["slices"])
    recovered_attempts = {
        item["details"]["source_path"]
        for item in events
        if item["kind"] == "generation-response-recovery" and item["status"] == "complete"
    }
    failed_folder = store.path / "generation-responses" / "failed"
    extra_attempts = (
        [
            read_json(path)
            for path in failed_folder.glob("*.json")
            if str(path.relative_to(store.root)) not in recovered_attempts
        ]
        if failed_folder.exists()
        else []
    )
    for field in ("elapsed_ms", "input_tokens", "output_tokens"):
        extra = _sum_measured(extra_attempts, field)
        if extra is not None:
            generation[field] = (generation[field] or 0) + extra
    generation["model_calls"] += len(extra_attempts)
    semantic = _work(events, "semantic-review")
    production = _work(events, "curation-call")
    audit_work = _work(events, "risk-audit")
    qa_usage = [item.get("usage") for item in findings if isinstance(item.get("usage"), dict)]
    qa_work = {
        field: _sum_measured(qa_usage, field)
        for field in ("elapsed_ms", "model_calls", "input_tokens", "output_tokens", "retrievals")
    }
    qa_work["reviewed"] = len(findings)
    promotion_work = _work(events, "promotion-slice")
    build_work = _work(events, "build")
    reported_at = manifest["updated_at"] if manifest["state"] == "complete" else utc_now()
    end_to_end_ms = round(
        (
            datetime.fromisoformat(reported_at) - datetime.fromisoformat(manifest["created_at"])
        ).total_seconds()
        * 1000
    )
    production_ms = production["elapsed_ms"]
    proposed_count = manifest.get("proposed_count", 0)
    no_contrast_count = sum(
        "no-meaningful-cross-language-contrast" in item.get("reason_codes", [])
        for item in decisions
    )
    duplicate_waste = (
        screen_reasons["duplicate"]
        + screen_reasons["redundant"]
        + sum("confirmed-duplicate" in item.get("reason_codes", []) for item in decisions)
    )
    report = {
        "schema_version": 1,
        "run_id": store.run_id,
        "workflow_version": manifest["workflow_version"],
        "policy_version": "3.1.0",
        "state": manifest["state"],
        "report_status": "final" if final else "provisional",
        "created_at": manifest["created_at"],
        "reported_at": reported_at,
        "baseline_count": manifest["baseline_count"],
        "final_corpus_count": len(active_ids),
        "growth_milestones": {
            "200_plus": {"target": 200, "reached": len(active_ids) >= 200},
            "500": {"target": 500, "remaining": max(0, 500 - len(active_ids))},
            "1000": {"target": 1000, "remaining": max(0, 1000 - len(active_ids))},
        },
        "allocation": manifest["allocation"],
        "coverage_before": before["counts"] if before else None,
        "coverage_after": after["counts"],
        "requested_count": manifest["requested_count"],
        "proposed_count": manifest.get("proposed_count", 0),
        "admitted_count": manifest["admitted_count"],
        "screened_out_count": manifest.get("screened_out_count", 0),
        "screen_reasons": dict(screen_reasons),
        "generated_category_distribution": dict(sorted(generated_by_category.items())),
        "admitted_category_distribution": dict(sorted(admitted_by_category.items())),
        "decision_counts": dict(outcomes),
        "relation_distribution": dict(relations),
        "confidence_distribution": dict(confidence),
        "risk_path_distribution": dict(risk_paths),
        "no_contrast_rejected": no_contrast_count,
        "risk_audit": {
            "required": audit_required,
            "cleared": audit_cleared,
            "withheld": audit_withheld,
            "pending": audit_required - audit_cleared - audit_withheld,
            "performed": len(audit_records),
            "finding_classes": dict(audit_findings),
            "verdicts": dict(audit_verdicts),
        },
        "qa": {
            "population_count": roster["population_count"] if roster else None,
            "sample_count": roster["sample_count"] if roster else None,
            "reviewed_count": len(findings),
            "findings": dict(qa_counts),
            "material_resolution_statuses": dict(qa_resolution_counts),
        },
        "promotion": {
            "promotable": outcomes["accepted"],
            "active_new": len(active_new),
            "ever_assigned": len(ever_assigned),
            "withdrawn": len(ever_assigned - active_ids),
            "withheld": outcomes["accepted"] - len(active_new),
            "withheld_candidates": outcomes["hold"] + outcomes["accepted"] - len(active_new),
            "rejected_candidates": outcomes["rejected"],
        },
        "active_promoted_yield": len(active_new) / manifest["admitted_count"]
        if manifest["admitted_count"]
        else None,
        "work": {
            "generation": generation,
            "semantic_review": semantic,
            "production": production,
            "risk_audit": audit_work,
            "random_qa": qa_work,
            "promotion": promotion_work,
            "build": build_work,
            "end_to_end": {"elapsed_ms": end_to_end_ms},
            "usage_unavailable_reasons": {
                "retrievals": "Local model adapter does not expose retrieval counts",
                "non_model_tokens": "Promotion and build do not make model calls",
                "empty_stage": "Null totals mean no measured call occurred in that stage",
            },
        },
        "throughput": {
            "production_decisions_per_hour": (
                len(decisions) * 3_600_000 / production_ms
                if production_ms and len(decisions) == manifest["admitted_count"]
                else None
            ),
            "active_promoted_cards_per_end_to_end_hour": (
                len(active_new) * 3_600_000 / end_to_end_ms if end_to_end_ms else None
            ),
            "production_decision_denominator": len(decisions),
            "active_promoted_denominator": len(active_new),
        },
        "quality_monitoring": {
            "learner_critical_per_100_active_promoted": (
                100 * qa_counts["learner-critical-answer"] / len(active_new) if active_new else None
            ),
            "post_promotion_corrections": sum(bool(item.get("withdrawal")) for item in findings),
            "random_qa_discoveries": len(findings) - qa_counts["none"],
            "risk_audit_learner_critical_findings": audit_findings["learner-critical-answer"],
            "repeated_error_categories": {
                key: count for key, count in error_categories.items() if count > 1
            },
            "hold_rate": outcomes["hold"] / len(decisions) if decisions else None,
            "reject_rate": outcomes["rejected"] / len(decisions) if decisions else None,
            "no_contrast_generation_rate": (
                (screen_reasons["prior-same"] + no_contrast_count) / proposed_count
                if proposed_count
                else None
            ),
            "duplicate_generation_rate": duplicate_waste / proposed_count
            if proposed_count
            else None,
            "denominators": {
                "active_promoted": len(active_new),
                "curated": len(decisions),
                "proposed": proposed_count,
            },
        },
        "brakes": manifest.get("brakes", []),
        "resumability_incidents": [
            item
            for item in events
            if item["kind"] in {"pause", "resume", "interruption", "generation-response-recovery"}
        ],
    }
    if final:
        atomic_json(store.path / "report.json", report)
    return report
