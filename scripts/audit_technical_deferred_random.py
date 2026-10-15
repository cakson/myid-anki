#!/usr/bin/env python3
"""Fixed-hash random backstop for deferred prospective preference cards."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from audit_prospective_preference_batch import MODEL, prompt
from compare_historical_verifiers import call_model

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
OUTPUT = SPEC / "technical-borrowing-deferred-random-audit.json"
SEED = "feature003-technical-deferred-random-v1"


def main() -> None:
    if OUTPUT.exists():
        print("existing random audit preserved")
        return
    decisions = json.loads((SPEC / "prospective-preference-50-enriched-state.json").read_text())[
        "candidate_decisions"
    ]
    audited = set(
        json.loads((SPEC / "prospective-preference-50-audit.json").read_text())["results"]
    )
    audited.add("pros4-health-001:health-09")
    pool = [
        ref for ref, row in decisions.items() if row["outcome"] == "accepted" and ref not in audited
    ]
    selected = sorted(pool, key=lambda ref: hashlib.sha256(f"{SEED}|{ref}".encode()).hexdigest())[
        :2
    ]
    reasons = {ref: ["fixed-hash-random-backstop"] for ref in selected}
    started = datetime.now(UTC).isoformat()
    with tempfile.TemporaryDirectory(prefix="myid-technical-random-") as temporary:
        attempt = call_model(
            ROOT,
            Path(temporary),
            "technical-deferred-random",
            MODEL,
            prompt([decisions[ref] for ref in selected], reasons),
        )
    if attempt["status"] != "complete":
        raise RuntimeError(attempt.get("error_summary") or "random audit failed")
    items = attempt["decision"].get("items", [])
    if {item.get("candidate_ref") for item in items} != set(selected):
        raise ValueError("random audit returned the wrong candidates")
    atomic_json(
        OUTPUT,
        {
            "selected_refs": selected,
            "selection_seed": SEED,
            "pool_size": len(pool),
            "model": MODEL,
            "started_at_utc": started,
            "ended_at_utc": datetime.now(UTC).isoformat(),
            "attempt": {
                key: value
                for key, value in attempt.items()
                if key not in {"decision", "response_text"}
            },
            "results": {item["candidate_ref"]: item for item in items},
        },
    )
    print(selected, [item["verdict"] for item in items])


if __name__ == "__main__":
    main()
