#!/usr/bin/env python3
"""Read-only, bounded policy-v2 replay of frozen historical hold IDs.

Copies batch artifacts before packet reconstruction because old archive snapshots may be
materialized during replay. No candidate is regenerated or promoted.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path

from indo_malay_anki.curation.gate import decide_candidate
from indo_malay_anki.curation.store import BatchStore
from indo_malay_anki.curation.workflow import current_results


def run(root: Path, sample_path: Path) -> dict:
    sample_path = sample_path.resolve()
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    refs = sample["candidate_refs"]
    if len(refs) != len(set(refs)) or not 20 <= len(refs) <= 30:
        raise ValueError("sample must have 20–30 distinct candidate references")
    with tempfile.TemporaryDirectory(prefix="myid-hold-replay-") as temporary:
        mirror = Path(temporary)
        shutil.copytree(root / "curation" / "batches", mirror / "curation" / "batches")
        (mirror / "data").mkdir()
        shutil.copy2(root / "data" / "vocabulary.tsv", mirror / "data" / "vocabulary.tsv")
        rows = []
        for ref in refs:
            batch_id, candidate_id = ref.split(":", 1)
            if batch_id == "growth-audit-001":
                raise ValueError("process fixture must not enter product sample")
            store = BatchStore(mirror, batch_id)
            archived = json.loads((store.path / "report.json").read_text(encoding="utf-8"))
            prior = next(
                (item for item in archived["decisions"] if item["candidate_id"] == candidate_id),
                None,
            )
            if prior is None or prior["outcome"] != "hold":
                raise ValueError(f"sample is not an archived hold: {ref}")
            started = time.perf_counter_ns()
            candidate = store.candidate(candidate_id)
            stages = current_results(store, candidate_id)
            revised = decide_candidate(candidate, stages, policy_version="2.0.0")
            replay_ms = (time.perf_counter_ns() - started) / 1_000_000
            outcome = "hold" if revised["outcome"] == "pending" else revised["outcome"]
            original_events = store.events(candidate_id)
            rows.append(
                {
                    "candidate_ref": ref,
                    "english": candidate["english"],
                    "indonesian": candidate["indonesian"],
                    "malaysian": candidate["malaysian"],
                    "original_decision": prior["outcome"],
                    "original_reason_codes": prior.get("reason_codes", []),
                    "new_decision": outcome,
                    "raw_gate_outcome": revised["outcome"],
                    "risk_tier": revised["risk"]["path"],
                    "fast_path_used": (
                        outcome == "accepted" and revised["risk"]["path"] == "ordinary-fast"
                    ),
                    "escalation_occurred": revised["risk"]["path"] in {"escalated", "false-friend"},
                    "escalation_reasons": revised["risk"]["triggers"],
                    "final_decision_reasons": revised["reason_codes"],
                    "reused_stages": list(stages),
                    "historical_candidate_stage_events": len(original_events),
                    "new_evidence_retrieval_count": 0,
                    "new_model_call_count": 0,
                    "new_verifier_call_count": 0,
                    "new_adversarial_review_count": 0,
                    "new_retry_count": 0,
                    "policy_replay_elapsed_ms": round(replay_ms, 3),
                    "observed_experiment_elapsed_ms": round(replay_ms, 3),
                    "full_curation_elapsed_ms": None,
                    "historical_evidence_retrieval_count": None,
                    "historical_model_call_count": None,
                    "historical_verifier_call_count": None,
                    "historical_adversarial_review_count": None,
                    "historical_retry_count": None,
                    "new_input_tokens": 0,
                    "new_output_tokens": 0,
                    "approximate_cost": None,
                }
            )
    comparison_path = root / "specs/003-vocabulary-curation/historical-model-comparison.json"
    if comparison_path.exists() and comparison_path.stat().st_size:
        comparisons = json.loads(comparison_path.read_text(encoding="utf-8"))["results"]
        by_ref = {row["candidate_ref"]: row for row in rows}
        for ref, row in by_ref.items():
            attempts = [item for item in comparisons if item["candidate_ref"] == ref]
            successful = [item for item in attempts if item["status"] == "complete"]
            row["new_model_call_count"] = len(successful)
            row["new_verifier_call_count"] = len(successful)
            row["new_retry_count"] = len(attempts) - len(successful)
            row["failed_tool_attempt_count"] = len(attempts) - len(successful)
            row["model_comparison_elapsed_ms"] = round(
                1000 * sum(item["elapsed_seconds"] for item in attempts), 3
            )
            row["observed_experiment_elapsed_ms"] = round(
                row["policy_replay_elapsed_ms"] + row["model_comparison_elapsed_ms"], 3
            )
            if any(item["input_tokens"] is None for item in successful):
                row["new_input_tokens"] = None
            else:
                row["new_input_tokens"] = sum(item["input_tokens"] for item in successful)
            if any(item["output_tokens"] is None for item in successful):
                row["new_output_tokens"] = None
            else:
                row["new_output_tokens"] = sum(item["output_tokens"] for item in successful)
            row["model_comparison_only"] = bool(attempts)
    counts = Counter(row["new_decision"] for row in rows)
    risks = Counter(row["risk_tier"] for row in rows)
    return {
        "schema_version": 1,
        "sample_manifest": str(sample_path.relative_to(root)),
        "sample_size": len(rows),
        "original_distribution": {"accepted": 0, "hold": len(rows), "rejected": 0},
        "new_distribution": {key: counts[key] for key in ("accepted", "hold", "rejected")},
        "risk_distribution": dict(sorted(risks.items())),
        "new_model_calls": sum(row["new_model_call_count"] for row in rows),
        "new_evidence_retrievals": 0,
        "failed_tool_attempts": sum(row.get("failed_tool_attempt_count", 0) for row in rows),
        "historical_usage_available": False,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        type=Path,
        default=Path("specs/003-vocabulary-curation/historical-hold-sample.json"),
    )
    args = parser.parse_args()
    print(json.dumps(run(Path.cwd(), args.sample), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
