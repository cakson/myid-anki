#!/usr/bin/env python3
"""Simulate a production-time localized-standard audit signal on saved batches."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from calibrate_feature003_audit import BATCHES, evaluate, load_cohort, sampled_refs

from indo_malay_anki.curation.localized_standard_risk import classify_localized_standard_risk
from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
OUTPUT = SPEC / "localized-standard-audit-simulation.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revised_routing(records: list[dict]) -> dict:
    before = evaluate(records, "C-risk-first")
    deterministic = {ref: list(reasons) for ref, reasons in before["deterministic_reasons"].items()}
    new_deterministic = set()
    for row in records:
        risk = row["localized_standard_risk"]
        if risk["level"] != "none":
            ref = row["candidate_ref"]
            if ref not in deterministic:
                new_deterministic.add(ref)
            deterministic.setdefault(ref, []).append(
                f"localized-standard-vs-borrowed:{risk['level']}"
            )
    random = sampled_refs(records, deterministic, "D-localized-standard-risk")
    selected = set(deterministic) | random
    observed = {row["candidate_ref"]: row for row in records if row["audit_observed"]}
    critical = {ref for ref, row in observed.items() if row["audit_label"] == "critical"}
    good = {ref for ref, row in observed.items() if row["audit_label"] == "confirmed-safe"}
    return {
        "accept_count": len(records),
        "audit_count": len(selected),
        "audit_percent": round(100 * len(selected) / len(records), 2),
        "deterministic_count": len(deterministic),
        "random_count": len(random),
        "new_deterministic_refs": sorted(new_deterministic),
        "deterministic_reasons": deterministic,
        "random_refs": sorted(random),
        "known_critical_total": len(critical),
        "critical_deterministic": len(critical & deterministic.keys()),
        "critical_random_only": len((critical & random) - deterministic.keys()),
        "critical_missed": sorted(critical - selected),
        "confirmed_good_audited": len(good & selected),
        "newly_selected_known_critical": sorted(
            (selected - (set(before["deterministic_reasons"]) | set(before["random_refs"])))
            & critical
        ),
        "newly_selected_confirmed_good": sorted(
            (selected - (set(before["deterministic_reasons"]) | set(before["random_refs"]))) & good
        ),
        "newly_selected_unlabeled": sorted(
            (selected - (set(before["deterministic_reasons"]) | set(before["random_refs"])))
            - set(observed)
        ),
    }


def main() -> None:
    records, input_sha = load_cohort()
    source_counts = Counter()
    for row in records:
        batch_id, candidate_id = row["candidate_ref"].split(":", 1)
        state_name = BATCHES[row["batch"]][0]
        decision = json.loads((SPEC / state_name).read_text())["candidate_decisions"][
            row["candidate_ref"]
        ]
        risk = classify_localized_standard_risk(decision)
        row["localized_standard_risk"] = risk
        row["production_features"]["localized_standard_risk"] = risk
        evidence_dir = ROOT / "curation/batches" / batch_id / "candidates" / candidate_id
        evidence_files = sorted(
            str(path.relative_to(ROOT)) for path in evidence_dir.glob("*evidence*")
        )
        references = decision.get("evidence") or decision.get("source_references") or []
        row["source_provenance"] = {
            "decision_external_references": references,
            "candidate_evidence_files": evidence_files,
            "source_type": "external-documented"
            if references or evidence_files
            else "verifier-only",
        }
        source_counts[row["source_provenance"]["source_type"]] += 1
    by_batch = {
        batch: {
            "before_C": evaluate([row for row in records if row["batch"] == batch], "C-risk-first"),
            "after_D": revised_routing([row for row in records if row["batch"] == batch]),
        }
        for batch in BATCHES
    }
    levels = Counter(row["localized_standard_risk"]["level"] for row in records)
    by_level_label = {
        level: dict(
            Counter(
                row["audit_label"] or "unaudited"
                for row in records
                if row["localized_standard_risk"]["level"] == level
            )
        )
        for level in ("none", "possible", "strong")
    }
    result = {
        "schema_version": 1,
        "purpose": "retrospective audit-routing simulation only; production v3.1 unchanged",
        "input_sha256": input_sha,
        "risk_levels": dict(levels),
        "risk_by_audit_label": by_level_label,
        "source_type_counts": dict(source_counts),
        "records": records,
        "pooled": {
            "before_C": evaluate(records, "C-risk-first"),
            "after_D": revised_routing(records),
        },
        "by_batch": by_batch,
        "limitations": [
            "The rule was developed after observing the flash-drive audit; "
            "final-batch performance is retrospective fit, not prospective validation.",
            "Earlier batches lack structured preference_risk; a missing signal "
            "is not evidence of no risk.",
            "Fast-path production decisions carry no independent external source "
            "citations; source type cannot predict this failure from these records.",
            "Unaudited candidates have unknown true quality and never count as confirmed safe.",
        ],
    }
    atomic_json(OUTPUT, result)
    print("levels", dict(levels), "source types", dict(source_counts))
    for batch, values in by_batch.items():
        print(
            batch,
            values["before_C"]["audit_count"],
            values["after_D"]["audit_count"],
            values["after_D"]["critical_missed"],
        )


if __name__ == "__main__":
    main()
