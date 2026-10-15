#!/usr/bin/env python3
"""Targeted and random independent audit of the prospective 50-candidate cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from compare_historical_verifiers import call_model

from indo_malay_anki.curation.models import role_route
from indo_malay_anki.curation.preference_risk import STRONG_AUDIT_FLAGS
from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
COHORT = "prospective-preference-50"
STATE = SPEC / f"{COHORT}-enriched-state.json"
OUTPUT = SPEC / f"{COHORT}-audit.json"
MODEL = role_route(ROOT, "adversarial-review")["model"]
EVIDENCE_FLAGS = {
    "borrowed-form-competition",
    "usage-evidence-conflict",
    "official-source-only-preference",
    "preference-evidence-thin",
}
VALID = {
    "confirmed-good",
    "minor-correction",
    "materially-misleading",
    "should-hold",
    "should-reject",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select(decisions: dict[str, dict]) -> dict[str, list[str]]:
    selected = {}
    for ref, row in sorted(decisions.items()):
        if row["outcome"] != "accepted":
            continue
        reasons = []
        if row["relation"] == "false-friend":
            reasons.append("false-friend")
        if row.get("confidence_tier") in {"low", "very-low"}:
            reasons.append(f"confidence:{row['confidence_tier']}")
        flags = set(row.get("review_flags", []))
        reasons.extend(f"flag:{flag}" for flag in sorted(flags & STRONG_AUDIT_FLAGS))
        reasons.extend(f"evidence:{flag}" for flag in sorted(flags & EVIDENCE_FLAGS))
        if "technical-borrowing-risk" in flags:
            reasons.append("flag:technical-borrowing-risk")
        if reasons:
            selected[ref] = reasons
    pool = defaultdict(list)
    for ref, row in decisions.items():
        if row["outcome"] == "accepted" and ref not in selected:
            pool[row["confidence_tier"]].append(ref)
    for tier, refs in pool.items():
        fraction = 0.10 if tier == "high" else 0.15
        count = math.ceil(fraction * len(refs))
        ranked = sorted(
            refs,
            key=lambda ref: hashlib.sha256(
                f"feature003-prospective-audit-v1|{tier}|{ref}".encode()
            ).hexdigest(),
        )
        for ref in ranked[:count]:
            selected[ref] = [f"stratified-random:{tier}"]
    return dict(sorted(selected.items()))


def prompt(rows: list[dict], reasons: dict[str, list[str]]) -> str:
    payload = []
    for row in rows:
        research = row.get("preference_evidence") or {}
        payload.append(
            {
                "candidate_ref": row["candidate_ref"],
                "candidate": row["candidate"],
                "relation": row["relation"],
                "confidence_tier": row["confidence_tier"],
                "confidence_rationale": row["confidence_rationale"],
                "review_flags": row["review_flags"],
                "preference_risk": row.get("verifier", {}).get("preference_risk"),
                "targeted_evidence": research,
                "selection_reasons": reasons[row["candidate_ref"]],
            }
        )
    return (
        "Independently deep-audit these provisionally accepted Indonesian–Malaysian Malay "
        "cards. You did not generate or verify them. Check precise English cue sense, both "
        "learner answers, everyday usage, useful national contrast, relation, and any "
        "localized-standard versus borrowed-form problem. Treat cited evidence according "
        "to its source role: dictionary inclusion does not prove everyday preference, and "
        "one publication example does not prove relative frequency. Do not browse or "
        "generate candidates. Return JSON with `items`, exactly one per candidate_ref. "
        "Each item: candidate_ref, verdict (confirmed-good/minor-correction/"
        "materially-misleading/should-hold/should-reject), reason, relation, corrections "
        "(exact learner or metadata changes; [] if none), material_false_positive (boolean), "
        "confidence_rationale_adequate (boolean), external_check_needed (boolean). "
        "Be willing to find unsafe cards; do not force either acceptance or rejection.\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


def main() -> None:
    global COHORT, STATE, OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort",
        choices=("prospective-preference-50", "technical-borrowing-25"),
        default=COHORT,
    )
    args = parser.parse_args()
    COHORT = args.cohort
    STATE = SPEC / f"{COHORT}-enriched-state.json"
    OUTPUT = SPEC / f"{COHORT}-audit.json"
    state = json.loads(STATE.read_text())
    decisions = state["candidate_decisions"]
    selected = select(decisions)
    artifact = (
        json.loads(OUTPUT.read_text())
        if OUTPUT.exists()
        else {
            "schema_version": 1,
            "model": MODEL,
            "enriched_state_digest": digest(STATE),
            "selection_policy": (
                "all low/very-low/false-friend/strong flags/evidence risks; "
                "fixed-hash stratified random"
            ),
            "selection_reasons": selected,
            "selected_refs": sorted(selected),
            "started_at_utc": datetime.now(UTC).isoformat(),
            "attempts": [],
            "results": {},
        }
    )
    if artifact["selected_refs"] != sorted(selected) or artifact["enriched_state_digest"] != digest(
        STATE
    ):
        raise ValueError("audit selection differs from frozen enriched state")
    pending = [decisions[ref] for ref in sorted(selected) if ref not in artifact["results"]]
    for offset in range(0, len(pending), 5):
        group = pending[offset : offset + 5]
        with tempfile.TemporaryDirectory(prefix="myid-prospective-audit-") as temp:
            attempt = call_model(
                ROOT, Path(temp), f"prospective-audit-{offset}", MODEL, prompt(group, selected)
            )
        artifact["attempts"].append(
            {
                key: value
                for key, value in attempt.items()
                if key not in {"decision", "response_text"}
            }
        )
        atomic_json(OUTPUT, artifact)
        if attempt["status"] != "complete":
            raise RuntimeError(attempt.get("error_summary") or "prospective audit failed")
        items = attempt["decision"].get("items", [])
        indexed = {item.get("candidate_ref"): item for item in items if isinstance(item, dict)}
        if set(indexed) != {row["candidate_ref"] for row in group}:
            raise ValueError("audit results differ from requested candidates")
        for ref, item in indexed.items():
            if item.get("verdict") not in VALID:
                raise ValueError(f"invalid audit verdict: {ref}")
            artifact["results"][ref] = item
        atomic_json(OUTPUT, artifact)
        print("audited", len(artifact["results"]), "/", len(selected), flush=True)
    artifact["ended_at_utc"] = datetime.now(UTC).isoformat()
    atomic_json(OUTPUT, artifact)


if __name__ == "__main__":
    main()
