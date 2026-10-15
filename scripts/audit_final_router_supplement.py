#!/usr/bin/env python3
"""Audit previously unreviewed final-batch cards selected by risk-first routing."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from audit_final_calibration_batch import MODEL, prompt
from compare_historical_verifiers import call_model

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
OUTPUT = SPEC / "final-calibration-router-supplement-audit.json"
VALID = {
    "confirmed-good",
    "minor-correction",
    "materially-misleading",
    "should-hold",
    "should-reject",
}


def main() -> None:
    calibration = json.loads((SPEC / "audit-router-calibration.json").read_text())
    policy = calibration["per_batch_fixed_policy_evaluation"]["batch3"]["C-risk-first"]
    production = json.loads((SPEC / "final-calibration-50-state.json").read_text())
    previous = json.loads((SPEC / "final-calibration-50-audit.json").read_text())
    selected = set(policy["deterministic_reasons"]) | set(policy["random_refs"])
    refs = sorted(selected - set(previous["results"]))
    rows = [production["candidate_decisions"][ref] for ref in refs]
    if any(row["outcome"] != "accepted" for row in rows):
        raise ValueError("router selected a non-accept")
    reasons = {
        ref: policy["deterministic_reasons"].get(ref, ["stratified-sample:risk-first"])
        for ref in refs
    }
    artifact = (
        json.loads(OUTPUT.read_text())
        if OUTPUT.exists()
        else {
            "schema_version": 1,
            "model": MODEL,
            "routing_policy": "C-risk-first, frozen hash sampling",
            "selected_refs": refs,
            "selection_reasons": reasons,
            "started_at_utc": datetime.now(UTC).isoformat(),
            "attempts": [],
            "results": {},
        }
    )
    if artifact["selected_refs"] != refs:
        raise ValueError("supplemental audit cohort changed")
    pending = [row for row in rows if row["candidate_ref"] not in artifact["results"]]
    if pending:
        with tempfile.TemporaryDirectory(prefix="myid-router-supplement-") as tmp:
            attempt = call_model(
                ROOT, Path(tmp), "final-router-supplement", MODEL, prompt(pending, reasons)
            )
        artifact["attempts"].append(
            {
                key: value
                for key, value in attempt.items()
                if key not in {"decision", "response_text"}
            }
        )
        atomic_json(OUTPUT, artifact)
        if attempt["status"] != "complete":
            raise RuntimeError(attempt.get("error_summary") or "supplemental audit failed")
        items = attempt["decision"].get("items", [])
        indexed = {item.get("candidate_ref"): item for item in items if isinstance(item, dict)}
        if set(indexed) != {row["candidate_ref"] for row in pending}:
            raise ValueError("supplemental audit response does not match selected refs")
        for ref, item in indexed.items():
            if item.get("verdict") not in VALID:
                raise ValueError(f"invalid supplemental verdict: {ref}")
            artifact["results"][ref] = item
    artifact["ended_at_utc"] = datetime.now(UTC).isoformat()
    atomic_json(OUTPUT, artifact)
    print({ref: result["verdict"] for ref, result in artifact["results"].items()})


if __name__ == "__main__":
    main()
