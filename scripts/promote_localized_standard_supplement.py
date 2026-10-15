#!/usr/bin/env python3
"""Guardedly promote only the newly audited final-batch cards from this phase."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from indo_malay_anki.curation.duplicates import find_deterministic_overlaps
from indo_malay_anki.curation.export import _source_rows, commit_learner_rows, recover_export
from indo_malay_anki.curation.ids import allocate_id, append_assignment, assigned_id, load_ledger
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import utc_now
from indo_malay_anki.validator import validate_vocabulary

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
PREVIEW = SPEC / "final-calibration-50-guarded-preview.json"
SIMULATION = SPEC / "localized-standard-audit-simulation.json"
AUDIT = SPEC / "final-calibration-localized-standard-audit.json"
RECORD = ROOT / "curation/promotions/final-calibration-localized-standard.json"
SOURCE = ROOT / "data/vocabulary.tsv"
LEDGER = ROOT / "curation/id-ledger.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def promote(*, dry_run: bool) -> dict:
    recover_export(ROOT)
    if RECORD.exists() and not dry_run:
        existing = json.loads(RECORD.read_text())
        if existing.get("source_digest_after") == digest(SOURCE) and existing.get(
            "ledger_digest_after"
        ) == digest(LEDGER):
            return existing
        raise ValueError("supplemental promotion record no longer matches canonical data")
    preview = json.loads(PREVIEW.read_text())
    simulation = json.loads(SIMULATION.read_text())
    audit = json.loads(AUDIT.read_text())
    previous = json.loads((ROOT / "curation/promotions/final-calibration-50.json").read_text())
    if previous["source_digest_after"] != digest(SOURCE) or len(_source_rows(SOURCE)) != 125:
        raise ValueError("expected preserved 125-card source after first guarded promotion")
    if audit["simulation_digest"] != digest(SIMULATION):
        raise ValueError("audit selection and simulation differ")
    if audit["production_digest"] != digest(SPEC / "final-calibration-50-state.json"):
        raise ValueError("frozen production decisions changed")
    selected = simulation["by_batch"]["batch3"]["after_D"]
    routed = set(selected["deterministic_reasons"]) | set(selected["random_refs"])
    items = {item["candidate_ref"]: item for item in preview["items"]}
    if set(audit["results"]) != set(audit["selected_refs"]) or not set(audit["results"]) <= routed:
        raise ValueError("audit results do not match routing")
    old_rows = _source_rows(SOURCE)
    ledger = copy.deepcopy(load_ledger(ROOT))
    promoted_items = []
    projected = []
    for ref, finding in sorted(audit["results"].items()):
        item = copy.deepcopy(items[ref])
        if item["promotion_status"] != "deferred-unaudited":
            raise ValueError(f"candidate was already decided for promotion: {ref}")
        if finding["verdict"] not in {"confirmed-good", "minor-correction"} or finding.get(
            "material_false_positive"
        ):
            raise ValueError(f"candidate was not independently cleared: {ref}")
        if finding.get("corrections") not in ({}, [], None):
            raise ValueError(f"unadjudicated correction: {ref}")
        if finding["relation"] != item["relation"] or item["relation"] not in {
            "similar",
            "different-common-word",
        }:
            raise ValueError(f"relation changed or ineligible: {ref}")
        batch_id, candidate_id = ref.split(":", 1)
        if BatchStore(ROOT, batch_id).candidate(candidate_id) != item["original_candidate"]:
            raise ValueError(f"archived candidate changed: {ref}")
        candidate = item["candidate"]
        concept_id = assigned_id(ledger, batch_id, candidate_id) or allocate_id(ledger)
        if not assigned_id(ledger, batch_id, candidate_id):
            append_assignment(
                ledger,
                concept_id=concept_id,
                batch_id=batch_id,
                candidate_id=candidate_id,
                assigned_at=utc_now(),
                semantic_concept_key=candidate["sense"],
            )
        row = {
            "id": concept_id,
            "english": candidate["english"],
            "indonesian": candidate["indonesian"],
            "malaysian": candidate["malaysian"],
            "relation": item["relation"],
            "image": candidate.get("image", ""),
            "tags": " ".join(candidate.get("tags", [])),
            "contrast": "",
        }
        item.update(
            {
                "concept_id": concept_id,
                "learner_row": row,
                "promotion_status": "promoted-after-localized-standard-audit",
                "audit_verdict": finding["verdict"],
                "audit_reason": finding["reason"],
                "audit_selection_reasons": audit["selection_reasons"][ref],
            }
        )
        promoted_items.append(item)
        projected.append(row)
    if len(projected) != 2:
        raise ValueError("expected exactly two newly audited cards")
    for row in projected:
        if find_deterministic_overlaps(
            row, [other for other in old_rows + projected if other["id"] != row["id"]]
        ):
            raise ValueError(f"duplicate learner concept: {row['english']}")
    if {row["id"] for row in projected} & {row["id"] for row in old_rows}:
        raise ValueError("permanent ID reused")
    remaining = [
        ref
        for ref, item in items.items()
        if item["promotion_status"] == "deferred-unaudited" and ref not in audit["results"]
    ]
    if len(remaining) != 11:
        raise ValueError("unexpected remaining unaudited count")
    before_source, before_ledger = digest(SOURCE), digest(LEDGER)
    if not dry_run:
        commit_learner_rows(
            ROOT, old_rows + projected, ledger, ["final-calibration-localized-standard"]
        )
        validate_vocabulary(SOURCE, ROOT / "media")
    result = {
        "schema_version": 1,
        "promotion_id": "final-calibration-localized-standard",
        "status": "dry-run" if dry_run else "promoted",
        "simulation_digest": digest(SIMULATION),
        "audit_digest": digest(AUDIT),
        "preview_digest": digest(PREVIEW),
        "source_digest_before": before_source,
        "source_digest_after": digest(SOURCE) if not dry_run else None,
        "ledger_digest_before": before_ledger,
        "ledger_digest_after": digest(LEDGER) if not dry_run else None,
        "learner_rows_before": len(old_rows),
        "learner_rows_added": len(projected),
        "learner_rows_after": len(old_rows) + len(projected),
        "items": promoted_items,
        "remaining_deferred_unaudited": sorted(remaining),
    }
    if not dry_run:
        atomic_json(RECORD, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = promote(dry_run=args.dry_run)
    print(result["status"], result["learner_rows_added"], result["learner_rows_after"])


if __name__ == "__main__":
    main()
