#!/usr/bin/env python3
"""Bounded policy-v3 replay of the frozen 26 historical holds; never exports cards."""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import tempfile
import time
from collections import Counter
from pathlib import Path

from compare_historical_verifiers import call_model

from indo_malay_anki.curation.gate import decide_candidate
from indo_malay_anki.curation.packets import make_packet
from indo_malay_anki.curation.records import RecordError, validate_stage_response
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results

PROMPT_VERSION = "2.0.0"
BATCH_SIZE = 5


def _latest_objection(store: BatchStore, candidate_id: str) -> dict:
    return next(
        (
            event["result"]
            for event in reversed(store.events(candidate_id))
            if event.get("role") == "adversarial-review"
            and event.get("status") == "complete"
            and event.get("result", {}).get("verdict") == "object"
        ),
        {},
    )


def _packet(store: BatchStore, candidate_id: str, stages: dict) -> dict:
    context = dict(stages)
    objection = _latest_objection(store, candidate_id)
    if objection:
        context["adversarial-review"] = objection
    return make_packet(
        store.root,
        store.manifest(),
        "independent-verification",
        candidate=store.candidate(candidate_id),
        stages=context,
        prompt_set_version=PROMPT_VERSION,
    )


def _verify_group(root: Path, workdir: Path, group: list[dict], model: str) -> dict:
    prompt = (
        "Independently verify each Indonesian–Malaysian Malay candidate in the JSON array. "
        "The proposed relation is provisional. Use your linguistic knowledge for ordinary "
        "common vocabulary; external research is not required absent a concrete concern. "
        "For each candidate, decide whether the cue, both normal forms, and useful relation "
        "are publishable. A named synonym, missing frequency proof, or generic uncertainty "
        "is nonblocking; a specific plausible rival/preference that would materially misteach "
        "is blocking. Assess every historical objection by exact text, marking material true "
        "only if a concrete learner risk remains. Confirmed identical ordinary forms are "
        "outside the deck; a possible false friend needs stronger review. Never approve to "
        "raise the acceptance count. Do not call tools or browse. Return JSON only with "
        "key `items`, one per input candidate_ref, each containing candidate_ref and result. "
        "Each result has verdict (`agree` or `object`), relation (`same`, `similar`, "
        "`different-common-word`, or `false-friend`), concerns (nonblocking caveats), "
        "material_concerns (concrete unresolved learner risks), rationale, and "
        "objection_assessments (one exact objection, boolean material, concise resolution "
        "for each historical objection). Optional affirmative_defect must be one of "
        "confirmed-duplicate, confirmed-semantic-mismatch, incorrect-translation, "
        "confirmed-misleading-usage, artificial-synonym, low-learning-value, "
        "false-friend-disproved. No other fields are needed.\n"
        + json.dumps(group, ensure_ascii=False, separators=(",", ":"))
    )
    return call_model(root, workdir, "group:" + group[0]["candidate_ref"], model, prompt)


def run(root: Path, output: Path, *, invoke_model: bool = True) -> dict:
    sample = json.loads(
        (root / "specs/003-vocabulary-curation/historical-hold-sample.json").read_text()
    )
    refs = sample["candidate_refs"]
    if len(refs) != 26 or len(set(refs)) != 26:
        raise ValueError("frozen historical sample must contain exactly 26 distinct IDs")
    config = json.loads((root / "curation/config.json").read_text())
    model = config["role_models"]["independent-verification"]["model"]
    state = (
        json.loads(output.read_text())
        if output.exists()
        else {
            "schema_version": 1,
            "prompt_version": PROMPT_VERSION,
            "model": model,
            "candidate_refs": refs,
            "attempts": [],
            "verifier_results": {},
        }
    )
    if state["candidate_refs"] != refs or state["prompt_version"] != PROMPT_VERSION:
        raise ValueError("existing replay artifact does not match frozen inputs")
    began = time.perf_counter()
    earlier_attempts = len(state["attempts"])
    with tempfile.TemporaryDirectory(prefix="myid-optimistic-replay-") as temp:
        mirror = Path(temp)
        shutil.copytree(root / "curation" / "batches", mirror / "curation" / "batches")
        (mirror / "data").mkdir()
        shutil.copy2(root / "data" / "vocabulary.tsv", mirror / "data" / "vocabulary.tsv")
        packets = []
        for ref in refs:
            batch_id, candidate_id = ref.split(":", 1)
            store = BatchStore(mirror, batch_id)
            stages = current_results(store, candidate_id)
            stages.pop("independent-verification", None)
            stages.pop("adversarial-review", None)
            objection = _latest_objection(store, candidate_id)
            if objection:
                stages["adversarial-review"] = objection
            early = decide_candidate(store.candidate(candidate_id), stages, policy_version="3.0.0")
            if early["outcome"] == "rejected":
                continue
            if ref not in state["verifier_results"]:
                packet = _packet(store, candidate_id, stages)
                packets.append(
                    {
                        "candidate_ref": ref,
                        "input_digest": packet["input_digest"],
                        "context": packet["context"],
                    }
                )
        if invoke_model:
            for offset in range(0, len(packets), BATCH_SIZE):
                group = packets[offset : offset + BATCH_SIZE]
                with tempfile.TemporaryDirectory(prefix="myid-luna-verifier-") as call_temp:
                    attempt = _verify_group(root, Path(call_temp), group, model)
                state["attempts"].append(
                    {
                        key: value
                        for key, value in attempt.items()
                        if key not in {"response_text", "decision"}
                    }
                )
                if attempt["status"] == "complete":
                    by_ref = {
                        item.get("candidate_ref"): item.get("result")
                        for item in attempt["decision"].get("items", [])
                        if isinstance(item, dict)
                    }
                    for packet in group:
                        ref = packet["candidate_ref"]
                        raw = by_ref.get(ref)
                        if not isinstance(raw, dict):
                            continue
                        try:
                            validate_stage_response(
                                "independent-verification",
                                {
                                    "schema_version": 1,
                                    "role": "independent-verification",
                                    "model": model,
                                    "result": raw,
                                },
                            )
                        except RecordError:
                            continue
                        state["verifier_results"][ref] = {
                            "input_digest": packet["input_digest"],
                            "result": raw,
                            "model": model,
                            "prompt_version": PROMPT_VERSION,
                        }
                atomic_json(output, state)
                print(f"verified {len(state['verifier_results'])}/{len(packets)}", flush=True)
        rows = []
        for ref in refs:
            batch_id, candidate_id = ref.split(":", 1)
            store = BatchStore(mirror, batch_id)
            stages = current_results(store, candidate_id)
            stages.pop("independent-verification", None)
            stages.pop("adversarial-review", None)
            objection = _latest_objection(store, candidate_id)
            if objection:
                stages["adversarial-review"] = objection
            verified = state["verifier_results"].get(ref)
            if verified:
                packet = _packet(store, candidate_id, stages)
                if verified["input_digest"] == packet["input_digest"]:
                    stages["independent-verification"] = verified["result"]
            decision = decide_candidate(
                store.candidate(candidate_id), stages, policy_version="3.0.0"
            )
            rows.append(
                {
                    "candidate_ref": ref,
                    "candidate": store.candidate(candidate_id),
                    "outcome": decision["outcome"],
                    "relation": decision["relation"],
                    "risk": decision["risk"],
                    "reason_codes": decision["reason_codes"],
                    "confidence_tier": decision.get("confidence_tier"),
                    "confidence_rationale": decision.get("confidence_rationale"),
                    "review_flags": decision.get("review_flags", []),
                    "verifier_reused": bool(verified),
                    "evidence_reused": len(
                        stages.get("evidence-audit", {}).get("observations", [])
                    ),
                }
            )
    current_elapsed = time.perf_counter() - began
    prior_call_seconds = sum(
        item["elapsed_seconds"] for item in state["attempts"][:earlier_attempts]
    )
    elapsed = current_elapsed + prior_call_seconds
    outcomes = Counter(row["outcome"] for row in rows)
    accepted = outcomes["accepted"]
    tokens = [
        item["input_tokens"]
        for item in state["attempts"]
        if item.get("status") == "complete" and item.get("input_tokens") is not None
    ]
    report = {
        "schema_version": 1,
        "candidate_refs": refs,
        "total_candidates": len(rows),
        "outcomes": dict(outcomes),
        "no_contrast_rejects": sum(
            "no-meaningful-cross-language-contrast" in row["reason_codes"] for row in rows
        ),
        "fast_path_accepts": sum(
            row["outcome"] == "accepted" and row["risk"]["path"] == "ordinary-fast" for row in rows
        ),
        "escalated_accepts": sum(
            row["outcome"] == "accepted" and row["risk"]["path"] != "ordinary-fast" for row in rows
        ),
        "confidence_distribution": dict(
            Counter(row["confidence_tier"] for row in rows if row["confidence_tier"])
        ),
        "verifier_calls": sum(item.get("status") == "complete" for item in state["attempts"]),
        "verifier_attempts": len(state["attempts"]),
        "failed_verifier_launches": sum(
            item.get("status") != "complete" for item in state["attempts"]
        ),
        "average_verifier_input_tokens": statistics.mean(tokens) if tokens else None,
        "median_verifier_input_tokens": statistics.median(tokens) if tokens else None,
        "total_elapsed_seconds": round(elapsed, 3),
        "accepted_cards_per_hour": round(3600 * accepted / elapsed, 3) if elapsed else None,
        "fast_path_utilization_rate": (
            sum(
                row["outcome"] == "accepted" and row["risk"]["path"] == "ordinary-fast"
                for row in rows
            )
            / sum(
                "no-meaningful-cross-language-contrast" not in row["reason_codes"] for row in rows
            )
        ),
        "canonical_promotions": 0,
        "rows": rows,
    }
    atomic_json(output.with_name("optimistic-replay-report.json"), report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/003-vocabulary-curation/optimistic-verifier-results.json"),
    )
    parser.add_argument("--no-model", action="store_true")
    args = parser.parse_args()
    report = run(Path.cwd(), args.output.resolve(), invoke_model=not args.no_model)
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
