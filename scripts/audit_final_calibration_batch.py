#!/usr/bin/env python3
"""Targeted independent audit of the final fresh calibration batch."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from compare_historical_verifiers import call_model

from indo_malay_anki.curation.models import role_route
from indo_malay_anki.curation.preference_risk import audit_selection
from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
STATE = ROOT / "specs/003-vocabulary-curation/final-calibration-50-state.json"
OUTPUT = ROOT / "specs/003-vocabulary-curation/final-calibration-50-audit.json"
MODEL = role_route(ROOT, "adversarial-review")["model"]


def select(rows: list[dict]) -> tuple[list[dict], dict[str, list[str]]]:
    reasons = audit_selection(rows, seed=3004, medium_sample=2, high_sample=1)
    return (
        sorted(
            (row for row in rows if row["candidate_ref"] in reasons),
            key=lambda row: row["candidate_ref"],
        ),
        reasons,
    )


def prompt(group: list[dict], selection_reasons_for_prompt: dict[str, list[str]]) -> str:
    payload = [
        {
            "candidate_ref": row["candidate_ref"],
            "candidate": row["candidate"],
            "verified_relation": row["relation"],
            "confidence_tier": row["confidence_tier"],
            "confidence_rationale": row["confidence_rationale"],
            "review_flags": row["review_flags"],
            "preference_risk": row["verifier"].get("preference_risk", {}),
            "selection_reasons": selection_reasons_for_prompt.get(row["candidate_ref"], []),
        }
        for row in group
    ]
    return (
        "Independently audit these provisional Indonesian–Malaysian Malay cards. "
        "You did not generate or verify them. Judge exact cue sense, natural everyday "
        "Indonesian and Malaysian Malay usage, meaningful learning contrast, relation, "
        "and whether the confidence rationale explains actual risk. Look actively for "
        "semantic mismatches, artificial national contrasts, shared normal synonyms, "
        "register and regional errors, and no-contrast cards. Do not browse. "
        "Return JSON with `items` list, exactly one item per candidate_ref. Each item "
        "must contain candidate_ref, verdict (confirmed-good/minor-correction/"
        "materially-misleading/should-hold/should-reject), reason, relation, "
        "corrections (object of exact learner or metadata field changes), "
        "material_false_positive (boolean), confidence_rationale_adequate (boolean), "
        "and external_check_needed (boolean). Minor cue/metadata corrections are not "
        "material false positives. A card that should not be shown as written is. "
        "Do not favor acceptance for throughput. Distinguish learner-answer, "
        "learner-cue, and metadata-only changes in `corrections`.\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    production = json.loads(STATE.read_text())
    if production.get("phase") != "production-complete":
        raise ValueError("production decisions must be frozen before audit")
    selected, selection_reasons = select(list(production["candidate_decisions"].values()))
    output = OUTPUT
    refs = [row["candidate_ref"] for row in selected]
    audit = (
        json.loads(output.read_text())
        if output.exists()
        else {
            "schema_version": 1,
            "model": MODEL,
            "selection_policy": (
                "all false friends, low, very-low and strong flags; seeded 2 medium and 1 high"
            ),
            "selection_reasons": selection_reasons,
            "selected_refs": refs,
            "started_at_utc": datetime.now(UTC).isoformat(),
            "attempts": [],
            "results": {},
        }
    )
    if audit["selected_refs"] != refs:
        raise ValueError("audit cohort changed")
    pending = [row for row in selected if row["candidate_ref"] not in audit["results"]]
    for offset in range(0, len(pending), 5):
        group = pending[offset : offset + 5]
        for retry in range(2):
            with tempfile.TemporaryDirectory(prefix="myid-fresh-audit-") as tmp:
                attempt = call_model(
                    ROOT,
                    Path(tmp),
                    "final-calibration-audit",
                    MODEL,
                    prompt(group, selection_reasons),
                )
            audit["attempts"].append(
                {
                    **{
                        key: value
                        for key, value in attempt.items()
                        if key not in {"decision", "response_text"}
                    },
                    "group_refs": [row["candidate_ref"] for row in group],
                    "group_retry": retry,
                }
            )
            atomic_json(output, audit)
            if attempt["status"] == "complete":
                break
        else:
            raise RuntimeError(attempt.get("error_summary") or "audit model call failed twice")
        items = attempt["decision"].get("items", [])
        by_ref = {item.get("candidate_ref"): item for item in items if isinstance(item, dict)}
        for row in group:
            ref = row["candidate_ref"]
            item = by_ref.get(ref)
            if not item or item.get("verdict") not in {
                "confirmed-good",
                "minor-correction",
                "materially-misleading",
                "should-hold",
                "should-reject",
            }:
                atomic_json(output, audit)
                raise ValueError(f"missing or malformed audit result for {ref}")
            audit["results"][ref] = item
        atomic_json(output, audit)
        print(f"audited {len(audit['results'])}/{len(refs)}", flush=True)
    audit["ended_at_utc"] = datetime.now(UTC).isoformat()
    atomic_json(output, audit)


if __name__ == "__main__":
    main()
