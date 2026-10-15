#!/usr/bin/env python3
"""Independently audit deferred cards newly selected by localized-standard routing."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from audit_final_calibration_batch import MODEL, prompt
from compare_historical_verifiers import call_model

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
SIMULATION = SPEC / "localized-standard-audit-simulation.json"
OUTPUT = SPEC / "final-calibration-localized-standard-audit.json"
VALID = {
    "confirmed-good",
    "minor-correction",
    "materially-misleading",
    "should-hold",
    "should-reject",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    simulation = json.loads(SIMULATION.read_text())
    chosen = simulation["by_batch"]["batch3"]["after_D"]
    selected = set(chosen["deterministic_reasons"]) | set(chosen["random_refs"])
    original = json.loads((SPEC / "final-calibration-50-audit.json").read_text())
    prior = json.loads((SPEC / "final-calibration-router-supplement-audit.json").read_text())
    old = set(original["results"]) | set(prior["results"])
    refs = sorted(selected - old)
    production_path = SPEC / "final-calibration-50-state.json"
    production = json.loads(production_path.read_text())
    rows = [production["candidate_decisions"][ref] for ref in refs]
    reasons = {
        ref: chosen["deterministic_reasons"].get(ref, ["stratified-random-sample"]) for ref in refs
    }
    if any(row["outcome"] != "accepted" for row in rows):
        raise ValueError("non-accepted candidate selected")
    artifact = (
        json.loads(OUTPUT.read_text())
        if OUTPUT.exists()
        else {
            "schema_version": 1,
            "model": MODEL,
            "simulation_digest": digest(SIMULATION),
            "production_digest": digest(production_path),
            "selection_policy": "D-localized-standard-risk, frozen v1 hash sample",
            "selected_refs": refs,
            "selection_reasons": reasons,
            "started_at_utc": datetime.now(UTC).isoformat(),
            "attempts": [],
            "results": {},
        }
    )
    if artifact["selected_refs"] != refs or artifact["simulation_digest"] != digest(SIMULATION):
        raise ValueError("frozen audit selection changed")
    pending = [row for row in rows if row["candidate_ref"] not in artifact["results"]]
    if pending:
        with tempfile.TemporaryDirectory(prefix="myid-localized-audit-") as temp:
            attempt = call_model(
                ROOT, Path(temp), "localized-standard-audit", MODEL, prompt(pending, reasons)
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
            raise RuntimeError(attempt.get("error_summary") or "localized-standard audit failed")
        items = attempt["decision"].get("items", [])
        indexed = {item.get("candidate_ref"): item for item in items if isinstance(item, dict)}
        if set(indexed) != {row["candidate_ref"] for row in pending}:
            raise ValueError("audit result refs differ from frozen selection")
        for ref, item in indexed.items():
            if item.get("verdict") not in VALID:
                raise ValueError(f"invalid audit verdict: {ref}")
            artifact["results"][ref] = item
    artifact["ended_at_utc"] = datetime.now(UTC).isoformat()
    atomic_json(OUTPUT, artifact)
    print({ref: item["verdict"] for ref, item in artifact["results"].items()})


if __name__ == "__main__":
    main()
