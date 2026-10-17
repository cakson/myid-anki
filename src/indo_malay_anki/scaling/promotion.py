"""Feature 004 eligibility writer and guarded Feature 003 export adapter."""

from __future__ import annotations

import csv
import time

from indo_malay_anki.curation.export import (
    ExportError,
    _projected_row,
    commit_learner_rows,
    export_batches,
    recover_export,
)
from indo_malay_anki.curation.ids import assigned_id, load_ledger
from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json
from indo_malay_anki.curation.workflow import current_results

from .audit import current_audit, decision_core, selection_reasons
from .store import RunError, RunStore, digest, file_digest, utc_now


def _rows(root):
    source = root / "data" / "vocabulary.tsv"
    if not source.exists():
        return []
    with source.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def write_eligibility(store: RunStore, slice_id: str) -> dict:
    manifest = store.load()
    slice_store = BatchStore(store.root, slice_id)
    report = read_json(slice_store.path / "report.json")
    if report.get("status") != "closed" or slice_store.manifest().status != "closed":
        raise RunError("slice must have a current closed report before promotion")
    if any(item.get("active") for item in manifest.get("brakes", [])):
        raise RunError("active promotion brake")
    entries = {}
    for decision in report["decisions"]:
        if decision["outcome"] != "accepted":
            continue
        candidate_id = decision["candidate_id"]
        row = _projected_row(
            slice_store.candidate(candidate_id),
            current_results(slice_store, candidate_id),
            decision,
        )
        reasons = selection_reasons(decision)
        audit = current_audit(store, slice_id, candidate_id, decision) if reasons else None
        finding_path = store.path / "qa" / "findings" / f"{slice_id}--{candidate_id}.json"
        material_qa = False
        if finding_path.exists():
            finding = read_json(finding_path)
            if finding.get("resolution_status") == "resolved-withheld":
                from .qa import qa_resolution_current

                material_qa = not qa_resolution_current(store, finding)
            else:
                if finding.get("finding_class") in {"learner-critical-answer", "cue-content"}:
                    from .qa import qa_resolution_current

                    material_qa = not finding.get("resolved") or not qa_resolution_current(
                        store, finding
                    )
        eligible = not material_qa and (
            not reasons or audit is not None and audit["verdict"] == "cleared"
        )
        entries[candidate_id] = {
            "status": "eligible" if eligible else "withheld",
            "audit_route": "risk-based" if reasons else "none",
            "audit_verdict": (
                "not-required" if not reasons else audit["verdict"] if audit else "pending"
            ),
            "decision_digest": digest(decision_core(decision)),
            "content_digest": digest(row),
            "withheld_reasons": (["unresolved-material-qa"] if material_qa else [])
            + (
                ["missing-or-uncleared-risk-audit"]
                if reasons and not audit or audit and audit["verdict"] != "cleared"
                else []
            ),
        }
    record = {
        "schema_version": 1,
        "batch_id": slice_id,
        "batch_safety_brake": False,
        "generated_at": utc_now(),
        "candidates": entries,
    }
    atomic_json(slice_store.path / "promotion-eligibility.json", record)
    return record


def promote_run(store: RunStore) -> dict:
    manifest = store.load()
    if manifest["state"] not in {"promotion-ready", "qa-monitoring"}:
        raise RunError("promotion requires settled production and risk audit")
    if any(item.get("active") for item in manifest.get("brakes", [])):
        raise RunError("active promotion brake")
    try:
        recover_export(store.root)
    except ExportError as exc:
        store.add_brake("identity-export-inconsistency", detail=str(exc))
        raise
    before_ids = {row["id"] for row in _rows(store.root)}
    before_assigned = {item["id"] for item in load_ledger(store.root)["assignments"]}
    result = {"promoted_slices": [], "blocked_slices": [], "new_ids": []}
    for item in manifest["slices"]:
        if not item["candidate_ids"]:
            continue
        slice_store = BatchStore(store.root, item["slice_id"])
        if slice_store.manifest().status != "closed":
            result["blocked_slices"].append({"slice_id": item["slice_id"], "reason": "open"})
            continue
        record = write_eligibility(store, item["slice_id"])
        blocked = [
            candidate_id
            for candidate_id, entry in record["candidates"].items()
            if entry["status"] != "eligible"
        ]
        if blocked:
            result["blocked_slices"].append({"slice_id": item["slice_id"], "candidates": blocked})
            continue
        started = time.perf_counter()
        try:
            exported = export_batches(store.root, [item["slice_id"]])
        except (ExportError, OSError) as exc:
            store.add_brake("identity-export-inconsistency", detail=str(exc))
            raise
        result["promoted_slices"].append(item["slice_id"])
        result["new_ids"].extend(
            concept_id for concept_id in exported if concept_id not in before_assigned
        )
        store.append_event(
            "promotion-slice",
            "complete",
            details={
                "slice_id": item["slice_id"],
                "exported_ids": exported,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "source_digest": file_digest(store.root / "data" / "vocabulary.tsv"),
                "ledger_digest": file_digest(store.root / "curation" / "id-ledger.json"),
            },
        )
    from .workflow import transition

    if store.load()["state"] == "promotion-ready":
        transition(store, "qa-monitoring")
    result["active_promoted_count"] = len({row["id"] for row in _rows(store.root)} - before_ids)
    return result


def withdraw_candidate(store: RunStore, slice_id: str, candidate_id: str, *, reason: str) -> dict:
    """Remove one unsafe active row through the existing source/ledger journal."""
    if not reason.strip():
        raise RunError("withdrawal requires a reason")
    recover_export(store.root)
    ledger = load_ledger(store.root)
    concept_id = assigned_id(ledger, slice_id, candidate_id)
    if concept_id is None:
        raise RunError("candidate has no permanent assignment")
    rows = _rows(store.root)
    matched = [row for row in rows if row["id"] == concept_id]
    if not matched:
        return {"id": concept_id, "status": "already-withdrawn"}
    slice_store = BatchStore(store.root, slice_id)
    report = read_json(slice_store.path / "report.json")
    decision = next(item for item in report["decisions"] if item["candidate_id"] == candidate_id)
    if decision["outcome"] == "accepted":
        projected = _projected_row(
            slice_store.candidate(candidate_id),
            current_results(slice_store, candidate_id),
            decision,
        )
        if matched[0] != {"id": concept_id, **projected}:
            store.add_brake(
                "identity-export-inconsistency",
                detail=f"source row mismatch for {slice_id}:{candidate_id}",
            )
            raise RunError("active row differs from assigned candidate; promotion brake required")
    commit_learner_rows(
        store.root, [row for row in rows if row["id"] != concept_id], ledger, [slice_id]
    )
    store.append_event(
        "withdrawal",
        "complete",
        details={
            "slice_id": slice_id,
            "candidate_id": candidate_id,
            "id": concept_id,
            "reason": reason,
        },
    )
    return {"id": concept_id, "status": "withdrawn"}
