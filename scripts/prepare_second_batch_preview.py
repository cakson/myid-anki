#!/usr/bin/env python3
"""Prepare a guarded, read-only promotion recommendation for calibration batch two."""

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
PRODUCTION = SPEC / "second-batch-50-state.json"
AUDIT = SPEC / "second-batch-50-audit.json"
PREVIEW = SPEC / "second-batch-50-promotion-preview.json"
SAFE = {"confirmed-good", "minor-correction"}
ELIGIBLE = {"similar", "different-common-word", "false-friend"}

# Audited substitutions are not automatically safe. Only these reviewed changes enter
# the preview; the original model proposals remain in the audit artifact.
CONTENT_EDITS = {
    "cal2-daily-001:daily-03": {
        "english": "washbasin",
        "sense": "a fixed basin used for washing hands or face, especially in a bathroom",
        "tags": ["household-items", "bathroom"],
    },
    "cal2-daily-001:daily-10": {"english": "to tidy a room"},
    "cal2-shopping-001:shopping-08": {"sense": "a service made available to customers or users"},
    "cal2-travel-001:travel-04": {"english": "traffic congestion"},
    "cal2-work-001:work-03": {
        "english": "school score",
        "sense": "the points or numerical score received for schoolwork",
    },
}
RELATION_EDITS = {"cal2-shopping-001:shopping-02": "similar"}
RATIONALE_EDITS = {
    "cal2-daily-001:daily-02": (
        "Keran and paip both cover the intended tap; Malay paip also names the water pipe, "
        "while pili and kepala paip can specify the flow-control fitting."
    ),
    "cal2-daily-001:daily-03": (
        "Wastafel denotes a washbasin for washing hands or face, and sinki covers that "
        "fixture in Malay; the narrowed cue avoids the broader kitchen-sink sense."
    ),
    "cal2-daily-001:daily-07": (
        "Seprai and cadar both denote a bedsheet in the stated languages. Indonesian "
        "cadar commonly has a face-veil sense, which makes the Malay term worth learning."
    ),
    "cal2-daily-001:daily-09": (
        "Menyetrika and menggosok pakaian both mean ironing clothes. Malay menyeterika "
        "also occurs, so this is a preferred-expression contrast."
    ),
    "cal2-daily-001:daily-10": (
        "Merapikan and mengemas both work for tidying a room; the room cue avoids "
        "mengemas's additional packing sense."
    ),
    "cal2-shopping-001:shopping-02": (
        "Uang tunai and wang tunai express the same cash concept; uang and wang are "
        "recognizably related language-specific forms, so similar is the useful relation."
    ),
    "cal2-shopping-001:shopping-08": (
        "Layanan and perkhidmatan fit a service made available to users or customers. "
        "Indonesian jasa and pelayanan overlap in some contexts."
    ),
    "cal2-social-001:social-09": (
        "Percaya diri and yakin diri express self-confidence. Malay also uses yakin, "
        "keyakinan diri, or fuller constructions depending on syntax."
    ),
    "cal2-social-001:social-07": (
        "Nongkrong and lepak are informal ordinary ways to describe hanging out. "
        "Both can also imply lingering or lounging, which fits the social cue."
    ),
    "cal2-travel-001:travel-01": (
        "Pesawat is the concise everyday Indonesian term for an airplane, while kapal "
        "terbang is a characteristic Malay choice; longer pesawat terms also cross varieties."
    ),
    "cal2-travel-001:travel-04": (
        "Kemacetan and kesesakan lalu lintas denote traffic congestion; conversational "
        "Indonesian macet and Malay jem are additional alternatives."
    ),
    "cal2-travel-001:travel-06": (
        "Kedatangan fits Indonesian arrival and ketibaan is characteristic Malay in "
        "transport contexts; Malay kedatangan remains ordinary in broader contexts."
    ),
    "cal2-work-001:work-03": (
        "Nilai and markah both fit a numerical school score; a letter or category grade "
        "would call for a different Malay cue, such as gred."
    ),
    "cal2-work-001:work-07": (
        "Seragam is usual in Indonesian and uniform common in Malaysian Malay. Both "
        "borrowed and native alternatives cross language boundaries, so this is a preference."
    ),
}
ADJUDICATION_NOTES = {
    "cal2-daily-001:daily-02": (
        "Keep paip: DBP explicitly defines paip as a water outlet/tap and equates it "
        "with pili; the proposed substitution was not required."
    ),
    "cal2-daily-001:daily-09": (
        "Keep menggosok pakaian: DBP defines menggosok as ironing clothes; the "
        "proposed menggosok baju is an alternative, not a correction."
    ),
    "cal2-daily-001:daily-10": (
        "Use a concise contextual cue rather than slash-separated answer variants."
    ),
    "cal2-shopping-001:shopping-02": (
        "Map the proposed out-of-schema cognate label to the allowed similar relation."
    ),
    "cal2-work-001:work-07": (
        "Retain the allowed different-common-word relation; the proposed label is "
        "outside the deck schema."
    ),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    production = json.loads(PRODUCTION.read_text())
    audit = json.loads(AUDIT.read_text())
    decisions = production["candidate_decisions"]
    accepted = {ref for ref, row in decisions.items() if row["outcome"] == "accepted"}
    if len(decisions) != 50 or len(accepted) != 40 or set(audit["results"]) != accepted:
        raise ValueError("the frozen 50-candidate production and audit cohorts must agree")
    minor = {
        ref for ref, result in audit["results"].items() if result["verdict"] == "minor-correction"
    }
    inadequate = {
        ref
        for ref, result in audit["results"].items()
        if result["verdict"] in SAFE and not result["confidence_rationale_adequate"]
    }
    if not (minor | inadequate) <= set(RATIONALE_EDITS):
        raise ValueError("every minor or inadequate rationale needs an explicit edit")
    source = ROOT / "data/vocabulary.tsv"
    rows = _source_rows(source)
    if len(rows) != 69:
        raise ValueError("the learner source must remain at 69 cards during this preview")
    items = []
    projected = []
    for ref, row in sorted(decisions.items()):
        if row["outcome"] != "accepted":
            continue
        audit_result = audit["results"][ref]
        candidate = copy.deepcopy(row["candidate"])
        candidate.update(CONTENT_EDITS.get(ref, {}))
        relation = RELATION_EDITS.get(ref, row["relation"])
        ready = audit_result["verdict"] in SAFE and not audit_result["material_false_positive"]
        ready &= relation in ELIGIBLE and relation != "false-friend"
        item = {
            "candidate_ref": ref,
            "original_candidate": row["candidate"],
            "candidate": candidate,
            "production_outcome": row["outcome"],
            "audit_verdict": audit_result["verdict"],
            "audit_reason": audit_result["reason"],
            "audit_proposed_corrections": audit_result.get("corrections", {}),
            "applied_candidate_edits": CONTENT_EDITS.get(ref, {}),
            "relation_before": row["relation"],
            "relation": relation,
            "confidence_tier": row["confidence_tier"],
            "confidence_rationale_before": row["confidence_rationale"],
            "confidence_rationale": RATIONALE_EDITS.get(ref, row["confidence_rationale"]),
            "review_flags": row["review_flags"],
            "adjudication_note": ADJUDICATION_NOTES.get(ref, ""),
            "promotion_status": "ready" if ready else "withheld",
        }
        items.append(item)
        if ready:
            projected.append(
                {
                    "id": ref,
                    "english": candidate["english"],
                    "indonesian": candidate["indonesian"],
                    "malaysian": candidate["malaysian"],
                    "relation": relation,
                }
            )
    if sum(item["promotion_status"] == "ready" for item in items) != 34:
        raise ValueError("unexpected audit-cleared promotion recommendation")
    for proposed in projected:
        overlaps = find_deterministic_overlaps(
            proposed, [other for other in rows + projected if other["id"] != proposed["id"]]
        )
        if overlaps:
            raise ValueError(f"promotion preview has duplicate concept: {proposed['id']}")
    result = {
        "schema_version": 1,
        "status": "recommendation-only",
        "production_digest": digest(PRODUCTION),
        "audit_digest": digest(AUDIT),
        "canonical_source_digest": digest(source),
        "learner_rows_unchanged": len(rows),
        "ready_count": len(projected),
        "withheld_accepted_count": len(items) - len(projected),
        "ready_relation_distribution": dict(Counter(row["relation"] for row in projected)),
        "items": items,
        "production_nonaccepts": [
            {"candidate_ref": ref, "outcome": row["outcome"], "reason": row["reason_codes"]}
            for ref, row in sorted(decisions.items())
            if row["outcome"] != "accepted"
        ],
    }
    atomic_json(PREVIEW, result)
    print(f"ready={len(projected)} withheld={len(items) - len(projected)} source={len(rows)}")


if __name__ == "__main__":
    main()
