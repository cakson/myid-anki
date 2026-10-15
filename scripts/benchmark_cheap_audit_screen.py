#!/usr/bin/env python3
"""Run one frozen, batched Luna audit-screen contract on historical ACCEPTs."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from compare_historical_verifiers import call_model

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
COHORT = SPEC / "operational-audit-cohort.json"
INPUTS = SPEC / "cheap-audit-screen-inputs.json"
LABELS = SPEC / "cheap-audit-screen-labels.json"
PROMPT = SPEC / "cheap-audit-screen-contract.md"
MODEL = "gpt-5.6-luna"
REASONS = {
    "semantic-precision",
    "answer-naturalness",
    "everyday-usage",
    "hidden-alternative",
    "cue-ambiguity",
}
SIZES = (5, 10, 20)
STATES = {
    "fresh1": "fresh-batch-50-state.json",
    "fresh2": "second-batch-50-state.json",
    "fresh3": "final-calibration-50-state.json",
    "prospective50": "prospective-preference-50-enriched-state.json",
    "technical25": "technical-borrowing-25-enriched-state.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare() -> None:
    if INPUTS.exists() or LABELS.exists():
        if not INPUTS.exists() or not LABELS.exists():
            raise ValueError("partial frozen screen benchmark")
        if json.loads(LABELS.read_text())["input_digest"] != digest(INPUTS):
            raise ValueError("frozen screen inputs changed")
        print("frozen", len(json.loads(INPUTS.read_text())["items"]))
        return
    cohort = json.loads(COHORT.read_text())["records"]
    states = {batch: json.loads((SPEC / name).read_text()) for batch, name in STATES.items()}
    items = []
    labels = {}
    for ref, record in sorted(cohort.items()):
        if record["audit_category"] is None:
            continue
        row = states[record["batch"]]["candidate_decisions"][ref]
        candidate = row["candidate"]
        items.append(
            {
                "ref": ref,
                "english": candidate["english"],
                "indonesian": candidate["indonesian"],
                "malaysian": candidate["malaysian"],
                "sense": candidate["sense"],
                "relation": row["relation"],
            }
        )
        labels[ref] = {
            "batch": record["batch"],
            "category": record["audit_category"],
            "verdict": record["audit_label"],
            "deterministic_reasons": record["deterministic_reasons"],
        }
    if len(items) != 153:
        raise ValueError(f"unexpected audited ACCEPT count: {len(items)}")
    atomic_json(
        INPUTS,
        {
            "schema_version": 1,
            "cohort_digest": digest(COHORT),
            "purpose": "pre-audit card fields only; model runner never reads labels",
            "items": items,
        },
    )
    atomic_json(
        LABELS,
        {
            "schema_version": 1,
            "input_digest": digest(INPUTS),
            "labels": labels,
        },
    )
    print("prepared", len(items))


def validate(raw: dict, refs: set[str]) -> dict:
    if not isinstance(raw, dict) or set(raw) != {"items"} or not isinstance(raw["items"], dict):
        raise ValueError("invalid top-level output")
    if set(raw["items"]) != refs:
        raise ValueError("screen response refs differ from request")
    for ref, item in raw["items"].items():
        if not isinstance(item, dict) or set(item) != {"decision", "reasons"}:
            raise ValueError(f"invalid item shape: {ref}")
        decision, reasons = item["decision"], item["reasons"]
        if decision not in {"screen-clear", "screen-review"}:
            raise ValueError(f"invalid decision: {ref}")
        if not isinstance(reasons, list) or not set(reasons) <= REASONS:
            raise ValueError(f"invalid reasons: {ref}")
        if (decision == "screen-review") != bool(reasons):
            raise ValueError(f"decision and reasons disagree: {ref}")
    return raw["items"]


def prompt_for(group: list[dict]) -> str:
    return (
        PROMPT.read_text()
        + "\nCards:\n"
        + json.dumps(group, ensure_ascii=False, separators=(",", ":"))
    )


def run_group(size: int, index: int, group: list[dict]) -> tuple[int, dict, dict | None]:
    prompt = prompt_for(group)
    with tempfile.TemporaryDirectory(prefix="myid-cheap-screen-") as temp:
        attempt = call_model(
            ROOT,
            Path(temp),
            f"screen:{size}:{index}",
            MODEL,
            prompt,
            reasoning_effort="low",
        )
    metric = {k: v for k, v in attempt.items() if k not in {"decision", "response_text"}}
    metric.update(
        {
            "size": size,
            "group": index,
            "cards": len(group),
            "prompt_digest": hashlib.sha256(prompt.encode()).hexdigest(),
        }
    )
    if attempt["status"] != "complete":
        return index, metric, None
    try:
        parsed = validate(attempt["decision"], {item["ref"] for item in group})
    except (ValueError, TypeError) as exc:
        metric["status"] = "malformed"
        metric["error_summary"] = str(exc)
        return index, metric, None
    return index, metric, parsed


def run(size: int, workers: int) -> None:
    if size not in SIZES:
        raise ValueError(size)
    if json.loads(LABELS.read_text())["input_digest"] != digest(INPUTS):
        raise ValueError("input digest differs from sealed label artifact")
    source = json.loads(INPUTS.read_text())
    result_path = SPEC / f"cheap-audit-screen-{size}-results.json"
    if result_path.exists():
        artifact = json.loads(result_path.read_text())
        if artifact["input_digest"] != digest(INPUTS) or artifact["prompt_digest"] != digest(
            PROMPT
        ):
            raise ValueError("frozen screen input or prompt changed")
    else:
        artifact = {
            "schema_version": 1,
            "model": MODEL,
            "reasoning_effort": "low",
            "batch_size": size,
            "input_digest": digest(INPUTS),
            "prompt_digest": digest(PROMPT),
            "attempts": [],
            "results": {},
        }
        atomic_json(result_path, artifact)
    groups = [
        (index // size, source["items"][index : index + size])
        for index in range(0, len(source["items"]), size)
    ]
    pending = [
        (index, group)
        for index, group in groups
        if not all(item["ref"] in artifact["results"] for item in group)
    ]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_group, size, index, group): index for index, group in pending}
        for future in as_completed(futures):
            index, metric, parsed = future.result()
            artifact["attempts"].append(metric)
            if parsed:
                artifact["results"].update(parsed)
            atomic_json(result_path, artifact)
            print(size, index, metric["status"], len(parsed or {}), flush=True)
    if len(artifact["results"]) != len(source["items"]):
        raise RuntimeError(f"incomplete screen size {size}: {len(artifact['results'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run"))
    parser.add_argument("--size", type=int, choices=SIZES)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    elif args.size is None:
        parser.error("run requires --size")
    else:
        run(args.size, args.workers)


if __name__ == "__main__":
    main()
