#!/usr/bin/env python3
"""Prepare a read-only, guarded recommendation for the final calibration batch."""

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
PRODUCTION = SPEC / "final-calibration-50-state.json"
AUDIT = SPEC / "final-calibration-50-audit.json"
PREVIEW = SPEC / "final-calibration-50-promotion-preview.json"
ELIGIBLE = {"similar", "different-common-word", "false-friend"}
UNSAFE = {"materially-misleading", "should-hold", "should-reject"}
RELATION_EDITS = {
    "cal3-actions-001:actions-04": "similar",
    "cal3-home-001:home-09": "similar",
    "cal3-home-001:home-10": "similar",
}
RATIONALE_EDITS = {
    "cal3-home-001:home-10": (
        "Deterjen and detergen express the same detergent concept with a useful spelling "
        "contrast; Malaysian everyday washing-product terms also vary."
    ),
}
ADJUDICATION_NOTES = {
    "cal3-food-001:food-05": (
        "The named English alternative is code switching, rather than a competing "
        "Malay lexical answer; retained original learner fields."
    ),
    "cal3-home-001:home-08": (
        "Retained beg beli-belah. The suggested beg membeli-belah also occurs, but DBP "
        "distinguishes noun modifier beli-belah from verbal membeli-belah and Malaysian "
        "published usage attests the original phrase."
    ),
    "cal3-home-001:home-10": (
        "Mapped the audit's out-of-schema orthographic-variant label to similar."
    ),
    "cal3-actions-001:actions-04": (
        "Preview-only relation correction: recognizable memperbaiki/membaiki forms are similar."
    ),
    "cal3-home-001:home-09": (
        "Preview-only relation correction: recognizable ubin/jubin forms are similar."
    ),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    production = json.loads(PRODUCTION.read_text())
    audit = json.loads(AUDIT.read_text())
    decisions = production["candidate_decisions"]
    if len(decisions) != 50 or set(audit["results"]) != set(audit["selected_refs"]):
        raise ValueError("production or targeted audit is incomplete")
    source = ROOT / "data/vocabulary.tsv"
    rows = _source_rows(source)
    if len(rows) != 103:
        raise ValueError("canonical corpus changed during calibration")
    items: list[dict] = []
    projected: list[dict] = []
    for ref, row in sorted(decisions.items()):
        if row["outcome"] != "accepted":
            continue
        audit_result = audit["results"].get(ref)
        verdict = audit_result["verdict"] if audit_result else "not-sampled"
        candidate = copy.deepcopy(row["candidate"])
        relation = RELATION_EDITS.get(ref, row["relation"])
        status = (
            "withheld-audit"
            if verdict in UNSAFE or (audit_result and audit_result.get("material_false_positive"))
            else "ready-audited"
            if audit_result
            else "ready-under-sampled-policy"
        )
        if relation not in ELIGIBLE or relation == "false-friend":
            status = "withheld-relation-gate"
        item = {
            "candidate_ref": ref,
            "original_candidate": row["candidate"],
            "candidate": candidate,
            "production_outcome": row["outcome"],
            "audit_verdict": verdict,
            "audit_reason": audit_result.get("reason", "") if audit_result else "",
            "audit_proposed_corrections": audit_result.get("corrections", {})
            if audit_result
            else {},
            "audit_selection_reasons": audit.get("selection_reasons", {}).get(ref, []),
            "relation_before": row["relation"],
            "relation": relation,
            "confidence_tier": row["confidence_tier"],
            "confidence_rationale_before": row["confidence_rationale"],
            "confidence_rationale": RATIONALE_EDITS.get(ref, row["confidence_rationale"]),
            "review_flags": row["review_flags"],
            "preference_risk": row["verifier"].get("preference_risk", {}),
            "adjudication_note": ADJUDICATION_NOTES.get(ref, ""),
            "promotion_status": status,
        }
        items.append(item)
        if status.startswith("ready-"):
            projected.append(
                {
                    "id": ref,
                    "english": candidate["english"],
                    "indonesian": candidate["indonesian"],
                    "malaysian": candidate["malaysian"],
                    "relation": relation,
                }
            )
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
        "ready_audited_count": sum(x["promotion_status"] == "ready-audited" for x in items),
        "ready_under_sampled_policy_count": sum(
            x["promotion_status"] == "ready-under-sampled-policy" for x in items
        ),
        "withheld_accepted_count": sum(x["promotion_status"].startswith("withheld") for x in items),
        "ready_relation_distribution": dict(Counter(row["relation"] for row in projected)),
        "items": items,
        "production_nonaccepts": [
            {"candidate_ref": ref, "outcome": row["outcome"], "reason": row["reason_codes"]}
            for ref, row in sorted(decisions.items())
            if row["outcome"] != "accepted"
        ],
    }
    atomic_json(PREVIEW, result)
    print(f"ready={len(projected)} audited={result['ready_audited_count']} source={len(rows)}")


if __name__ == "__main__":
    main()
