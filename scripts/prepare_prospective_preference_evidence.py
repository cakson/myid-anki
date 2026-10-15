#!/usr/bin/env python3
"""Prepare and validate bounded preference research after frozen v3.1 decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from indo_malay_anki.curation.evidence_cache import EvidenceCache, normalized
from indo_malay_anki.curation.preference_evidence import (
    preference_trigger,
    validate_source_record,
)
from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
COHORT = "prospective-preference-50"
STATE = SPEC / f"{COHORT}-state.json"
MANIFEST = SPEC / f"{COHORT}-research-manifest.json"
EVIDENCE = SPEC / f"{COHORT}-evidence.json"
VALID_CONCLUSIONS = {"low-concern", "review-worthy", "material-blocker"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare() -> dict:
    state = json.loads(STATE.read_text())
    if len(state.get("candidate_decisions", {})) != state.get("target_candidates"):
        raise ValueError("freeze all candidate decisions before targeted research")
    items = {}
    cached = EvidenceCache(ROOT).records()
    for ref, decision in sorted(state["candidate_decisions"].items()):
        reasons = preference_trigger(decision)
        if reasons:
            candidate = decision["candidate"]
            cache_matches = [
                {
                    "cache_key": fact["cache_key"],
                    "claim_kind": fact["claim_kind"],
                    "source_family": fact["source_family"],
                    "canonical_reference": fact["canonical_reference"],
                }
                for fact in cached
                if fact["locale"] in {"Indonesia", "Malaysia"}
                and normalized(fact["form"])
                == normalized(
                    candidate["indonesian"]
                    if fact["locale"] == "Indonesia"
                    else candidate["malaysian"]
                )
                and normalized(fact["sense"]) == normalized(candidate["sense"])
            ]
            items[ref] = {
                "candidate": candidate,
                "relation": decision["relation"],
                "v3_1_outcome": decision["outcome"],
                "trigger_reasons": reasons,
                "named_alternative": decision.get("verifier", {})
                .get("preference_risk", {})
                .get("form", ""),
                "cached_evidence": cache_matches,
            }
    result = {
        "schema_version": 1,
        "purpose": "targeted source-role research, not universal evidence gate",
        "production_state_digest": digest(STATE),
        "triggered_count": len(items),
        "cache_candidate_hits": sum(bool(item["cached_evidence"]) for item in items.values()),
        "cache_candidate_misses": sum(not item["cached_evidence"] for item in items.values()),
        "items": items,
    }
    if MANIFEST.exists() and json.loads(MANIFEST.read_text()) != result:
        raise ValueError("saved research manifest differs from frozen production decisions")
    atomic_json(MANIFEST, result)
    if not EVIDENCE.exists():
        atomic_json(
            EVIDENCE,
            {
                "schema_version": 1,
                "manifest_digest": digest(MANIFEST),
                "started_at_utc": datetime.now(UTC).isoformat(),
                "research_operations": [],
                "items": {},
            },
        )
    return result


def finalize() -> dict:
    manifest = json.loads(MANIFEST.read_text())
    evidence = json.loads(EVIDENCE.read_text())
    state = json.loads(STATE.read_text())
    if evidence["manifest_digest"] != digest(MANIFEST):
        raise ValueError("evidence is not linked to the frozen manifest")
    if manifest["production_state_digest"] != digest(STATE):
        raise ValueError("production decisions changed after research selection")
    if set(evidence["items"]) != set(manifest["items"]):
        raise ValueError("every triggered candidate needs an explicit research outcome")
    enriched = {}
    for ref, decision in state["candidate_decisions"].items():
        copy = dict(decision)
        copy["v3_1_outcome"] = decision["outcome"]
        if ref in evidence["items"]:
            research = evidence["items"][ref]
            if research.get("usage_conclusion") not in VALID_CONCLUSIONS:
                raise ValueError(f"invalid usage conclusion for {ref}")
            if not isinstance(research.get("rationale"), str) or not research["rationale"].strip():
                raise ValueError(f"missing usage rationale for {ref}")
            if research.get("competition_kind", "none") not in {
                "none",
                "borrowed",
                "shared-synonym",
                "localized-standard",
            }:
                raise ValueError(f"invalid competition kind for {ref}")
            sources = [validate_source_record(item) for item in research.get("sources", [])]
            copy["preference_evidence"] = {
                **research,
                "sources": sources,
                "trigger_reasons": manifest["items"][ref]["trigger_reasons"],
            }
            flags = set(copy.get("review_flags", []))
            if "technical-borrowing-risk" in manifest["items"][ref]["trigger_reasons"]:
                flags.add("technical-borrowing-risk")
            ordinary = {
                source["source_type"]
                for source in sources
                if "ordinary-usage" in source["claim_roles"]
                or "relative-preference" in source["claim_roles"]
            }
            if not ordinary:
                flags.add("preference-evidence-thin")
            if research["usage_conclusion"] in {"review-worthy", "material-blocker"}:
                flags.add("preference-uncertainty")
            if research.get("competition_kind") == "borrowed":
                flags.add("borrowed-form-competition")
            if research.get("evidence_conflict"):
                flags.add("usage-evidence-conflict")
            if sources and all(
                source["source_type"] == "official-dictionary-terminology" for source in sources
            ):
                flags.add("official-source-only-preference")
            copy["review_flags"] = sorted(flags)
            if research["usage_conclusion"] == "material-blocker":
                if not research.get("concrete_blocker"):
                    raise ValueError(f"material blocker needs concrete evidence: {ref}")
                copy["outcome"] = "hold"
                copy["reason_codes"] = sorted(
                    set(copy.get("reason_codes", [])) | {"targeted-usage-material-blocker"}
                )
        enriched[ref] = copy
    result = {
        "schema_version": 1,
        "policy_version": "3.1.0 with targeted evidence annotation",
        "production_state_digest": digest(STATE),
        "manifest_digest": digest(MANIFEST),
        "evidence_digest": digest(EVIDENCE),
        "production_with_evidence_ended_at_utc": datetime.now(UTC).isoformat(),
        "candidate_decisions": enriched,
    }
    atomic_json(SPEC / f"{COHORT}-enriched-state.json", result)
    return result


def main() -> None:
    global COHORT, STATE, MANIFEST, EVIDENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "finalize"))
    parser.add_argument(
        "--cohort",
        choices=("prospective-preference-50", "technical-borrowing-25"),
        default=COHORT,
    )
    args = parser.parse_args()
    COHORT = args.cohort
    STATE = SPEC / f"{COHORT}-state.json"
    MANIFEST = SPEC / f"{COHORT}-research-manifest.json"
    EVIDENCE = SPEC / f"{COHORT}-evidence.json"
    result = prepare() if args.phase == "prepare" else finalize()
    print(args.phase, len(result.get("items", result.get("candidate_decisions", {}))))


if __name__ == "__main__":
    main()
