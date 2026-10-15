#!/usr/bin/env python3
"""Freeze current audit routing and simulate residual random audit budgets."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from audit_prospective_preference_batch import EVIDENCE_FLAGS

from indo_malay_anki.curation.preference_risk import STRONG_AUDIT_FLAGS
from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
DATASET = SPEC / "operational-audit-cohort.json"
RESULT = SPEC / "operational-audit-budget-simulation.json"
SEED = 3003001
REPETITIONS = 4096
RATES = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
CRITICAL = {"materially-misleading", "unsafe-unresolved", "should-hold", "should-reject"}
BATCHES = {
    "fresh1": (
        "fresh-batch-50-state.json",
        ("fresh-batch-50-audit.json", "fresh-batch-50-audit-completion.json"),
    ),
    "fresh2": ("second-batch-50-state.json", ("second-batch-50-audit.json",)),
    "fresh3": (
        "final-calibration-50-state.json",
        (
            "final-calibration-50-audit.json",
            "final-calibration-localized-standard-audit.json",
            "final-calibration-router-supplement-audit.json",
        ),
    ),
    "prospective50": (
        "prospective-preference-50-enriched-state.json",
        (
            "prospective-preference-50-audit.json",
            "technical-borrowing-deferred-audit.json",
            "technical-borrowing-deferred-random-audit.json",
        ),
    ),
    "technical25": (
        "technical-borrowing-25-enriched-state.json",
        ("technical-borrowing-25-audit.json",),
    ),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deterministic_reasons(row: dict) -> list[str]:
    """Frozen deterministic branch of audit_prospective_preference_batch.select."""
    if row["outcome"] != "accepted":
        return []
    reasons = []
    if row["relation"] == "false-friend":
        reasons.append("false-friend")
    if row.get("confidence_tier") in {"low", "very-low"}:
        reasons.append(f"confidence:{row['confidence_tier']}")
    flags = set(row.get("review_flags", []))
    reasons.extend(f"flag:{flag}" for flag in sorted(flags & STRONG_AUDIT_FLAGS))
    reasons.extend(f"evidence:{flag}" for flag in sorted(flags & EVIDENCE_FLAGS))
    if "technical-borrowing-risk" in flags:
        reasons.append("flag:technical-borrowing-risk")
    return reasons


def audit_items(path: Path) -> dict:
    artifact = json.loads(path.read_text())
    if "results" in artifact:
        return artifact["results"]
    if "result" in artifact and "candidate_ref" in artifact:
        return {artifact["candidate_ref"]: artifact["result"]}
    raise ValueError(f"unrecognized audit artifact: {path}")


def build_dataset() -> dict:
    if DATASET.exists():
        saved = json.loads(DATASET.read_text())
        for filename, expected in saved["source_digests"].items():
            if sha(SPEC / filename) != expected:
                raise ValueError(f"frozen source changed: {filename}")
        return saved
    records = {}
    digests = {}
    for batch, (state_name, audit_names) in BATCHES.items():
        state_path = SPEC / state_name
        state = json.loads(state_path.read_text())
        digests[state_name] = sha(state_path)
        audits = {}
        for name in audit_names:
            path = SPEC / name
            digests[name] = sha(path)
            for ref, item in audit_items(path).items():
                if ref in audits:
                    raise ValueError(f"duplicate independent audit label: {ref}")
                audits[ref] = item
        accepted = {
            ref: row
            for ref, row in state["candidate_decisions"].items()
            if row["outcome"] == "accepted"
        }
        if not set(audits) <= set(accepted):
            raise ValueError(f"audit outside production ACCEPT set: {batch}")
        for ref, row in accepted.items():
            audit = audits.get(ref)
            verdict = audit["verdict"] if audit else None
            if verdict and verdict not in CRITICAL | {"minor-correction", "confirmed-good"}:
                raise ValueError(f"unknown audit verdict: {ref}")
            verifier = row.get("verifier") or {}
            records[ref] = {
                "candidate_ref": ref,
                "batch": batch,
                "production_features": {
                    "relation": row["relation"],
                    "confidence_tier": row.get("confidence_tier"),
                    "review_flags": row.get("review_flags", []),
                    "preference_risk": verifier.get("preference_risk"),
                    "verifier_verdict": verifier.get("verdict"),
                    "verifier_concerns": verifier.get("concerns", []),
                    "verifier_material_concerns": verifier.get("material_concerns", []),
                    "risk_path": (row.get("risk") or {}).get("path"),
                    "evidence_source_types": sorted(
                        {
                            source["source_type"]
                            for source in (row.get("preference_evidence") or {}).get("sources", [])
                        }
                    ),
                },
                "deterministic_reasons": deterministic_reasons(row),
                "audit_label": verdict,
                "audit_category": (
                    "critical"
                    if verdict in CRITICAL or (audit or {}).get("material_false_positive")
                    else "correctable"
                    if verdict == "minor-correction"
                    else "confirmed-good"
                    if verdict == "confirmed-good"
                    else None
                ),
            }
    result = {
        "schema_version": 1,
        "router_snapshot": (
            "audit_prospective_preference_batch.select deterministic branch, 2026-10-15"
        ),
        "production_policy": "3.1.0",
        "source_digests": digests,
        "records": dict(sorted(records.items())),
        "label_limitation": "Unaudited ACCEPTs remain unlabeled, not presumed safe.",
    }
    atomic_json(DATASET, result)
    return result


def choose(pool: list[dict], count: int, rng: random.Random, mode: str) -> set[str]:
    if not count or not pool:
        return set()
    if mode == "uniform":
        return {row["candidate_ref"] for row in rng.sample(pool, min(count, len(pool)))}
    if mode != "stratified":
        raise ValueError(mode)
    # Half the slots stay genuinely uniform among every otherwise-clean card.
    uniform_count = math.ceil(count / 2)
    chosen = {row["candidate_ref"] for row in rng.sample(pool, uniform_count)}
    remaining = [row for row in pool if row["candidate_ref"] not in chosen]
    weighted_count = min(count - len(chosen), len(remaining))

    # Fixed, explainable weights; no learned score or audit-label-dependent threshold.
    def weight(row: dict) -> float:
        features = row["production_features"]
        relation_weight = 2.0 if features["relation"] == "different-common-word" else 1.0
        confidence_weight = 1.5 if features["confidence_tier"] == "medium" else 1.0
        return relation_weight * confidence_weight

    ranked = sorted(
        remaining,
        key=lambda row: -math.log(max(rng.random(), 1e-12)) / weight(row),
    )
    chosen.update(row["candidate_ref"] for row in ranked[:weighted_count])
    return chosen


def simulate(rows: list[dict], rate: float, mode: str, *, by_batch: bool) -> dict:
    deterministic = {row["candidate_ref"] for row in rows if row["deterministic_reasons"]}
    critical = {row["candidate_ref"] for row in rows if row["audit_category"] == "critical"}
    good = {row["candidate_ref"] for row in rows if row["audit_category"] == "confirmed-good"}
    pools = defaultdict(list)
    for row in rows:
        if row["candidate_ref"] not in deterministic:
            key = row["batch"] if by_batch else "pooled"
            pools[key].append(row)
    sample_count = sum(math.ceil(rate * len(pool)) for pool in pools.values())
    coverage = []
    good_audited = []
    all_caught = 0
    for repetition in range(REPETITIONS):
        sampled = set()
        for group, pool in sorted(pools.items()):
            seed_text = f"{SEED}|{mode}|{rate}|{repetition}|{group}"
            seed = int.from_bytes(hashlib.sha256(seed_text.encode()).digest()[:8], "big")
            sampled |= choose(pool, math.ceil(rate * len(pool)), random.Random(seed), mode)
        selected = deterministic | sampled
        caught = len(critical & selected)
        coverage.append(caught)
        good_audited.append(len(good & selected))
        all_caught += caught == len(critical)
    return {
        "accepts": len(rows),
        "labeled": sum(row["audit_label"] is not None for row in rows),
        "known_critical": len(critical),
        "deterministic_audits": len(deterministic),
        "known_critical_deterministic": len(critical & deterministic),
        "known_critical_residual": len(critical - deterministic),
        "residual_pool": sum(len(pool) for pool in pools.values()),
        "random_audits": sample_count,
        "total_audits": len(deterministic) + sample_count,
        "total_audit_fraction": round((len(deterministic) + sample_count) / len(rows), 4),
        "audit_count_per_100_accepts": round(
            100 * (len(deterministic) + sample_count) / len(rows), 1
        ),
        "mean_critical_caught": round(sum(coverage) / REPETITIONS, 3),
        "mean_critical_coverage": round(sum(coverage) / (REPETITIONS * len(critical)), 4)
        if critical
        else None,
        "worst_observed_critical_caught": min(coverage),
        "best_observed_critical_caught": max(coverage),
        "fraction_all_known_critical_caught": round(all_caught / REPETITIONS, 4),
        "fraction_at_least_one_known_critical_missed": round(1 - all_caught / REPETITIONS, 4),
        "mean_confirmed_good_audited": round(sum(good_audited) / REPETITIONS, 2),
        "worst_observed_confirmed_good_audited": max(good_audited),
    }


def main() -> None:
    dataset = build_dataset()
    records = list(dataset["records"].values())
    result = {
        "schema_version": 1,
        "dataset_digest": sha(DATASET),
        "router_snapshot": dataset["router_snapshot"],
        "seed": SEED,
        "repetitions": REPETITIONS,
        "rates": RATES,
        "selection": {
            "pure_random": "uniform without replacement among otherwise-clean ACCEPTs",
            "stratified": (
                "half uniform; remaining weighted 2x different-common-word and "
                "1.5x medium confidence; no audit labels in selection"
            ),
        },
        "pooled": {},
        "batchwise_pooled": {},
        "per_batch": {},
        "leave_one_batch_out": {},
    }
    for batch in BATCHES:
        batch_rows = [row for row in records if row["batch"] == batch]
        result["per_batch"][batch] = {}
        for mode in ("uniform", "stratified"):
            result["per_batch"][batch][mode] = {
                str(rate): simulate(batch_rows, rate, mode, by_batch=False) for rate in RATES
            }
    for mode in ("uniform", "stratified"):
        result["pooled"][mode] = {
            str(rate): simulate(records, rate, mode, by_batch=False) for rate in RATES
        }
        result["batchwise_pooled"][mode] = {
            str(rate): simulate(records, rate, mode, by_batch=True) for rate in RATES
        }
    # The router and weights are fixed; no threshold is fit on the other four batches.
    # These train/held-out summaries expose stability rather than claiming blind validation.
    for held_out in BATCHES:
        training = [row for row in records if row["batch"] != held_out]
        result["leave_one_batch_out"][held_out] = {}
        for mode in ("uniform", "stratified"):
            result["leave_one_batch_out"][held_out][mode] = {
                str(rate): {
                    "training": simulate(training, rate, mode, by_batch=True),
                    "held_out": result["per_batch"][held_out][mode][str(rate)],
                }
                for rate in RATES
            }
    atomic_json(RESULT, result)
    counts = Counter(row["audit_category"] for row in records)
    print("records", len(records), "labels", dict(counts))
    for mode in ("uniform", "stratified"):
        for rate in RATES:
            metric = result["batchwise_pooled"][mode][str(rate)]
            print(mode, rate, metric["total_audit_fraction"], metric["mean_critical_caught"])


if __name__ == "__main__":
    main()
