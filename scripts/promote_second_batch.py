#!/usr/bin/env python3
"""Guardedly promote the 34 independently audited Batch 2 cards."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from indo_malay_anki.curation.duplicates import find_deterministic_overlaps
from indo_malay_anki.curation.export import _source_rows, commit_learner_rows, recover_export
from indo_malay_anki.curation.ids import allocate_id, append_assignment, assigned_id, load_ledger
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import utc_now
from indo_malay_anki.validator import validate_vocabulary

SPEC = Path("specs/003-vocabulary-curation")
PREVIEW = SPEC / "second-batch-50-promotion-preview.json"
PRODUCTION = SPEC / "second-batch-50-state.json"
AUDIT = SPEC / "second-batch-50-audit.json"
RECORD = Path("curation/promotions/second-batch-50.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def promote(root: Path, *, dry_run: bool) -> dict:
    root = Path(root)
    recover_export(root)
    preview = json.loads((root / PREVIEW).read_text())
    source = root / "data/vocabulary.tsv"
    ledger_path = root / "curation/id-ledger.json"
    record_path = root / RECORD
    if record_path.exists() and not dry_run:
        previous = json.loads(record_path.read_text())
        if (
            previous.get("status") == "promoted"
            and previous.get("source_digest_after") == digest(source)
            and previous.get("ledger_digest_after") == digest(ledger_path)
        ):
            return previous
        raise ValueError("Batch 2 promotion record exists but source or ledger differs")
    if preview["status"] != "recommendation-only" or preview["ready_count"] != 34:
        raise ValueError("the 34-card independent-audit preview is not valid")
    if preview["production_digest"] != digest(root / PRODUCTION):
        raise ValueError("frozen production artifact changed")
    if preview["audit_digest"] != digest(root / AUDIT):
        raise ValueError("independent audit artifact changed")
    if preview["canonical_source_digest"] != digest(source):
        raise ValueError("canonical learner source changed since the preview")
    old_rows = _source_rows(source)
    if len(old_rows) != 69 or preview["learner_rows_unchanged"] != 69:
        raise ValueError("expected the preserved 69-card source")
    ready = [item for item in preview["items"] if item["promotion_status"] == "ready"]
    withheld = [item for item in preview["items"] if item["promotion_status"] != "ready"]
    if len(ready) != 34 or len(withheld) != 6:
        raise ValueError("audit eligibility changed")
    ledger = copy.deepcopy(load_ledger(root))
    projected = []
    for item in ready:
        ref = item["candidate_ref"]
        batch_id, candidate_id = ref.split(":", 1)
        archived = BatchStore(root, batch_id).candidate(candidate_id)
        if archived != item["original_candidate"]:
            raise ValueError(f"original candidate changed: {ref}")
        if item["audit_verdict"] not in {"confirmed-good", "minor-correction"}:
            raise ValueError(f"audit did not clear: {ref}")
        if item["relation"] not in {"similar", "different-common-word"}:
            raise ValueError(f"relation is not cleared for this promotion: {ref}")
        candidate = item["candidate"]
        previous_id = assigned_id(ledger, batch_id, candidate_id)
        concept_id = previous_id or allocate_id(ledger)
        if not previous_id:
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
        item["concept_id"] = concept_id
        item["learner_row"] = row
        projected.append(row)
    if len({row["id"] for row in projected}) != len(projected):
        raise ValueError("new candidates received duplicate permanent IDs")
    old_by_id = {row["id"]: row for row in old_rows}
    if any(row["id"] in old_by_id for row in projected):
        raise ValueError("new card reused an old permanent ID")
    for item in ready:
        row = item["learner_row"]
        others = [other for other in old_rows + projected if other["id"] != row["id"]]
        overlaps = find_deterministic_overlaps(row, others)
        if overlaps:
            raise ValueError(f"promotion duplicate: {item['candidate_ref']}: {overlaps}")
    final = old_rows + projected
    if len(final) != 103 or any(row["relation"] == "same" for row in final):
        raise ValueError("guarded promotion violates expected deck count or relation")
    before_source = digest(source)
    before_ledger = digest(ledger_path)
    if not dry_run:
        commit_learner_rows(root, final, ledger, ["second-batch-50"])
        validate_vocabulary(source, root / "media")
    result = {
        "schema_version": 1,
        "promotion_id": "second-batch-50",
        "status": "dry-run" if dry_run else "promoted",
        "preview_digest": digest(root / PREVIEW),
        "production_digest": digest(root / PRODUCTION),
        "audit_digest": digest(root / AUDIT),
        "source_digest_before": before_source,
        "source_digest_after": digest(source) if not dry_run else None,
        "ledger_digest_before": before_ledger,
        "ledger_digest_after": digest(ledger_path) if not dry_run else None,
        "learner_rows_before": len(old_rows),
        "learner_rows_added": len(projected),
        "learner_rows_after": len(final),
        "relation_distribution": dict(Counter(row["relation"] for row in projected)),
        "confidence_distribution": dict(Counter(item["confidence_tier"] for item in ready)),
        "items": ready + withheld,
        "excluded_production_nonaccepts": preview["production_nonaccepts"],
    }
    if not dry_run:
        atomic_json(record_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = promote(Path.cwd(), dry_run=args.dry_run)
    print(result["status"], result["learner_rows_added"], result["learner_rows_after"])


if __name__ == "__main__":
    main()
