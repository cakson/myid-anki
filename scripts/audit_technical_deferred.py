#!/usr/bin/env python3
"""Audit the one previously unaudited card newly selected by revised sampling."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from audit_prospective_preference_batch import MODEL, prompt
from compare_historical_verifiers import call_model

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
REF = "pros4-health-001:health-09"
OUTPUT = SPEC / "technical-borrowing-deferred-audit.json"


def main() -> None:
    if OUTPUT.exists():
        print("existing deferred audit preserved")
        return
    decisions = json.loads((SPEC / "prospective-preference-50-enriched-state.json").read_text())[
        "candidate_decisions"
    ]
    row = decisions[REF]
    reasons = {REF: ["newly-selected-stratified-random-after-technical-flag"]}
    started = datetime.now(UTC).isoformat()
    with tempfile.TemporaryDirectory(prefix="myid-technical-deferred-") as temporary:
        attempt = call_model(
            ROOT, Path(temporary), "technical-deferred-audit", MODEL, prompt([row], reasons)
        )
    if attempt["status"] != "complete":
        raise RuntimeError(attempt.get("error_summary") or "deferred audit failed")
    items = attempt["decision"].get("items", [])
    if len(items) != 1 or items[0].get("candidate_ref") != REF:
        raise ValueError("deferred audit returned the wrong candidate")
    atomic_json(
        OUTPUT,
        {
            "candidate_ref": REF,
            "selection_reason": reasons[REF],
            "model": MODEL,
            "started_at_utc": started,
            "ended_at_utc": datetime.now(UTC).isoformat(),
            "attempt": {
                key: value
                for key, value in attempt.items()
                if key not in {"decision", "response_text"}
            },
            "result": items[0],
        },
    )
    print(REF, items[0]["verdict"])


if __name__ == "__main__":
    main()
