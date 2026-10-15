#!/usr/bin/env python3
"""Compare frozen cheap-screen outputs with independent historical audit labels."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
INPUTS = SPEC / "cheap-audit-screen-inputs.json"
LABELS = SPEC / "cheap-audit-screen-labels.json"
RESULT = SPEC / "cheap-audit-screen-evaluation.json"
SIZES = (5, 10, 20)
RATES = (0.05, 0.10, 0.15, 0.20)
REPETITIONS = 4096
SEED = 3003002


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screen_summary(labels: dict, decisions: dict) -> dict:
    summary = {}
    for batch in sorted({label["batch"] for label in labels.values()} | {"pooled"}):
        refs = [ref for ref in labels if batch == "pooled" or labels[ref]["batch"] == batch]
        by_category = defaultdict(Counter)
        for ref in refs:
            by_category[labels[ref]["category"]][decisions[ref]["decision"]] += 1
        summary[batch] = {
            category: dict(counts) for category, counts in sorted(by_category.items())
        }
    return summary


def simulate(labels: dict, screen: dict | None, architecture: str, rate: float) -> dict:
    if architecture == "A":
        deterministic = {ref for ref, label in labels.items() if label["deterministic_reasons"]}
    elif architecture == "B":
        deterministic = {ref for ref, item in screen.items() if item["decision"] == "screen-review"}
    elif architecture == "C":
        deterministic = {ref for ref, label in labels.items() if label["deterministic_reasons"]}
        deterministic |= {
            ref for ref, item in screen.items() if item["decision"] == "screen-review"
        }
    else:
        raise ValueError(architecture)
    critical = {ref for ref, label in labels.items() if label["category"] == "critical"}
    good = {ref for ref, label in labels.items() if label["category"] == "confirmed-good"}
    pools = defaultdict(list)
    for ref, label in labels.items():
        if ref not in deterministic:
            pools[label["batch"]].append(ref)
    random_count = sum(math.ceil(rate * len(pool)) for pool in pools.values())
    coverage, residual_coverage, good_counts = [], [], []
    residual_critical = critical - deterministic
    all_caught = 0
    for repetition in range(REPETITIONS):
        selected = set(deterministic)
        for batch, pool in sorted(pools.items()):
            seed = hashlib.sha256(
                f"{SEED}|{architecture}|{rate}|{repetition}|{batch}".encode()
            ).digest()
            rng = random.Random(int.from_bytes(seed[:8], "big"))
            selected.update(rng.sample(pool, math.ceil(rate * len(pool))))
        caught = len(selected & critical)
        coverage.append(caught)
        residual_coverage.append(len(selected & residual_critical))
        good_counts.append(len(selected & good))
        all_caught += caught == len(critical)
    return {
        "accepts": len(labels),
        "deterministic_deep_audits": len(deterministic),
        "random_deep_audits": random_count,
        "total_deep_audits": len(deterministic) + random_count,
        "deep_audit_fraction": round((len(deterministic) + random_count) / len(labels), 4),
        "critical_deterministic": len(critical & deterministic),
        "critical_residual": len(residual_critical),
        "mean_critical_caught": round(sum(coverage) / REPETITIONS, 3),
        "worst_critical_caught": min(coverage),
        "all_known_critical_caught_fraction": round(all_caught / REPETITIONS, 4),
        "mean_residual_critical_caught": round(sum(residual_coverage) / REPETITIONS, 3),
        "mean_confirmed_good_deep_audited": round(sum(good_counts) / REPETITIONS, 2),
    }


def main() -> None:
    labels_artifact = json.loads(LABELS.read_text())
    if labels_artifact["input_digest"] != digest(INPUTS):
        raise ValueError("frozen input digest mismatch")
    labels = labels_artifact["labels"]
    output = {
        "schema_version": 1,
        "input_digest": digest(INPUTS),
        "labels_digest": digest(LABELS),
        "seed": SEED,
        "repetitions": REPETITIONS,
        "rates": RATES,
        "screens": {},
        "architecture_A": {},
    }
    for rate in RATES:
        output["architecture_A"][str(rate)] = simulate(labels, None, "A", rate)
    for size in SIZES:
        artifact_path = SPEC / f"cheap-audit-screen-{size}-results.json"
        artifact = json.loads(artifact_path.read_text())
        if artifact["input_digest"] != digest(INPUTS):
            raise ValueError(f"screen input changed for size {size}")
        decisions = artifact["results"]
        if set(decisions) != set(labels):
            raise ValueError(f"incomplete screen size {size}")
        attempts = artifact["attempts"]
        output["screens"][str(size)] = {
            "artifact_digest": digest(artifact_path),
            "by_batch": screen_summary(labels, decisions),
            "review_count": sum(x["decision"] == "screen-review" for x in decisions.values()),
            "model_calls": len(attempts),
            "elapsed_model_call_seconds": round(
                sum(x.get("elapsed_seconds") or 0 for x in attempts), 3
            ),
            "input_tokens": sum(x.get("input_tokens") or 0 for x in attempts),
            "output_tokens": sum(x.get("output_tokens") or 0 for x in attempts),
            "missing_usage_calls": sum(
                x.get("input_tokens") is None or x.get("output_tokens") is None for x in attempts
            ),
            "architectures": {
                architecture: {
                    str(rate): simulate(labels, decisions, architecture, rate) for rate in RATES
                }
                for architecture in ("B", "C")
            },
            "residual_cases": {
                ref: {
                    "screen": decisions[ref],
                    "deterministic_reasons": labels[ref]["deterministic_reasons"],
                    "audit_verdict": labels[ref]["verdict"],
                }
                for ref in labels
                if labels[ref]["category"] == "critical"
                and not labels[ref]["deterministic_reasons"]
            },
        }
    atomic_json(RESULT, output)
    for size in SIZES:
        row = output["screens"][str(size)]
        print(
            size,
            "calls",
            row["model_calls"],
            "review",
            row["review_count"],
            "critical",
            row["by_batch"]["pooled"]["critical"],
        )


if __name__ == "__main__":
    main()
