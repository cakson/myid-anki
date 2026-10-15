#!/usr/bin/env python3
"""Evaluate a lexical IT borrowing signal on frozen, independently audited batches."""

from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path

from audit_prospective_preference_batch import select

from indo_malay_anki.curation.preference_evidence import preference_trigger
from indo_malay_anki.curation.store import atomic_json
from indo_malay_anki.curation.technical_borrowing_risk import technical_borrowing_risk

SPEC = Path.cwd() / "specs/003-vocabulary-curation"
OUT = SPEC / "technical-borrowing-retrospective.json"
BATCHES = {
    "batch1": (
        "fresh-batch-50-state.json",
        ["fresh-batch-50-audit.json", "fresh-batch-50-audit-completion.json"],
    ),
    "batch2": ("second-batch-50-state.json", ["second-batch-50-audit.json"]),
    "batch3": (
        "final-calibration-50-state.json",
        [
            "final-calibration-50-audit.json",
            "final-calibration-router-supplement-audit.json",
            "final-calibration-localized-standard-audit.json",
        ],
    ),
    "prospective50": (
        "prospective-preference-50-enriched-state.json",
        ["prospective-preference-50-audit.json"],
    ),
}
CRITICAL = {"materially-misleading", "should-hold", "should-reject"}


def load_audits(names: list[str]) -> dict:
    results = {}
    for name in names:
        for ref, row in json.loads((SPEC / name).read_text())["results"].items():
            if ref in results:
                raise ValueError(f"duplicate audit: {ref}")
            results[ref] = row
    return results


def main() -> None:
    records = {}
    batch_metrics = {}
    for batch, (state_name, audit_names) in BATCHES.items():
        decisions = json.loads((SPEC / state_name).read_text())["candidate_decisions"]
        audits = load_audits(audit_names)
        before = select(decisions)
        revised = copy.deepcopy(decisions)
        for row in revised.values():
            if technical_borrowing_risk(row)["triggered"]:
                row.setdefault("review_flags", []).append("technical-borrowing-risk")
        # select() is the current router. Simulate the new flag without changing
        # the production gate or editing frozen decision artifacts.
        after = select(revised)
        batch_metrics[batch] = {
            "accepts": sum(row["outcome"] == "accepted" for row in decisions.values()),
            "audited_labels": len(audits),
            "router_before": len(before),
            "router_after": len(after),
            "newly_routed": sorted(set(after) - set(before)),
        }
        for ref, row in decisions.items():
            if row["outcome"] != "accepted":
                continue
            tech = technical_borrowing_risk(row)
            existing = preference_trigger(row, include_technical=False)
            audit = audits.get(ref)
            records[ref] = {
                "batch": batch,
                "candidate": row["candidate"],
                "relation": row["relation"],
                "technical_trigger": tech,
                "existing_preference_reasons": existing,
                "audit_verdict": audit["verdict"] if audit else None,
                "critical_audit_label": audit["verdict"] in CRITICAL if audit else None,
                "router_before": before.get(ref),
                "router_after": after.get(ref),
            }
    labels = [record for record in records.values() if record["audit_verdict"]]
    tech = [record for record in records.values() if record["technical_trigger"]["triggered"]]
    result = {
        "schema_version": 1,
        "policy": "candidate-lexical-only; no AI call; audit/evidence routing only",
        "accepted_count": len(records),
        "independently_audited_count": len(labels),
        "technical_trigger_count": len(tech),
        "technical_trigger_audited_count": sum(bool(r["audit_verdict"]) for r in tech),
        "technical_trigger_critical_count": sum(r["critical_audit_label"] is True for r in tech),
        "technical_trigger_confirmed_good_count": sum(
            r["audit_verdict"] == "confirmed-good" for r in tech
        ),
        "technical_trigger_correctable_count": sum(
            r["audit_verdict"] == "minor-correction" for r in tech
        ),
        "existing_and_technical": sum(bool(r["existing_preference_reasons"]) for r in tech),
        "technical_only": sum(not r["existing_preference_reasons"] for r in tech),
        "existing_only": sum(
            bool(r["existing_preference_reasons"]) and not r["technical_trigger"]["triggered"]
            for r in records.values()
        ),
        "neither": sum(
            not r["existing_preference_reasons"] and not r["technical_trigger"]["triggered"]
            for r in records.values()
        ),
        "audit_verdicts_by_trigger": dict(Counter(r["audit_verdict"] or "unaudited" for r in tech)),
        "batch_metrics": batch_metrics,
        "records": records,
    }
    atomic_json(OUT, result)
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
