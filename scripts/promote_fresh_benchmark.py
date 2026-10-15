#!/usr/bin/env python3
"""Guardedly promote the fully audited fresh Feature 003 calibration batch."""
# ruff: noqa: E501

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
PRODUCTION = SPEC / "fresh-batch-50-state.json"
FIRST_AUDIT = SPEC / "fresh-batch-50-audit.json"
COMPLETION_AUDIT = SPEC / "fresh-batch-50-audit-completion.json"
PREVIEW = SPEC / "fresh-batch-50-promotion-preview.json"
RECORD = Path("curation/promotions/fresh-batch-50.json")
SAFE_VERDICTS = {"confirmed-good", "minor-correction"}
ELIGIBLE_RELATIONS = {"similar", "different-common-word", "false-friend"}

# Every accepted learner-facing change is explicit. Audit prose is never copied
# into the TSV as if it were a validated replacement value.
CANDIDATE_EDITS = {
    "fresh-food-001:food-07": {
        "english": "printed receipt",
        "sense": "a printed receipt or transaction slip given as proof of a purchase",
    },
    "fresh-home-001:home-08": {"malaysian": "sikat"},
    "fresh-actions-001:action-03": {
        "sense": (
            "make software or information current, including by installing or applying "
            "a newer software version"
        )
    },
}

RATIONALE_EDITS = {
    "fresh-actions-001:action-01": "Mengunduh and memuat turun are standard localized download terms; the shared English borrowing download is also common informally in both varieties.",
    "fresh-actions-001:action-02": "Mengunggah and memuat naik are standard localized upload terms; the shared English borrowing upload is also common informally in both varieties.",
    "fresh-actions-001:action-03": "Memperbarui and mengemas kini align for making software or information current; the shared borrowing update also occurs informally.",
    "fresh-actions-001:action-04": "Kata sandi and kata laluan are useful standard password terms, while password itself is a common shared informal alternative.",
    "fresh-actions-001:action-05": "Papan ketik and papan kekunci are parallel localized keyboard terms; keyboard is also common informally in both varieties.",
    "fresh-actions-001:action-09": "Darurat and kecemasan align for an emergency, but Malay darurat also occurs, especially for grave or officially declared emergencies; this is a preference contrast.",
    "fresh-actions-001:action-10": "Berisik is a common Indonesian noisy descriptor and bising a usual Malay choice; bising is also valid in Indonesian, so the contrast is preferential.",
    "fresh-food-001:food-07": "Struk naturally names a printed purchase slip and resit a written receipt; the narrowed printed-receipt cue aligns the meanings.",
    "fresh-home-001:home-04": "Tirai is natural Indonesian, though gorden is also common; langsir is usual Malay while tirai exists there too, so this is a preference contrast.",
    "fresh-home-001:home-08": "Sisir is the ordinary Indonesian comb noun and Malay sikat directly names a hair comb; the corrected Malay form aligns the toothed-tool cue.",
    "fresh-travel-001:travel-02": "Peron is usual in Indonesian railway contexts and platform common in Malaysia, though Indonesian platform and Malay pelantar are available alternatives.",
    "fresh-travel-001:travel-10": "Perahu and bot can name a small boat, but Malay perahu also occurs for traditional craft and bot often suggests a modern or motorized boat; the contrast is contextual.",
    "fresh-work-001:work-01": "Karyawan is a common Indonesian employment term and pekerja a natural Malay equivalent; pekerja is also ordinary Indonesian, making this a preference contrast.",
    "fresh-work-001:work-03": "PR is the usual Indonesian school-homework abbreviation and kerja rumah a Malay phrase; the latter can also mean housework outside the school context.",
    "fresh-work-001:work-06": "Presentasi and pembentangan fit a formal talk in Indonesian and standard Malay; Indonesian pemaparan and English presentation in Malaysian professional speech also occur.",
    "fresh-work-001:work-08": "Lamaran kerja and permohonan kerja align for a job application and share kerja; Malay permohonan pekerjaan is another natural variant.",
    "fresh-work-001:work-09": "Perusahaan and syarikat are usual company terms in Indonesian and Malay respectively; perusahaan also exists in Malay, so the contrast is preferred usage rather than exclusivity.",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(root: Path) -> tuple[dict, dict[str, dict]]:
    production = json.loads((root / PRODUCTION).read_text())
    first = json.loads((root / FIRST_AUDIT).read_text())
    completion = json.loads((root / COMPLETION_AUDIT).read_text())
    accepted = {
        ref
        for ref, row in production["candidate_decisions"].items()
        if row["outcome"] == "accepted"
    }
    audits = {**first["results"], **completion["results"]}
    if len(production["candidate_decisions"]) != 50 or len(accepted) != 44:
        raise ValueError("fresh production cohort differs from the frozen 50-candidate run")
    if len(first["results"]) != 23 or len(completion["results"]) != 21:
        raise ValueError("complete audit requires the 23-card and 21-card audit artifacts")
    if set(audits) != accepted or set(first["results"]) & set(completion["results"]):
        raise ValueError("audit IDs do not exactly cover the 44 provisional accepts")
    minor = {ref for ref, result in audits.items() if result["verdict"] == "minor-correction"}
    if minor != set(RATIONALE_EDITS):
        raise ValueError("minor-correction rationales are incomplete or stale")
    return production, audits


def corrected_items(root: Path, production: dict, audits: dict[str, dict]) -> list[dict]:
    items = []
    for ref, row in sorted(production["candidate_decisions"].items()):
        if row["outcome"] != "accepted":
            continue
        batch_id, candidate_id = ref.split(":", 1)
        archived = BatchStore(root, batch_id).candidate(candidate_id)
        if archived != row["candidate"]:
            raise ValueError(f"source candidate changed after production: {ref}")
        audit = audits[ref]
        candidate = copy.deepcopy(archived)
        candidate.update(CANDIDATE_EDITS.get(ref, {}))
        safe = audit["verdict"] in SAFE_VERDICTS and not audit["material_false_positive"]
        if row["relation"] not in ELIGIBLE_RELATIONS:
            safe = False
        if row["relation"] == "false-friend":
            # No accepted false friend exists in this frozen batch. A future
            # false-friend promotion needs its strict evidence/contrast record.
            safe = False
        rationale = RATIONALE_EDITS.get(ref, row["confidence_rationale"])
        item = {
            "candidate_ref": ref,
            "original_candidate": archived,
            "candidate": candidate,
            "original_decision": row["outcome"],
            "audit_verdict": audit["verdict"],
            "audit_reason": audit["reason"],
            "audit_corrections": audit.get("corrections", {}),
            "applied_candidate_edits": CANDIDATE_EDITS.get(ref, {}),
            "original_confidence": row["confidence_tier"],
            "confidence": row["confidence_tier"],
            "original_confidence_rationale": row["confidence_rationale"],
            "confidence_rationale": rationale,
            "original_review_flags": row["review_flags"],
            "review_flags": row["review_flags"],
            "relation": row["relation"],
            "promotion_status": "ready" if safe else "withheld",
            "provenance": {
                "batch_id": batch_id,
                "candidate_id": candidate_id,
                "production_artifact": str(PRODUCTION),
                "audit_artifacts": [str(FIRST_AUDIT), str(COMPLETION_AUDIT)],
            },
        }
        if ref == "fresh-work-001:work-09":
            item["confidence_calibration_note"] = (
                "Auditor proposed high; original very-low is retained until tiers have "
                "broader empirical calibration and preference evidence."
            )
        items.append(item)
    if sum(item["promotion_status"] == "ready" for item in items) != 41:
        raise ValueError("unexpected number of audit-cleared fresh cards")
    return items


def promote(root: Path, *, dry_run: bool) -> dict:
    root = Path(root)
    production, audits = load_inputs(root)
    recover_export(root)
    record_path = root / RECORD
    source = root / "data/vocabulary.tsv"
    if record_path.exists() and not dry_run:
        prior = json.loads(record_path.read_text())
        if (
            prior.get("status") == "promoted"
            and prior.get("source_digest_after") == digest(source)
            and prior.get("production_digest") == digest(root / PRODUCTION)
            and prior.get("first_audit_digest") == digest(root / FIRST_AUDIT)
            and prior.get("completion_audit_digest") == digest(root / COMPLETION_AUDIT)
        ):
            return prior
        raise ValueError("promotion record exists but canonical source differs")
    items = corrected_items(root, production, audits)
    old_rows = _source_rows(source)
    if len(old_rows) != 28:
        raise ValueError("expected the 28-card canonical source before fresh promotion")
    old_digest = digest(source)
    old_by_id = {row["id"]: row for row in old_rows}
    ledger = copy.deepcopy(load_ledger(root))
    projected = []
    for item in items:
        if item["promotion_status"] != "ready":
            continue
        ref = item["candidate_ref"]
        candidate = item["candidate"]
        batch_id, candidate_id = ref.split(":", 1)
        prior = assigned_id(ledger, batch_id, candidate_id)
        concept_id = prior or allocate_id(ledger)
        if not prior:
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
    for item in items:
        if item["promotion_status"] != "ready":
            continue
        row = item["learner_row"]
        others = [other for other in old_rows + projected if other["id"] != row["id"]]
        overlaps = find_deterministic_overlaps(row, others)
        if overlaps:
            raise ValueError(f"promotion duplicate: {item['candidate_ref']}: {overlaps}")
    final_by_id = {**old_by_id, **{row["id"]: row for row in projected}}
    if len(final_by_id) != len(old_rows) + len(projected):
        raise ValueError("new candidate reused an existing permanent ID")
    if digest(source) != old_digest:
        raise ValueError("canonical source changed during promotion preflight")
    if not dry_run:
        commit_learner_rows(root, list(final_by_id.values()), ledger, ["fresh-batch-50"])
        validate_vocabulary(source, root / "media")
    result = {
        "schema_version": 1,
        "promotion_id": "fresh-batch-50",
        "status": "dry-run" if dry_run else "promoted",
        "source_digest_before": old_digest,
        "source_digest_after": digest(source) if not dry_run else None,
        "production_digest": digest(root / PRODUCTION),
        "first_audit_digest": digest(root / FIRST_AUDIT),
        "completion_audit_digest": digest(root / COMPLETION_AUDIT),
        "learner_rows_before": len(old_rows),
        "learner_rows_added": len(projected),
        "learner_rows_after": len(final_by_id),
        "promoted_relation_distribution": dict(Counter(row["relation"] for row in projected)),
        "promoted_confidence_distribution": dict(
            Counter(item["confidence"] for item in items if item["promotion_status"] == "ready")
        ),
        "excluded": [
            {"candidate_ref": ref, "reason": row["reason_codes"]}
            for ref, row in sorted(production["candidate_decisions"].items())
            if row["outcome"] != "accepted"
        ]
        + [
            {
                "candidate_ref": item["candidate_ref"],
                "reason": item["audit_reason"],
                "audit_verdict": item["audit_verdict"],
            }
            for item in items
            if item["promotion_status"] != "ready"
        ],
        "items": items,
    }
    atomic_json(root / PREVIEW, result)
    if not dry_run:
        atomic_json(record_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = promote(Path.cwd(), dry_run=args.dry_run)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "items"},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
