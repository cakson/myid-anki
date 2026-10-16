"""Independent, digest-bound risk review for Feature 004 promotion."""

from __future__ import annotations

import json
from pathlib import Path

from indo_malay_anki.curation.export import _projected_row
from indo_malay_anki.curation.preference_risk import STRONG_AUDIT_FLAGS
from indo_malay_anki.curation.report import batch_report
from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json
from indo_malay_anki.curation.workflow import current_results

from .provider import call_model
from .store import RunError, RunStore, digest, utc_now


def selection_reasons(decision: dict) -> list[str]:
    reasons = []
    if decision.get("risk", {}).get("path") in {"escalated", "false-friend"}:
        reasons.append("risk-path:" + decision["risk"]["path"])
    if decision.get("confidence_tier") in {"low", "very-low"}:
        reasons.append("confidence:" + decision["confidence_tier"])
    reasons.extend(
        "review-flag:" + flag
        for flag in sorted(STRONG_AUDIT_FLAGS.intersection(decision.get("review_flags", [])))
    )
    return reasons


def decision_core(decision: dict) -> dict:
    """Match the exact decision object hashed by Feature 003's exporter."""
    return {key: value for key, value in decision.items() if key != "candidate_id"}


def audit_path(store: RunStore, slice_id: str, candidate_id: str) -> Path:
    return store.path / "audits" / slice_id / f"{candidate_id}.json"


def current_audit(store: RunStore, slice_id: str, candidate_id: str, decision: dict) -> dict | None:
    path = audit_path(store, slice_id, candidate_id)
    if not path.exists():
        return None
    record = read_json(path)
    if (
        record.get("schema_version") != 1
        or record.get("run_id") != store.run_id
        or record.get("slice_id") != slice_id
        or record.get("candidate_id") != candidate_id
        or not record.get("attempt_id")
        or not record.get("reviewer", {}).get("invocation")
    ):
        return None
    try:
        _validate_response(record)
    except RunError:
        return None
    slice_store = BatchStore(store.root, slice_id)
    row = _projected_row(
        slice_store.candidate(candidate_id), current_results(slice_store, candidate_id), decision
    )
    if record.get("decision_digest") != digest(decision_core(decision)) or record.get(
        "content_digest"
    ) != digest(row):
        return None
    if record.get("route") != "risk-based" or record.get("selection_reasons") != selection_reasons(
        decision
    ):
        return None
    return record


def _validate_response(response: dict) -> dict:
    if not isinstance(response, dict) or response.get("schema_version") != 1:
        raise RunError("invalid independent audit response")
    if response.get("verdict") not in {"cleared", "needs-correction", "withheld"}:
        raise RunError("invalid independent audit verdict")
    if response.get("finding_class") not in {
        "none",
        "learner-critical-answer",
        "cue-content",
        "metadata-only",
    }:
        raise RunError("invalid independent audit finding class")
    reviews = response.get("claim_reviews")
    if (
        not isinstance(reviews, list)
        or not reviews
        or any(
            not isinstance(item, dict)
            or not str(item.get("subject", "")).strip()
            or not str(item.get("conclusion", "")).strip()
            or type(item.get("material_risk")) is not bool
            or (
                not item.get("evidence_refs")
                and not str(item.get("evidence_limitation", "")).strip()
            )
            for item in reviews
        )
    ):
        raise RunError("independent audit requires claim-specific reviews")
    if not str(response.get("rationale", "")).strip():
        raise RunError("independent audit requires rationale")
    if response["verdict"] == "cleared" and (
        response["finding_class"] in {"learner-critical-answer", "cue-content"}
        or any(item.get("material_risk") is True for item in reviews)
    ):
        raise RunError("material risk cannot be marked cleared")
    return response


def audit_run(store: RunStore, *, provider=call_model) -> dict:
    manifest = store.load()
    if manifest["state"] not in {"awaiting-risk-audit", "promotion-ready", "qa-monitoring"}:
        raise RunError("risk audit requires settled production decisions")
    summary = {"required": 0, "cleared": 0, "withheld": 0, "pending": 0}
    for item in manifest["slices"]:
        if not item["candidate_ids"]:
            continue
        slice_store = BatchStore(store.root, item["slice_id"])
        report = (
            batch_report(slice_store)
            if slice_store.manifest().status == "open"
            else read_json(slice_store.path / "report.json")
        )
        for decision in report["decisions"]:
            if decision["outcome"] != "accepted":
                continue
            reasons = selection_reasons(decision)
            if not reasons:
                continue
            summary["required"] += 1
            candidate_id = decision["candidate_id"]
            existing = current_audit(store, item["slice_id"], candidate_id, decision)
            if existing:
                summary["cleared" if existing["verdict"] == "cleared" else "withheld"] += 1
                continue
            row = _projected_row(
                slice_store.candidate(candidate_id),
                current_results(slice_store, candidate_id),
                decision,
            )
            packet = {
                "schema_version": 1,
                "route": "risk-based",
                "run_id": store.run_id,
                "slice_id": item["slice_id"],
                "candidate_id": candidate_id,
                "selection_reasons": reasons,
                "candidate": slice_store.candidate(candidate_id),
                "decision": decision_core(decision),
                "learner_content": row,
            }
            packet_digest = digest(packet)
            prompt = (
                "Independent risk audit of Indonesian versus Malaysian Malay learner card. "
                "Check both answers, English cue and sense, final relation, and any false-friend "
                "contrast. Return only JSON with schema_version=1, verdict (cleared, "
                "needs-correction, withheld), finding_class (none, learner-critical-answer, "
                "cue-content, metadata-only), rationale, and nonempty claim_reviews list. "
                "Each claim review needs subject, conclusion, material_risk boolean, and "
                "evidence_refs list or evidence_limitation. Be independent of the production "
                "verifier.\n" + json.dumps(packet, ensure_ascii=False)
            )
            path = audit_path(store, item["slice_id"], candidate_id)
            atomic_json(path.with_suffix(".packet.json"), packet)
            captured_path = path.with_suffix(".response.json")
            if captured_path.exists():
                captured = read_json(captured_path)
                if captured.get("packet_digest") != packet_digest:
                    raise RunError("stale captured audit response")
            else:
                answer = provider(store.root, "independent-verification", prompt)
                captured = {"packet_digest": packet_digest, **answer}
                atomic_json(captured_path, captured)
            try:
                result = _validate_response(captured["response"])
            except (KeyError, TypeError, ValueError) as exc:
                from .workflow import _archive_failed_capture

                _archive_failed_capture(store, captured_path, kind="risk-audit-response", error=exc)
                raise
            record = {
                "schema_version": 1,
                "run_id": store.run_id,
                "slice_id": item["slice_id"],
                "candidate_id": candidate_id,
                "route": "risk-based",
                "selection_reasons": reasons,
                "decision_digest": digest(decision_core(decision)),
                "content_digest": digest(row),
                "packet_digest": packet_digest,
                "attempt_id": digest({"packet": packet_digest, "at": utc_now()})[:16],
                "reviewer": {
                    "model": captured.get("model"),
                    "tool": "codex-cli",
                    "invocation": str(captured_path),
                },
                "reviewed_at": utc_now(),
                "claim_reviews": result["claim_reviews"],
                "verdict": result["verdict"],
                "finding_class": result["finding_class"],
                "rationale": result["rationale"],
                "correction_refs": [],
                "elapsed_ms": captured.get("elapsed_ms"),
                "model_calls": captured.get("model_calls"),
                "input_tokens": captured.get("input_tokens"),
                "output_tokens": captured.get("output_tokens"),
                "retrievals": captured.get("retrievals"),
            }
            atomic_json(path, record)
            store.append_event(
                "risk-audit",
                "complete",
                details={
                    "slice_id": item["slice_id"],
                    "candidate_id": candidate_id,
                    "verdict": record["verdict"],
                    "elapsed_ms": record["elapsed_ms"],
                    "model_calls": record["model_calls"],
                    "input_tokens": record["input_tokens"],
                    "output_tokens": record["output_tokens"],
                    "retrievals": record["retrievals"],
                },
            )
            summary["cleared" if record["verdict"] == "cleared" else "withheld"] += 1
            from .qa import evaluate_brakes

            evaluate_brakes(store)
    if manifest["state"] == "awaiting-risk-audit":
        from .workflow import transition

        transition(store, "promotion-ready")
    return summary
