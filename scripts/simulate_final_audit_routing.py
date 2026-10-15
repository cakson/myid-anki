#!/usr/bin/env python3
"""Evaluate general-purpose audit routing against frozen Batch 2 outcomes."""

from __future__ import annotations

import json
from pathlib import Path

from indo_malay_anki.curation.preference_risk import audit_selection, legacy_preference_flags
from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
PREFIX = ROOT / "specs/003-vocabulary-curation"


def main() -> None:
    replay = json.loads((PREFIX / "second-batch-50-policy-replay.json").read_text())
    audit = json.loads((PREFIX / "second-batch-50-audit.json").read_text())
    rows = []
    for ref, record in replay["candidate_results"].items():
        decision = record["replay"]
        verifier = replay["verifier_results"].get(ref, {})
        rows.append(
            {
                "candidate_ref": ref,
                "outcome": decision["outcome"],
                "relation": decision["relation"],
                "confidence_tier": decision.get("confidence_tier"),
                "review_flags": sorted(
                    set(decision.get("review_flags", [])) | legacy_preference_flags(verifier)
                ),
            }
        )
    routes = audit_selection(rows, seed=3003)
    unsafe = {
        ref
        for ref, result in audit["results"].items()
        if result["verdict"] in {"materially-misleading", "should-hold", "should-reject"}
    }
    held = {row["candidate_ref"] for row in rows if row["outcome"] in {"hold", "rejected"}}
    good = {
        ref for ref, result in audit["results"].items() if result["verdict"] == "confirmed-good"
    }
    result = {
        "schema_version": 1,
        "fixed_corpus": "second-batch-50-policy-replay",
        "model_calls": 0,
        "audit_routes": routes,
        "mandatory_route_count": sum(
            not reasons[0].startswith("stratified-sample") for reasons in routes.values()
        ),
        "sample_route_count": sum(
            reasons[0].startswith("stratified-sample") for reasons in routes.values()
        ),
        "known_unsafe_total": len(unsafe),
        "known_unsafe_caught_by_production": sorted(unsafe & held),
        "known_unsafe_routed": {ref: routes[ref] for ref in sorted(unsafe & routes.keys())},
        "known_unsafe_missed": sorted(unsafe - held - routes.keys()),
        "confirmed_good_routed_mandatory": sorted(
            ref
            for ref in good & routes.keys()
            if not routes[ref][0].startswith("stratified-sample")
        ),
        "confirmed_good_routed_total": sorted(good & routes.keys()),
        "confirmed_good_not_routed": sorted(good - routes.keys()),
        "comparison_previous": {"known_unsafe_covered": "6/6", "confirmed_good_routed": "4/24"},
        "legacy_signal_note": (
            "Signals are inferred only from saved v2.2 verifier fields; "
            "no new verifier or audit calls."
        ),
    }
    atomic_json(PREFIX / "final-calibration-batch2-routing.json", result)
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key
                not in {
                    "audit_routes",
                    "known_unsafe_routed",
                    "confirmed_good_routed_mandatory",
                    "confirmed_good_routed_total",
                    "confirmed_good_not_routed",
                }
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
