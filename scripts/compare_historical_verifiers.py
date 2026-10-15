#!/usr/bin/env python3
"""Bounded, read-only Luna/Sol comparison over identical saved evidence packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results

REFS = (
    "food-001:foods-06",
    "home-001:topic-02",
    "home-001:topic-03",
    "transportation-001:transportation-01",
    "university-001:university-study-03",
)
MODELS = ("gpt-5.6-luna", "gpt-5.6-sol")


def prompt_for(store: BatchStore, candidate_id: str) -> str:
    stages = current_results(store, candidate_id)
    context = {
        "candidate": store.candidate(candidate_id),
        "indonesian_usage": stages.get("indonesian-usage"),
        "malaysian_usage": stages.get("malaysian-usage"),
        "relation_proposal": stages.get("relation-proposal"),
        "audited_observations": stages.get("evidence-audit", {}).get("observations", []),
    }
    return (
        "You are an independent verifier of one Indonesian–Malaysian Malay vocabulary "
        "candidate. Use only the supplied saved evidence; do not call tools, browse, or "
        "assume that a dictionary entry proves everyday preference. Assess the intended "
        "neutral sense, normal usage in each locale, source independence, proposed relation, "
        "and any material contradiction. Distinguish missing support from contrary evidence. "
        "Return exactly one compact JSON object with keys verdict (supported, unresolved, "
        "or defect), relation, concrete_issue, evidence_reason, and would_require_new_evidence "
        "(boolean). Do not accept merely to meet a card target.\n\n"
        + json.dumps(context, ensure_ascii=False, sort_keys=True)
    )


def call_model(
    root: Path,
    temporary: Path,
    ref: str,
    model: str,
    prompt: str,
    *,
    reasoning_effort: str = "medium",
) -> dict:
    codex_bin = os.environ.get(
        "CURATION_CODEX_BIN",
        str(
            Path.home()
            / ".codex/packages/standalone/releases/0.153.0-aarch64-apple-darwin/bin/codex"
        ),
    )
    args = [
        sys.executable,
        str(root / "scripts" / "curation_codex.py"),
        "--codex-bin",
        codex_bin,
        "--",
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "-s",
        "read-only",
        "-C",
        str(temporary),
        "-m",
        model,
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-",
    ]
    began = time.perf_counter()
    try:
        result = subprocess.run(
            args,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        elapsed = round(time.perf_counter() - began, 3)
    except subprocess.TimeoutExpired:
        return {
            "candidate_ref": ref,
            "model": model,
            "status": "timeout",
            "elapsed_seconds": 180,
            "input_tokens": None,
            "output_tokens": None,
            "provider_request_id": None,
            "decision": None,
            "retry_count": 0,
        }
    events = []
    for line in result.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    usage = next(
        (
            item.get("usage", {})
            for item in reversed(events)
            if item.get("type") == "turn.completed"
        ),
        {},
    )
    message = next(
        (
            item.get("item", {}).get("text", "")
            for item in reversed(events)
            if item.get("type") == "item.completed"
            and item.get("item", {}).get("type") == "agent_message"
        ),
        "",
    )
    try:
        decision = json.loads(message)
    except json.JSONDecodeError:
        decision = None
    return {
        "candidate_ref": ref,
        "model": model,
        "status": "complete" if result.returncode == 0 and decision else "failed",
        "exit_code": result.returncode,
        "elapsed_seconds": elapsed,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "provider_request_id": None,
        "decision": decision,
        "response_text": message if result.returncode == 0 else None,
        "error_summary": result.stderr[-500:] if result.returncode else None,
        "retry_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/003-vocabulary-curation/historical-model-comparison.json"),
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= len(REFS):
        parser.error("limit must be 1–5")
    root = Path.cwd()
    output = args.output.resolve()
    state = (
        json.loads(output.read_text())
        if output.exists() and output.stat().st_size
        else {
            "schema_version": 1,
            "purpose": "Matched independent-verifier comparison using saved evidence only",
            "model_configuration": {"reasoning_effort": "medium", "sandbox": "read-only"},
            "models": list(MODELS),
            "candidate_refs": list(REFS),
            "results": [],
        }
    )
    with tempfile.TemporaryDirectory(prefix="myid-model-compare-") as temporary:
        mirror = Path(temporary)
        shutil.copytree(root / "curation" / "batches", mirror / "curation" / "batches")
        (mirror / "data").mkdir()
        shutil.copy2(root / "data" / "vocabulary.tsv", mirror / "data" / "vocabulary.tsv")
        for ref in REFS[: args.limit]:
            batch_id, candidate_id = ref.split(":", 1)
            prompt = prompt_for(BatchStore(mirror, batch_id), candidate_id)
            prompt_digest = hashlib.sha256(prompt.encode()).hexdigest()
            for model in MODELS:
                attempts = [
                    row
                    for row in state["results"]
                    if row["candidate_ref"] == ref and row["model"] == model
                ]
                if any(row["status"] == "complete" for row in attempts) or len(attempts) >= 2:
                    continue
                row = call_model(root, mirror, ref, model, prompt)
                row["retry_count"] = len(attempts)
                row["prompt_digest"] = prompt_digest
                state["results"].append(row)
                atomic_json(output, state)
                print(ref, model, row["status"], row["elapsed_seconds"], flush=True)


if __name__ == "__main__":
    main()
