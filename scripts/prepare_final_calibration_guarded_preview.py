#!/usr/bin/env python3
"""Freeze the post-routing guarded promotion subset without rewriting prior previews."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from indo_malay_anki.curation.duplicates import find_deterministic_overlaps
from indo_malay_anki.curation.export import _source_rows
from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
BASE = SPEC / "final-calibration-50-promotion-preview.json"
SUPPLEMENT = SPEC / "final-calibration-router-supplement-audit.json"
OUTPUT = SPEC / "final-calibration-50-guarded-preview.json"
UNSAFE = {"materially-misleading", "should-hold", "should-reject"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    base = json.loads(BASE.read_text())
    supplement = json.loads(SUPPLEMENT.read_text())
    first = json.loads((SPEC / "final-calibration-50-audit.json").read_text())
    production = json.loads((SPEC / "final-calibration-50-state.json").read_text())
    source = ROOT / "data/vocabulary.tsv"
    if base["canonical_source_digest"] != digest(source) or len(_source_rows(source)) != 103:
        raise ValueError("canonical source changed since the read-only preview")
    if set(first["results"]) & set(supplement["results"]):
        raise ValueError("supplemental audit overlaps the initial audit")
    audit_results = {**first["results"], **supplement["results"]}
    items = copy.deepcopy(base["items"])
    for item in items:
        ref = item["candidate_ref"]
        finding = audit_results.get(ref)
        if finding is None:
            item["promotion_status"] = "deferred-unaudited"
            item["audit_verdict"] = "not-sampled"
            continue
        item["audit_verdict"] = finding["verdict"]
        item["audit_reason"] = finding["reason"]
        item["audit_proposed_corrections"] = finding.get("corrections", {})
        item["audit_selection_reasons"] = first.get("selection_reasons", {}).get(
            ref
        ) or supplement.get("selection_reasons", {}).get(ref, [])
        item["promotion_status"] = (
            "withheld-audit"
            if finding["verdict"] in UNSAFE or finding.get("material_false_positive")
            else "ready-audited"
        )
        if ref == "cal3-actions-001:actions-04":
            # Both production verifier and supplemental independent audit selected
            # different-common-word; remove the earlier preview-only edit.
            item["relation"] = production["candidate_decisions"][ref]["relation"]
            item["confidence_rationale"] = (
                "Memperbaiki and membaiki are natural local repair verbs; "
                "memperbaiki is also understood in Malaysia, so the pair teaches "
                "a useful preference rather than exclusive word ownership."
            )
            item["adjudication_note"] = (
                "Kept the independently confirmed production relation and clarified overlap."
            )
        if ref == "cal3-food-001:food-04":
            item["review_flags"] = [
                flag for flag in item["review_flags"] if flag != "nonpreferred-alternative"
            ]
            item["adjudication_note"] = (
                "Removed an unsupported alternate-form flag; learner cue and answers stay intact."
            )
    ready = [item for item in items if item["promotion_status"] == "ready-audited"]
    deferred = [item for item in items if item["promotion_status"] == "deferred-unaudited"]
    withheld = [item for item in items if item["promotion_status"] == "withheld-audit"]
    if (len(ready), len(deferred), len(withheld)) != (22, 13, 3):
        raise ValueError("unexpected guarded promotion split")
    source_rows = _source_rows(source)
    projected = [
        {
            "id": item["candidate_ref"],
            "english": item["candidate"]["english"],
            "indonesian": item["candidate"]["indonesian"],
            "malaysian": item["candidate"]["malaysian"],
            "relation": item["relation"],
        }
        for item in ready
    ]
    for row in projected:
        overlaps = find_deterministic_overlaps(
            row, [other for other in source_rows + projected if other["id"] != row["id"]]
        )
        if overlaps:
            raise ValueError(f"guarded promotion would duplicate {row['id']}")
    result = {
        "schema_version": 1,
        "status": "guarded-recommendation",
        "base_preview_digest": digest(BASE),
        "production_digest": digest(SPEC / "final-calibration-50-state.json"),
        "first_audit_digest": digest(SPEC / "final-calibration-50-audit.json"),
        "supplement_audit_digest": digest(SUPPLEMENT),
        "canonical_source_digest": digest(source),
        "learner_rows_before": len(source_rows),
        "ready_count": len(ready),
        "deferred_unaudited_count": len(deferred),
        "withheld_unsafe_count": len(withheld),
        "ready_relation_distribution": dict(Counter(item["relation"] for item in ready)),
        "items": items,
        "production_nonaccepts": base["production_nonaccepts"],
    }
    atomic_json(OUTPUT, result)
    print(f"ready={len(ready)} deferred={len(deferred)} unsafe={len(withheld)}")


if __name__ == "__main__":
    main()
