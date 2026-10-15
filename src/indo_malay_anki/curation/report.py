"""Reconciled provisional and closed batch quality reports."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .gate import decide_candidate
from .store import BatchStore, atomic_json
from .workflow import close_manifest, current_results, utc_now


def batch_report(store: BatchStore) -> dict[str, Any]:
    candidate_ids = store.candidate_ids()
    decisions = []
    stage_failures = 0
    verifier_objections = 0
    adversarial_objections = 0
    duplicates = 0
    duplicate_resolutions: Counter[str] = Counter()
    evidence_failures = 0
    proposed_relations: Counter[str] = Counter()
    outcomes_by_relation: dict[str, Counter[str]] = {}
    reason_codes: Counter[str] = Counter()
    corrections = 0
    stage_failures += sum(event.get("status") == "failed" for event in store.batch_events())
    for candidate_id in candidate_ids:
        events = store.events(candidate_id)
        explicit = next(
            (event for event in reversed(events) if event.get("role") == "explicit-final"), None
        )
        stages = current_results(store, candidate_id)
        decision = decide_candidate(
            store.candidate(candidate_id),
            stages,
            explicit_final=explicit.get("decision") if explicit else None,
        )
        decision["candidate_id"] = candidate_id
        decisions.append(decision)
        stage_failures += sum(event.get("status") == "failed" for event in events)
        corrections += sum(event.get("role") == "proposal-revision" for event in events)
        corrections += sum(
            event.get("role") == "explicit-final" and event.get("decision") is None
            for event in events
        )
        completed_roles = Counter(
            str(event.get("role")) for event in events if event.get("status") == "complete"
        )
        stage_roles = {
            "normalize-and-dedupe",
            "indonesian-usage",
            "malaysian-usage",
            "relation-proposal",
            "evidence-audit",
            "independent-verification",
            "adversarial-review",
        }
        corrections += sum(
            max(0, count - 1) for role, count in completed_roles.items() if role in stage_roles
        )
        proposed = stages.get("relation-proposal", {}).get("relation")
        if proposed:
            proposed_relations[proposed] += 1
            outcomes_by_relation.setdefault(proposed, Counter())[decision["outcome"]] += 1
        if stages.get("independent-verification", {}).get("verdict") == "object":
            verifier_objections += 1
        if stages.get("adversarial-review", {}).get("verdict") == "object":
            adversarial_objections += 1
        reason_codes.update(decision["reason_codes"])
        for overlap in stages.get("normalize-and-dedupe", {}).get("overlaps", []):
            duplicates += 1
            duplicate_resolutions[str(overlap.get("resolution", "unresolved"))] += 1
        evidence_failures += sum(
            "evidence" in reason or "source" in reason or "claim" in reason
            for reason in decision["reason_codes"]
        )
    counts = Counter(decision["outcome"] for decision in decisions)
    generated = len(candidate_ids)
    pending = counts["pending"]
    generation_done = any(
        event.get("role") == "generate" and event.get("status") == "complete"
        for event in store.batch_events()
    )
    closed = generation_done and pending == 0
    report = {
        "batch_id": store.batch_id,
        "status": "closed" if closed else "open",
        "generated": generated,
        "accepted": counts["accepted"],
        "held": counts["hold"],
        "rejected": counts["rejected"],
        "pending": pending,
        "relation_distribution": dict(
            sorted(
                Counter(
                    decision["relation"]
                    for decision in decisions
                    if decision["outcome"] == "accepted"
                ).items()
            )
        ),
        "proposed_relation_distribution": dict(sorted(proposed_relations.items())),
        "outcomes_by_relation": {
            relation: dict(sorted(outcomes.items()))
            for relation, outcomes in sorted(outcomes_by_relation.items())
        },
        "reason_code_distribution": dict(sorted(reason_codes.items())),
        "corrections": corrections,
        "duplicate_detections": duplicates,
        "duplicate_resolutions": dict(sorted(duplicate_resolutions.items())),
        "verification_failures": stage_failures + verifier_objections + adversarial_objections,
        "evidence_failures": evidence_failures,
        "further_investigation": [
            decision["candidate_id"]
            for decision in decisions
            if decision["outcome"] in {"pending", "hold"}
        ],
        "decisions": decisions,
        "created_at": utc_now(),
    }
    assert generated == report["accepted"] + report["held"] + report["rejected"] + pending
    atomic_json(store.path / "report.json", report)
    if closed:
        close_manifest(store)
    return report


def report_path(root: Path, batch_id: str) -> Path:
    return root / "curation" / "batches" / batch_id / "report.json"
