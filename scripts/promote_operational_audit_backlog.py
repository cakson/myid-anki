#!/usr/bin/env python3
"""Promote only independently cleared, unchanged backlog cards."""

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
SOURCE = ROOT / "data/vocabulary.tsv"
LEDGER = ROOT / "curation/id-ledger.json"
RECORD = ROOT / "curation/promotions/operational-audit-backlog.json"
TECHNICAL = SPEC / "technical-borrowing-25-promotion-preview.json"
TECHNICAL_AUDIT = SPEC / "technical-borrowing-25-audit.json"
PROSPECTIVE = SPEC / "prospective-preference-50-promotion-preview.json"
PROSPECTIVE_AUDITS = (
    SPEC / "technical-borrowing-deferred-audit.json",
    SPEC / "technical-borrowing-deferred-random-audit.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cleared_items() -> list[dict]:
    technical = json.loads(TECHNICAL.read_text())["items"]
    audit = json.loads(TECHNICAL_AUDIT.read_text())["results"]
    prospective = json.loads(PROSPECTIVE.read_text())["items"]
    additional = {}
    for path in PROSPECTIVE_AUDITS:
        artifact = json.loads(path.read_text())
        if "results" in artifact:
            additional.update(artifact["results"])
        else:
            additional[artifact["candidate_ref"]] = artifact["result"]
    items = []
    for ref, item in technical.items():
        finding = audit.get(ref, {})
        if (
            item["status"] == "independently-cleared"
            and finding.get("verdict") == "confirmed-good"
            and not finding.get("corrections")
            and not finding.get("material_false_positive")
        ):
            items.append(
                {
                    "ref": ref,
                    "candidate": item["candidate"],
                    "relation": item["relation"],
                    "finding": finding,
                    "audit_source": TECHNICAL_AUDIT.name,
                }
            )
    for ref, item in prospective.items():
        finding = additional.get(ref, {})
        if (
            item["status"] == "not-deep-audited"
            and finding.get("verdict") == "confirmed-good"
            and not finding.get("corrections")
            and not finding.get("material_false_positive")
        ):
            items.append(
                {
                    "ref": ref,
                    "candidate": item["corrected_candidate"],
                    "relation": item["relation"],
                    "finding": finding,
                    "audit_source": "technical-borrowing-deferred",
                }
            )
    return sorted(items, key=lambda item: item["ref"])


def promote(*, dry_run: bool) -> dict:
    recover_export(ROOT)
    if RECORD.exists():
        existing = json.loads(RECORD.read_text())
        if existing["source_digest_after"] == digest(SOURCE) and existing[
            "ledger_digest_after"
        ] == digest(LEDGER):
            return existing
        raise ValueError("backlog promotion record no longer matches canonical source")
    rows = _source_rows(SOURCE)
    if len(rows) != 127:
        raise ValueError("expected preserved 127-card source")
    ledger = copy.deepcopy(load_ledger(ROOT))
    items = cleared_items()
    if len(items) != 10:
        raise ValueError(f"unexpected cleared backlog count: {len(items)}")
    new_rows = []
    for item in items:
        ref = item["ref"]
        batch_id, candidate_id = ref.split(":", 1)
        candidate = item["candidate"]
        if BatchStore(ROOT, batch_id).candidate(candidate_id) != candidate:
            raise ValueError(f"candidate changed: {ref}")
        if item["relation"] not in {"similar", "different-common-word", "false-friend"}:
            raise ValueError(f"ineligible relation: {ref}")
        concept_id = assigned_id(ledger, batch_id, candidate_id)
        if concept_id is None:
            concept_id = allocate_id(ledger)
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
        new_rows.append(row)
    if {row["id"] for row in rows} & {row["id"] for row in new_rows}:
        raise ValueError("permanent ID already in learner source")
    for row in new_rows:
        other_rows = [other for other in rows + new_rows if other["id"] != row["id"]]
        if find_deterministic_overlaps(row, other_rows):
            raise ValueError(f"duplicate learner concept: {row['english']}")
    before = {"source": digest(SOURCE), "ledger": digest(LEDGER)}
    if not dry_run:
        commit_learner_rows(ROOT, rows + new_rows, ledger, ["operational-audit-backlog"])
        validate_vocabulary(SOURCE, ROOT / "media")
    result = {
        "schema_version": 1,
        "status": "dry-run" if dry_run else "promoted",
        "source_digest_before": before["source"],
        "ledger_digest_before": before["ledger"],
        "source_digest_after": digest(SOURCE) if not dry_run else None,
        "ledger_digest_after": digest(LEDGER) if not dry_run else None,
        "source_artifact_digests": {
            path.name: digest(path)
            for path in (TECHNICAL, TECHNICAL_AUDIT, PROSPECTIVE, *PROSPECTIVE_AUDITS)
        },
        "learner_rows_before": len(rows),
        "learner_rows_added": len(new_rows),
        "learner_rows_after": len(rows) + len(new_rows),
        "items": items,
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
