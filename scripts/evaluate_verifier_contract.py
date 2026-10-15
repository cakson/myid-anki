#!/usr/bin/env python3
"""Evaluate frozen verifier outputs against separately stored independent audits."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from indo_malay_anki.curation.store import atomic_json

SPEC = Path("specs/003-vocabulary-curation")
INPUTS = SPEC / "verifier-contract-benchmark-inputs.json"
LABELS = SPEC / "verifier-contract-benchmark-labels.json"
RESULTS = SPEC / "verifier-contract-benchmark-results.json"
OUTPUT = SPEC / "verifier-contract-benchmark-evaluation.json"
BASELINE_STATES = (
    "second-batch-50-state.json",
    "final-calibration-50-state.json",
    "prospective-preference-50-state.json",
    "technical-borrowing-25-state.json",
)


def random_refs(refs: list[str], fraction: float) -> set[str]:
    count = math.ceil(len(refs) * fraction)
    ranked = sorted(
        refs,
        key=lambda ref: hashlib.sha256(
            f"feature003-verifier-benchmark-v1|{ref}".encode()
        ).hexdigest(),
    )
    return set(ranked[:count])


def score(labels: dict, decisions: dict, variant: str, subset: set[str] | None = None) -> dict:
    refs = sorted(set(labels) if subset is None else subset)
    actions = {ref: decisions[ref]["action"] for ref in refs}
    critical = {ref for ref in refs if labels[ref]["critical"]}
    good = {ref for ref in refs if labels[ref]["audit_verdict"] == "confirmed-good"}
    minor = {ref for ref in refs if labels[ref]["audit_verdict"] == "minor-correction"}
    result = {
        "candidates": len(refs),
        "critical": len(critical),
        "confirmed_good": len(good),
        "minor_correction": len(minor),
        "actions": dict(Counter(actions.values())),
        "critical_ordinary_accept": sorted(ref for ref in critical if actions[ref] == "ACCEPT"),
        "critical_review": sorted(ref for ref in critical if actions[ref] == "ACCEPT_WITH_REVIEW"),
        "critical_hold_or_reject": sorted(
            ref for ref in critical if actions[ref] in {"HOLD", "REJECT"}
        ),
        "good_false_escalation": sorted(ref for ref in good if actions[ref] != "ACCEPT"),
        "good_false_block": sorted(ref for ref in good if actions[ref] in {"HOLD", "REJECT"}),
        "minor_challenged": sorted(ref for ref in minor if actions[ref] != "ACCEPT"),
    }
    for fraction in (0, 0.10, 0.15, 0.20):
        ordinary = [ref for ref in refs if actions[ref] == "ACCEPT"]
        sampled = random_refs(ordinary, fraction)
        routed = {ref for ref in refs if actions[ref] == "ACCEPT_WITH_REVIEW"}
        caught = {
            ref
            for ref in critical
            if actions[ref] in {"HOLD", "REJECT"} or ref in routed or ref in sampled
        }
        result[f"routing_{fraction:.2f}"] = {
            "audited": len(routed | sampled),
            "audit_fraction": round(len(routed | sampled) / len(refs), 4) if refs else None,
            "review_audits": len(routed),
            "random_audits": len(sampled),
            "critical_caught": len(caught),
            "critical_missed": sorted(critical - caught),
            "confirmed_good_audited": len(good & (routed | sampled)),
        }
    return result


def costs(attempts: list[dict], variant: str, candidate_count: int) -> dict:
    selected = [item for item in attempts if item["variant"] == variant]
    tokens_known = all(
        item.get("input_tokens") is not None and item.get("output_tokens") is not None
        for item in selected
    )
    input_tokens = sum(item.get("input_tokens") or 0 for item in selected) if tokens_known else None
    output_tokens = (
        sum(item.get("output_tokens") or 0 for item in selected) if tokens_known else None
    )
    return {
        "calls": len(selected),
        "failed_calls": sum(item["status"] != "complete" for item in selected),
        "elapsed_model_seconds": round(sum(item["elapsed_seconds"] for item in selected), 3),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tokens_per_candidate": round((input_tokens + output_tokens) / candidate_count, 1)
        if input_tokens is not None and output_tokens is not None
        else None,
        "money_cost": None,
        "money_cost_reason": "No provider price or billed cost is configured for these CLI calls.",
    }


def archived_baseline_cost_reference() -> dict:
    """Amortized reference, since group calls cannot be isolated to selected cards."""
    candidate_count = 0
    attempts = []
    for filename in BASELINE_STATES:
        state = json.loads((SPEC / filename).read_text())
        candidate_count += len(state["candidate_decisions"])
        attempts.extend(
            item
            for item in state["operation_attempts"]
            if item.get("role") == "independent-verification"
        )
    return {
        "source_cohort_candidates": candidate_count,
        "source_cohort_calls": len(attempts),
        "source_cohort_elapsed_model_seconds": round(
            sum(item["elapsed_seconds"] for item in attempts), 3
        ),
        "source_cohort_input_tokens_recorded": sum(
            item.get("input_tokens") or 0 for item in attempts
        ),
        "source_cohort_output_tokens_recorded": sum(
            item.get("output_tokens") or 0 for item in attempts
        ),
        "calls_with_unavailable_tokens": sum(item.get("input_tokens") is None for item in attempts),
        "scope_note": (
            "Four historical cohorts; first fresh batch lacks role-tagged verifier attempts. "
            "Grouped calls include unselected cards and cannot be attributed exactly to the 48."
        ),
        "money_cost": None,
    }


def main() -> None:
    inputs = json.loads(INPUTS.read_text())
    labels_artifact = json.loads(LABELS.read_text())
    results = json.loads(RESULTS.read_text())
    digest = hashlib.sha256(INPUTS.read_bytes()).hexdigest()
    if labels_artifact["input_digest"] != digest or results["input_digest"] != digest:
        raise ValueError("input-label-result digest mismatch")
    labels = labels_artifact["labels"]
    refs = {item["candidate_ref"] for item in inputs["items"]}
    if refs != set(labels):
        raise ValueError("frozen input and label candidate sets differ")
    variants = {
        "A_v3_1_saved_luna": {ref: {"action": "ACCEPT"} for ref in refs},
        **results["results"],
    }
    if any(set(decisions) != refs for decisions in variants.values()):
        raise ValueError("a variant is incomplete")
    report = {
        "schema_version": 1,
        "candidate_count": len(refs),
        "critical_count": sum(item["critical"] for item in labels.values()),
        "label_distribution": dict(Counter(item["audit_verdict"] for item in labels.values())),
        "input_digest": digest,
        "prompt_digest": results["prompt_digest"],
        "archived_baseline_cost_reference": archived_baseline_cost_reference(),
        "variants": {},
        "batch_separated": {},
        "limitations": [
            "The benchmark deliberately includes every known unsafe historical ACCEPT; "
            "its risk prevalence is not a population estimate.",
            "Variant A reuses archived Luna production decisions and incurs no new benchmark "
            "call. Its historical prompts and batching differ from variants B/C.",
            "The revised contract was specified after the failure classes were known; "
            "batch-separated results are descriptive validation, not a blind prospective trial.",
            "Random sample outcomes depend on the fixed hash seed and this small enriched set.",
        ],
    }
    for name, decisions in variants.items():
        report["variants"][name] = score(labels, decisions, name)
        report["variants"][name]["cost"] = (
            None if name.startswith("A_") else costs(results["attempts"], name, len(refs))
        )
        report["batch_separated"][name] = {}
        for batch in sorted({item["batch"] for item in labels.values()}):
            subset = {ref for ref in refs if labels[ref]["batch"] == batch}
            report["batch_separated"][name][batch] = score(labels, decisions, name, subset)
    # Candidate-level outcomes support inspection of misses without changing prompts.
    report["candidate_results"] = {
        ref: {
            "audit_verdict": labels[ref]["audit_verdict"],
            "batch": labels[ref]["batch"],
            "actions": {name: decisions[ref]["action"] for name, decisions in variants.items()},
            "objections": {
                name: decisions[ref].get("concrete_objection")
                for name, decisions in variants.items()
                if not name.startswith("A_")
            },
        }
        for ref in sorted(refs)
    }
    atomic_json(OUTPUT, report)
    for name, data in report["variants"].items():
        print(
            name,
            "critical ordinary accepts",
            len(data["critical_ordinary_accept"]),
            "good false escalations",
            len(data["good_false_escalation"]),
            "actions",
            data["actions"],
        )


if __name__ == "__main__":
    main()
