#!/usr/bin/env python3
"""Replay the frozen holds with claim-scoped evidence reuse; never promote data."""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import tempfile
import time
from collections import Counter
from pathlib import Path

from indo_malay_anki.curation.evidence_cache import (
    ArchivedObservationProvider,
    EvidenceCache,
    StoredCaptureProvider,
    materialize_observations,
    queries_for_candidate,
)
from indo_malay_anki.curation.gate import decide_candidate, preverification_reasons
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results


def run(root: Path, *, verifier_path: Path | None = None) -> dict:
    started = time.perf_counter()
    manifest = root / "specs/003-vocabulary-curation/historical-hold-sample.json"
    refs = json.loads(manifest.read_text(encoding="utf-8"))["candidate_refs"]
    if len(refs) != 26 or len(set(refs)) != 26:
        raise ValueError("the original frozen 26-candidate sample changed")
    verifier_results = {}
    if verifier_path and verifier_path.exists():
        for record in json.loads(verifier_path.read_text(encoding="utf-8"))["results"]:
            if record.get("status") == "complete":
                verifier_results[record["candidate_ref"]] = record
    cache = EvidenceCache(root)
    with tempfile.TemporaryDirectory(prefix="myid-evidence-replay-") as temporary:
        mirror = Path(temporary)
        shutil.copytree(root / "curation/batches", mirror / "curation/batches")
        (mirror / "data").mkdir()
        shutil.copy2(root / "data/vocabulary.tsv", mirror / "data/vocabulary.tsv")
        packets = []
        all_queries = []
        for ref in refs:
            batch_id, candidate_id = ref.split(":", 1)
            store = BatchStore(mirror, batch_id)
            candidate = store.candidate(candidate_id)
            stages = current_results(store, candidate_id)
            queries = queries_for_candidate(ref, candidate, stages)
            all_queries.extend(queries)
            packets.append((ref, store, candidate, stages, queries))

        before, initial_hits, initial_misses = cache.lookup_many(all_queries)
        unresolved_queries = [
            query for query in all_queries if not before[(query.candidate_ref, query.claim_id)]
        ]
        archived = ArchivedObservationProvider(mirror).lookup_many(unresolved_queries)
        # New inspections are always imported. A source already found in the archive
        # remains one source family, rather than counting as a second signal.
        captured = StoredCaptureProvider(root).lookup_many(all_queries)
        _, new_cache_records = cache.upsert_many(archived + captured)
        resolved, _, remaining_misses = cache.lookup_many(all_queries)

        rows = []
        for ref, store, candidate, stages, queries in packets:
            row_started = time.perf_counter()
            batch_id, candidate_id = ref.split(":", 1)
            archived_report = json.loads((store.path / "report.json").read_text())
            prior = next(
                row for row in archived_report["decisions"] if row["candidate_id"] == candidate_id
            )
            if prior["outcome"] != "hold":
                raise ValueError(f"historical decision changed for {ref}")
            old_observations = stages.get("evidence-audit", {}).get("observations", [])
            existing_keys = {
                (item["claim_id"], item["url_or_query"], item["source_group"])
                for item in old_observations
            }
            reused = [
                item
                for query in queries
                for item in materialize_observations(
                    query, resolved[(query.candidate_ref, query.claim_id)]
                )
                if (item["claim_id"], item["url_or_query"], item["source_group"])
                not in existing_keys
            ]
            if old_observations or reused:
                stages["evidence-audit"] = {"observations": old_observations + reused}
            new_verifier = verifier_results.get(ref)
            if new_verifier is not None:
                decision = new_verifier["decision"]
                if decision.get("verdict") in {"agree", "object"} and isinstance(
                    decision.get("material_concerns"), list
                ):
                    stages["independent-verification"] = decision
            gate = decide_candidate(candidate, stages, policy_version="2.0.0")
            outcome = "hold" if gate["outcome"] == "pending" else gate["outcome"]
            evidence_issues = preverification_reasons(candidate, stages)
            claim_types = {
                claim["claim_id"]: claim["claim_type"]
                for role in ("indonesian-usage", "malaysian-usage", "relation-proposal")
                for claim in stages.get(role, {}).get("claims", [])
            }
            unresolved_types = {
                claim_types.get(issue.removeprefix("unsupported-claim:"), "unknown")
                for issue in evidence_issues
                if issue.startswith("unsupported-claim:")
            }
            if "missing-stage:evidence-audit" in evidence_issues:
                unresolved_types.add("claim-linked-inspected-evidence")
            if "missing-within-locale-preference" in evidence_issues:
                unresolved_types.add("preferred-everyday-form")
            if stages.get("relation-proposal", {}).get("relation") == "different-common-word":
                if any(
                    not any(
                        claim.get("claim_type") == "preferred-choice"
                        for claim in stages.get(role, {}).get("claims", [])
                    )
                    for role in ("indonesian-usage", "malaysian-usage")
                ):
                    unresolved_types.add("preferred-everyday-form")
            if any("verifier" in reason for reason in gate["reason_codes"]):
                unresolved_types.add("independent-verification")
            if "concrete-adversarial-objection" in gate["reason_codes"]:
                unresolved_types.add("historical-concrete-objection")
            retrieved = sum(not before[(query.candidate_ref, query.claim_id)] for query in queries)
            rows.append(
                {
                    "candidate_ref": ref,
                    "english": candidate["english"],
                    "indonesian": candidate["indonesian"],
                    "malaysian": candidate["malaysian"],
                    "original_decision": "hold",
                    "new_decision": outcome,
                    "risk_tier": gate["risk"]["path"],
                    "fast_path_used": outcome == "accepted"
                    and gate["risk"]["path"] == "ordinary-fast",
                    "escalation_reasons": gate["risk"]["triggers"],
                    "decision_reasons": gate["reason_codes"],
                    "preverification_issues": evidence_issues,
                    "unresolved_claim_types": sorted(unresolved_types) if outcome == "hold" else [],
                    "unresolved_claims": [
                        value.removeprefix("unsupported-claim:")
                        for value in gate["reason_codes"]
                        if value.startswith("unsupported-claim:")
                    ],
                    "evidence_queries": len(queries),
                    "evidence_cache_hits_before_provider": len(queries) - retrieved,
                    "evidence_cache_misses_before_provider": retrieved,
                    "new_evidence_observations_linked": len(reused),
                    "verifier_calls": int(new_verifier is not None),
                    "model_calls": int(new_verifier is not None),
                    "input_tokens": new_verifier.get("input_tokens") if new_verifier else 0,
                    "output_tokens": new_verifier.get("output_tokens") if new_verifier else 0,
                    "model_elapsed_seconds": new_verifier.get("elapsed_seconds", 0)
                    if new_verifier
                    else 0,
                    "replay_processing_seconds": round(time.perf_counter() - row_started, 6),
                    "evidence_references": sorted(
                        {
                            item["url_or_query"]
                            for item in stages.get("evidence-audit", {}).get("observations", [])
                            if item["stance"] == "supports"
                        }
                    )
                    if outcome == "accepted"
                    else [],
                }
            )
    elapsed = time.perf_counter() - started
    counts = Counter(row["new_decision"] for row in rows)
    accepted = counts["accepted"]
    model_elapsed = sum(row["model_elapsed_seconds"] for row in rows)
    measured_total = elapsed + model_elapsed
    accepted_durations = [
        row["replay_processing_seconds"] + row["model_elapsed_seconds"]
        for row in rows
        if row["new_decision"] == "accepted"
    ]
    return {
        "schema_version": 1,
        "sample_manifest": str(manifest.relative_to(root)),
        "sample_size": len(rows),
        "original_distribution": {"accepted": 0, "hold": 26, "rejected": 0},
        "new_distribution": {key: counts[key] for key in ("accepted", "hold", "rejected")},
        "full_replay_wall_clock_seconds": round(elapsed, 3),
        "recorded_model_elapsed_seconds": round(model_elapsed, 3),
        "combined_observed_seconds_sequential_equivalent": round(measured_total, 3),
        "historical_source_research_seconds": None,
        "accepted_cards_per_hour_observed": round(accepted * 3600 / measured_total, 3)
        if measured_total
        else 0,
        "seconds_per_accepted_card": round(measured_total / accepted, 3) if accepted else None,
        "accepted_candidate_processing_seconds_mean": round(statistics.mean(accepted_durations), 3)
        if accepted_durations
        else None,
        "accepted_candidate_processing_seconds_median": round(
            statistics.median(accepted_durations), 3
        )
        if accepted_durations
        else None,
        "cache_hits_before_provider": initial_hits,
        "cache_misses_before_provider": initial_misses,
        "cache_records_added": new_cache_records,
        "unresolved_evidence_queries_after_provider": remaining_misses,
        "external_live_retrievals": 0,
        "archived_observations_imported": len(archived),
        "inspected_capture_records_imported": len(captured),
        "model_calls": sum(row["model_calls"] for row in rows),
        "input_tokens": sum(row["input_tokens"] or 0 for row in rows),
        "output_tokens": sum(row["output_tokens"] or 0 for row in rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verifier-results",
        type=Path,
        default=Path("specs/003-vocabulary-curation/evidence-verifier-results.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/003-vocabulary-curation/historical-evidence-replay.json"),
    )
    args = parser.parse_args()
    result = run(Path.cwd(), verifier_path=args.verifier_results)
    atomic_json(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
