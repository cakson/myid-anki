"""Read-only replay of the completed Feature 004 batch for orchestration experiments.

Writes only below curation/efficiency-replays. It never ingests a response or exports cards.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from indo_malay_anki.curation.gate import decide_candidate
from indo_malay_anki.curation.records import validate_stage_response
from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json
from indo_malay_anki.curation.workflow import current_results, packet_for
from indo_malay_anki.scaling.audit import _validate_response as validate_audit_response
from indo_malay_anki.scaling.prompt_transport import compact_overlap_prompt
from indo_malay_anki.scaling.provider import call_model

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "curation/production-runs/corpus-004-001"
OUT = ROOT / "curation/efficiency-replays/corpus-004-001-v1"
FIXED_SHA256 = {
    ROOT
    / "data/vocabulary.tsv": "6de5367ccecb4178db89d59f0577286d1b95893dcdcc4e27c49c91d115512f5d",
    ROOT
    / "curation/id-ledger.json": "318f7694a5c7e670547b8d5c71c3fa16b19d9e99d625632f786ec08d16c436c8",
    RUN / "report.json": "7c0caa6435d685ba1fb6c8f7cf03a5158b5535ad33e1035aea03c3f80d125119",
}


def preflight() -> None:
    for path, expected in FIXED_SHA256.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"fixed benchmark artifact changed: {path}")
    for path in _captures("normalize-and-dedupe"):
        store = BatchStore(ROOT, path.parent.parent.name)
        snapshot = store.candidate_path(path.parent.name) / "archive-snapshot.json"
        if not snapshot.exists() and not (store.path / "archive-snapshot.json").exists():
            raise RuntimeError(f"missing frozen archive snapshot: {path}")


def _captures(role: str) -> list[Path]:
    return sorted((RUN / "curation-responses").glob(f"*/*/{role}.json"))


def _packet(path: Path, role: str) -> dict:
    return packet_for(BatchStore(ROOT, path.parent.parent.name), role, path.parent.name)


def _summary(rows: list[dict]) -> dict:
    return {
        "calls": len(rows),
        "input_tokens": sum(row["input_tokens"] for row in rows),
        "output_tokens": sum(row["output_tokens"] for row in rows),
        "elapsed_ms": sum(row["elapsed_ms"] for row in rows),
        "mean_input_per_call": round(statistics.mean(row["input_tokens"] for row in rows), 1),
        "median_input_per_call": statistics.median(row["input_tokens"] for row in rows),
        "mean_output_per_call": round(statistics.mean(row["output_tokens"] for row in rows), 1),
        "median_output_per_call": statistics.median(row["output_tokens"] for row in rows),
    }


def profile() -> dict:
    result = {}
    report = read_json(RUN / "report.json")
    for role in ("normalize-and-dedupe", "independent-verification"):
        paths = _captures(role)
        rows = [read_json(path) for path in paths]
        packets = [_packet(path, role) for path in paths]
        stage = _summary(rows)
        stage["candidates"] = len(paths)
        stage["mean_input_per_candidate"] = round(stage["input_tokens"] / len(paths), 1)
        stage["mean_packet_bytes"] = round(
            statistics.mean(len(json.dumps(p, ensure_ascii=False).encode()) for p in packets)
        )
        stage["mean_prompt_bytes"] = round(
            statistics.mean(len(p["prompt"].encode()) for p in packets)
        )
        stage["mean_archive_bytes"] = round(
            statistics.mean(
                len(json.dumps(p["context"].get("archive", []), ensure_ascii=False).encode())
                for p in packets
            )
        )
        stage["mean_archive_entries"] = round(
            statistics.mean(len(p["context"].get("archive", [])) for p in packets), 1
        )
        stage["mean_candidate_bytes"] = round(
            statistics.mean(
                len(json.dumps(p["context"]["candidate"], ensure_ascii=False).encode())
                for p in packets
            )
        )
        stage["mean_deterministic_overlap_bytes"] = round(
            statistics.mean(
                len(
                    json.dumps(
                        p["context"].get("deterministic_overlaps", []), ensure_ascii=False
                    ).encode()
                )
                for p in packets
            )
        )
        stage["mean_evidence_bytes"] = round(
            statistics.mean(
                len(
                    json.dumps(
                        p["context"].get("audited_evidence", []), ensure_ascii=False
                    ).encode()
                )
                for p in packets
            )
        )
        result[role] = stage
    audit_paths = sorted((RUN / "audits").glob("*/*.response.json"))
    audit_rows = [read_json(path) for path in audit_paths]
    result["risk-audit"] = _summary(audit_rows)
    result["risk-audit"]["candidates"] = len(audit_paths)
    result["risk-audit"]["mean_input_per_candidate"] = result["risk-audit"]["mean_input_per_call"]
    result["risk-audit"]["mean_packet_bytes"] = round(
        statistics.mean(
            len(path.with_name(path.name.replace(".response.json", ".packet.json")).read_bytes())
            for path in audit_paths
        )
    )
    result["risk-audit"]["mean_decision_bytes"] = round(
        statistics.mean(
            len(
                json.dumps(
                    read_json(path.with_name(path.name.replace(".response.json", ".packet.json")))[
                        "decision"
                    ],
                    ensure_ascii=False,
                ).encode()
            )
            for path in audit_paths
        )
    )
    stage_paths = {
        "generation": [
            path
            for path in (RUN / "generation-responses").glob("*.json")
            if read_json(path).get("input_tokens")
        ],
        "semantic_review": list((RUN / "generation-responses/semantic").glob("*.json")),
        "random_qa": list((RUN / "qa/findings").glob("*.response.json")),
    }
    failed_paths = {
        "generation": list((RUN / "generation-responses/failed").glob("*.json")),
        "random_qa": list((RUN / "qa/findings/failed").glob("*.json")),
    }
    denominators = {
        "generation": report["proposed_count"],
        "semantic_review": 14,
        "random_qa": report["qa"]["reviewed_count"],
    }
    for stage, paths in stage_paths.items():
        rows = [read_json(path) for path in paths]
        target = report["work"][stage]
        missing_input = target["input_tokens"] - sum(row["input_tokens"] for row in rows)
        missing_output = target["output_tokens"] - sum(row["output_tokens"] for row in rows)
        for path in failed_paths.get(stage, []):
            row = read_json(path)
            if (row.get("input_tokens"), row.get("output_tokens")) == (
                missing_input,
                missing_output,
            ):
                rows.append(row)
                break
        result[stage] = _summary(rows)
        result[stage]["candidates"] = denominators[stage]
        result[stage]["mean_input_per_candidate"] = round(
            result[stage]["input_tokens"] / denominators[stage], 1
        )
    result["total"] = {
        key: sum(
            item.get(key, 0) or 0 for item in report["work"].values() if isinstance(item, dict)
        )
        for key in ("model_calls", "input_tokens", "output_tokens")
    }
    atomic_json(OUT / "profile.json", result)
    return result


def _compact_verification(packet: dict) -> dict:
    return {
        "candidate_id": packet["candidate_id"],
        "input_digest": packet["input_digest"],
        "context": packet["context"],
    }


def _audit_packet(path: Path) -> dict:
    return read_json(path.with_name(path.name.replace(".response.json", ".packet.json")))


def _run(label: str, role: str, prompt: str, ids: list[str]) -> dict:
    path = OUT / "captures" / f"{label}.json"
    prompt_sha256 = hashlib.sha256(prompt.encode()).hexdigest()
    if path.exists():
        existing = read_json(path)
        if existing["candidate_ids"] != ids:
            raise ValueError(f"stale replay capture {label}")
        if existing.get("prompt_sha256", prompt_sha256) != prompt_sha256 or existing.get(
            "prompt_bytes"
        ) != len(prompt.encode()):
            raise ValueError(f"stale replay prompt {label}")
        return existing
    answer = call_model(ROOT, role, prompt, timeout_seconds=300)
    capture = {
        "candidate_ids": ids,
        "prompt_bytes": len(prompt.encode()),
        "prompt_sha256": prompt_sha256,
        **answer,
    }
    atomic_json(path, capture)
    return capture


def experiment() -> dict:
    """Bounded fixed-candidate trials; baseline size-one calls are already saved."""
    norm_paths = _captures("normalize-and-dedupe")[:10]
    verify_paths = _captures("independent-verification")[:10]
    audit_paths = sorted((RUN / "audits").glob("*/*.response.json"))[:10]
    result: dict = {"normalize": [], "verification": [], "audit": []}
    for index, path in enumerate(norm_paths):
        packet = _packet(path, "normalize-and-dedupe")
        capture = _run(
            f"normalize-compact-{index:02d}",
            "normalize-and-dedupe",
            compact_overlap_prompt(packet),
            [packet["candidate_id"]],
        )
        result["normalize"].append(
            {
                "candidate_id": packet["candidate_id"],
                "capture": str(OUT / "captures" / f"normalize-compact-{index:02d}.json"),
                "input_tokens": capture["input_tokens"],
                "output_tokens": capture["output_tokens"],
            }
        )
    for size in (5, 10):
        for start in range(0, 10, size):
            group = verify_paths[start : start + size]
            packets = [_packet(path, "independent-verification") for path in group]
            ids = [packet["candidate_id"] for packet in packets]
            prompt = (
                packets[0]["prompt"] + "\nReview each candidate independently. "
                'Return JSON only: {"results":[{"candidate_id":"...",'
                '"response":{all required verifier fields}}]}. '
                "Include each ID exactly once. "
                "Do not transfer judgments between candidates.\nCURATION_PACKETS_JSON\n"
                + json.dumps(
                    [_compact_verification(packet) for packet in packets],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            capture = _run(
                f"verification-{size}-{start:02d}", "independent-verification", prompt, ids
            )
            result["verification"].append(
                {
                    "size": size,
                    "candidate_ids": ids,
                    "input_tokens": capture["input_tokens"],
                    "output_tokens": capture["output_tokens"],
                    "elapsed_ms": capture["elapsed_ms"],
                }
            )
    audit_instruction = (
        "Independent risk audit of Indonesian versus Malaysian Malay learner cards. "
        "Review every card independently of production verification and every other card. "
        "Check both answers, English cue and sense, final relation, and any false-friend contrast. "
        'Return JSON only: {"results":[{"candidate_id":"...",'
        '"response":{"schema_version":1,"verdict":"cleared|needs-correction|withheld",'
        '"finding_class":"none|learner-critical-answer|cue-content|metadata-only",'
        '"rationale":"...","claim_reviews":[{"subject":"...","conclusion":"...",'
        '"material_risk":false,"evidence_refs":[],"evidence_limitation":"..."}]}}]}. '
        "Include each ID exactly once. A material risk cannot be cleared.\nAUDIT_PACKETS_JSON\n"
    )
    for size in (2, 5):
        for start in range(0, 10, size):
            group = audit_paths[start : start + size]
            packets = [_audit_packet(path) for path in group]
            ids = [packet["candidate_id"] for packet in packets]
            prompt = audit_instruction + json.dumps(
                packets, ensure_ascii=False, separators=(",", ":")
            )
            capture = _run(f"audit-{size}-{start:02d}", "independent-verification", prompt, ids)
            result["audit"].append(
                {
                    "size": size,
                    "candidate_ids": ids,
                    "input_tokens": capture["input_tokens"],
                    "output_tokens": capture["output_tokens"],
                    "elapsed_ms": capture["elapsed_ms"],
                }
            )
    atomic_json(OUT / "experiment.json", result)
    return result


def full_normalize() -> dict:
    """Replay the full fixed normalization stage, checkpointing each candidate."""

    def one(index_path: tuple[int, Path]) -> tuple[str, dict]:
        index, path = index_path
        packet = _packet(path, "normalize-and-dedupe")
        label = (
            f"normalize-compact-{index:02d}"
            if index < 10
            else f"full-normalize-{path.parent.parent.name}-{path.parent.name}"
        )
        capture = _run(
            label, "normalize-and-dedupe", compact_overlap_prompt(packet), [packet["candidate_id"]]
        )
        return packet["candidate_id"], {
            key: capture.get(key)
            for key in ("input_tokens", "output_tokens", "elapsed_ms", "prompt_sha256")
        }

    completed = {}
    errors = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            pool.submit(one, (index, path)): path
            for index, path in enumerate(_captures("normalize-and-dedupe"))
        }
        for future in as_completed(futures):
            path = futures[future]
            try:
                candidate_id, usage = future.result()
                completed[candidate_id] = usage
            except Exception as exc:  # preserve other completed replays
                errors[str(path)] = str(exc)
    result = {"completed": completed, "errors": errors}
    atomic_json(OUT / "full-normalize.json", result)
    return {
        "completed_count": len(completed),
        "error_count": len(errors),
        "input_tokens": sum(row["input_tokens"] or 0 for row in completed.values()),
        "output_tokens": sum(row["output_tokens"] or 0 for row in completed.values()),
        "elapsed_ms": sum(row["elapsed_ms"] or 0 for row in completed.values()),
        "errors": errors,
    }


def _decision(store: BatchStore, candidate_id: str, stages: dict) -> dict:
    explicit = next(
        (
            event
            for event in reversed(store.events(candidate_id))
            if event.get("role") == "explicit-final"
        ),
        None,
    )
    return decide_candidate(
        store.candidate(candidate_id),
        stages,
        explicit_final=explicit.get("decision") if explicit else None,
        policy_version="3.1.0",
    )


def _cue(store: BatchStore, candidate_id: str, decision: dict) -> str:
    return decision.get("cue_correction", {}).get("to") or store.candidate(candidate_id)["english"]


def compare() -> dict:
    """Compare every saved replay capture to immutable first-batch decisions."""
    changes: list[dict] = []
    validation_errors: list[dict] = []
    counts = {
        "normalization": 0,
        "verification_5": 0,
        "verification_10": 0,
        "audit_2": 0,
        "audit_5": 0,
    }
    for index, path in enumerate(_captures("normalize-and-dedupe")):
        label = (
            f"normalize-compact-{index:02d}"
            if index < 10
            else f"full-normalize-{path.parent.parent.name}-{path.parent.name}"
        )
        replay_path = OUT / "captures" / f"{label}.json"
        if not replay_path.exists():
            continue
        store = BatchStore(ROOT, path.parent.parent.name)
        candidate_id = path.parent.name
        response = read_json(replay_path)["response"]
        try:
            result = validate_stage_response("normalize-and-dedupe", response)["result"]
        except Exception as exc:
            validation_errors.append(
                {"stage": "normalization", "candidate_id": candidate_id, "error": str(exc)}
            )
            continue
        stages = current_results(store, candidate_id)
        old = _decision(store, candidate_id, stages)
        new = _decision(store, candidate_id, {**stages, "normalize-and-dedupe": result})
        counts["normalization"] += 1
        changed = [key for key in ("outcome", "relation") if old.get(key) != new.get(key)]
        if _cue(store, candidate_id, old) != _cue(store, candidate_id, new):
            changed.append("resolved_cue")
        if changed:
            changes.append(
                {
                    "stage": "normalization",
                    "size": 1,
                    "slice_id": store.batch_id,
                    "candidate_id": candidate_id,
                    "changed": changed,
                    "baseline": {
                        "outcome": old.get("outcome"),
                        "relation": old.get("relation"),
                        "cue": _cue(store, candidate_id, old),
                    },
                    "replay": {
                        "outcome": new.get("outcome"),
                        "relation": new.get("relation"),
                        "cue": _cue(store, candidate_id, new),
                    },
                    "classification": "quality-regression"
                    if old.get("outcome") == "rejected" and new.get("outcome") != "rejected"
                    else "unresolved",
                }
            )
    for size in (5, 10):
        for path in sorted((OUT / "captures").glob(f"verification-{size}-*.json")):
            capture = read_json(path)
            rows = capture["response"].get("results")
            if not isinstance(rows, list) or sorted(
                row.get("candidate_id") for row in rows
            ) != sorted(capture["candidate_ids"]):
                validation_errors.append(
                    {
                        "stage": "verification",
                        "capture": str(path),
                        "error": "candidate identity/count mismatch",
                    }
                )
                continue
            for row in rows:
                candidate_id = row["candidate_id"]
                original_path = next(
                    (RUN / "curation-responses").glob(
                        f"*/{candidate_id}/independent-verification.json"
                    )
                )
                store = BatchStore(ROOT, original_path.parent.parent.name)
                try:
                    result = validate_stage_response(
                        "independent-verification",
                        {
                            "schema_version": 1,
                            "role": "independent-verification",
                            "model": capture["model"],
                            "result": row["response"],
                        },
                    )["result"]
                except Exception as exc:
                    validation_errors.append(
                        {
                            "stage": "verification",
                            "candidate_id": candidate_id,
                            "size": size,
                            "error": str(exc),
                        }
                    )
                    continue
                stages = current_results(store, candidate_id)
                old = _decision(store, candidate_id, stages)
                new = _decision(store, candidate_id, {**stages, "independent-verification": result})
                counts[f"verification_{size}"] += 1
                changed = [key for key in ("outcome", "relation") if old.get(key) != new.get(key)]
                if _cue(store, candidate_id, old) != _cue(store, candidate_id, new):
                    changed.append("resolved_cue")
                if changed:
                    changes.append(
                        {
                            "stage": "verification",
                            "size": size,
                            "slice_id": store.batch_id,
                            "candidate_id": candidate_id,
                            "changed": changed,
                            "baseline": {
                                "outcome": old.get("outcome"),
                                "relation": old.get("relation"),
                                "cue": _cue(store, candidate_id, old),
                            },
                            "replay": {
                                "outcome": new.get("outcome"),
                                "relation": new.get("relation"),
                                "cue": _cue(store, candidate_id, new),
                            },
                            "classification": "quality-regression"
                            if "outcome" in changed or "resolved_cue" in changed
                            else "unresolved",
                        }
                    )
    for size in (2, 5):
        for path in sorted((OUT / "captures").glob(f"audit-{size}-*.json")):
            capture = read_json(path)
            rows = capture["response"].get("results")
            if not isinstance(rows, list) or sorted(
                row.get("candidate_id") for row in rows
            ) != sorted(capture["candidate_ids"]):
                validation_errors.append(
                    {
                        "stage": "audit",
                        "capture": str(path),
                        "error": "candidate identity/count mismatch",
                    }
                )
                continue
            for row in rows:
                candidate_id = row["candidate_id"]
                try:
                    result = validate_audit_response(row["response"])
                except Exception as exc:
                    validation_errors.append(
                        {
                            "stage": "audit",
                            "candidate_id": candidate_id,
                            "size": size,
                            "error": str(exc),
                        }
                    )
                    continue
                original_path = next((RUN / "audits").glob(f"*/{candidate_id}.response.json"))
                original = read_json(original_path)["response"]
                counts[f"audit_{size}"] += 1
                if (original["verdict"], original["finding_class"]) != (
                    result["verdict"],
                    result["finding_class"],
                ):
                    changes.append(
                        {
                            "stage": "audit",
                            "size": size,
                            "slice_id": original_path.parent.name,
                            "candidate_id": candidate_id,
                            "changed": ["risk_audit_clearance"],
                            "baseline": {
                                "verdict": original["verdict"],
                                "finding_class": original["finding_class"],
                            },
                            "replay": {
                                "verdict": result["verdict"],
                                "finding_class": result["finding_class"],
                            },
                            "classification": "quality-regression"
                            if original["finding_class"]
                            in {"learner-critical-answer", "cue-content", "metadata-only"}
                            and original["finding_class"] != result["finding_class"]
                            else "unresolved",
                        }
                    )
    result = {"valid_counts": counts, "validation_errors": validation_errors, "changes": changes}
    atomic_json(OUT / "comparison.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("profile", "experiment", "full-normalize", "compare"))
    args = parser.parse_args()
    preflight()
    result = {
        "profile": profile,
        "experiment": experiment,
        "full-normalize": full_normalize,
        "compare": compare,
    }[args.command]()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
