#!/usr/bin/env python3
"""Freeze and run a read-only, batch-separated verifier-contract comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from compare_historical_verifiers import call_model

from indo_malay_anki.curation.store import atomic_json

ROOT = Path.cwd()
SPEC = ROOT / "specs/003-vocabulary-curation"
STATES = {
    "fresh1": "fresh-batch-50-state.json",
    "fresh2": "second-batch-50-state.json",
    "fresh3": "final-calibration-50-state.json",
    "fresh4": "prospective-preference-50-state.json",
    "technical25": "technical-borrowing-25-state.json",
}
AUDITS = (
    "fresh-batch-50-audit.json",
    "fresh-batch-50-audit-completion.json",
    "second-batch-50-audit.json",
    "final-calibration-50-audit.json",
    "final-calibration-localized-standard-audit.json",
    "final-calibration-router-supplement-audit.json",
    "prospective-preference-50-audit.json",
    "technical-borrowing-25-audit.json",
)
INPUTS = SPEC / "verifier-contract-benchmark-inputs.json"
LABELS = SPEC / "verifier-contract-benchmark-labels.json"
RESULTS = SPEC / "verifier-contract-benchmark-results.json"
PROMPT = SPEC / "verifier-contract-experiment.md"
MODELS = {"B_luna": "gpt-5.6-luna", "C_sol": "gpt-5.6-sol"}
CRITICAL = {"materially-misleading", "should-hold", "should-reject"}
VALID_ACTIONS = {"ACCEPT", "ACCEPT_WITH_REVIEW", "HOLD", "REJECT"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_population() -> tuple[dict, dict]:
    production = {}
    for batch, filename in STATES.items():
        state = json.loads((SPEC / filename).read_text())
        for ref, row in state["candidate_decisions"].items():
            if row["outcome"] == "accepted":
                production[ref] = (batch, row)
    audits = {}
    for filename in AUDITS:
        audits.update(json.loads((SPEC / filename).read_text()).get("results", {}))
    return production, audits


def prepare() -> None:
    if INPUTS.exists() or LABELS.exists():
        if not (INPUTS.exists() and LABELS.exists()):
            raise ValueError("partial frozen benchmark exists")
        print("frozen benchmark preserved", len(json.loads(INPUTS.read_text())["items"]))
        return
    production, audits = load_population()
    available = {
        ref: (batch, row, audits[ref]) for ref, (batch, row) in production.items() if ref in audits
    }
    critical = sorted(
        ref for ref, (_, _, audit) in available.items() if audit["verdict"] in CRITICAL
    )
    if len(critical) != 20:
        raise ValueError(f"expected 20 known unsafe production ACCEPTs, got {len(critical)}")
    good = [ref for ref, (_, _, audit) in available.items() if audit["verdict"] == "confirmed-good"]
    minor = [
        ref for ref, (_, _, audit) in available.items() if audit["verdict"] == "minor-correction"
    ]
    # Four controls per batch keep the latest cohort evaluable on both errors and false alarms.
    selected_good = []
    for batch in STATES:
        targets = [ref for ref in critical if available[ref][0] == batch]
        for target in targets[:3]:
            target_tags = set(available[target][1]["candidate"].get("tags", []))
            choices = [
                ref
                for ref in good
                if available[ref][0] == batch
                and available[ref][1]["relation"] == "different-common-word"
                and ref not in selected_good
            ]
            ranked = sorted(
                choices,
                key=lambda ref: (
                    -len(target_tags & set(available[ref][1]["candidate"].get("tags", []))),
                    ref,
                ),
            )
            selected_good.append(ranked[0])
        fourth = sorted(
            ref
            for ref in good
            if available[ref][0] == batch
            and ref not in selected_good
            and (batch == "technical25" or available[ref][1]["relation"] == "similar")
        )
        selected_good.append(fourth[0])
    if len(selected_good) != 20:
        raise ValueError("insufficient matched confirmed-good controls")
    selected_minor = []
    for batch, count in zip(STATES, (2, 2, 2, 1, 1), strict=True):
        pool = sorted(
            ref for ref in minor if available[ref][0] == batch and ref not in selected_minor
        )
        selected_minor.extend(pool[:count])
    if len(selected_minor) != 8:
        raise ValueError("insufficient correction controls")
    refs = sorted(critical + selected_good + selected_minor)
    inputs = []
    labels = {}
    for ref in refs:
        batch, row, audit = available[ref]
        candidate = {
            key: row["candidate"][key]
            for key in ("english", "indonesian", "malaysian", "sense", "tags")
        }
        inputs.append({"candidate_ref": ref, "batch": batch, "candidate": candidate})
        labels[ref] = {
            "audit_verdict": audit["verdict"],
            "critical": audit["verdict"] in CRITICAL,
            "audit_reason": audit.get("reason"),
            "batch": batch,
            "relation_at_production": row["relation"],
            "production_action": "ACCEPT",
            "production_verifier": row.get("verifier"),
            "production_review_flags": row.get("review_flags", []),
        }
    atomic_json(
        INPUTS,
        {
            "schema_version": 1,
            "purpose": "production-time candidate input only; no audit labels or corrections",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "items": inputs,
        },
    )
    atomic_json(
        LABELS,
        {
            "schema_version": 1,
            "purpose": "evaluation labels; benchmark model runner never reads this file",
            "input_digest": digest(INPUTS),
            "labels": labels,
        },
    )
    print(
        "frozen",
        len(refs),
        Counter(
            "critical" if ref in critical else "good" if ref in selected_good else "minor"
            for ref in refs
        ),
    )


def model_prompt(items: list[dict]) -> str:
    contract = PROMPT.read_text()
    # Do not expose batch names, prior verifier outputs, routing flags, or audit labels.
    visible = [
        {"candidate_ref": item["candidate_ref"], "candidate": item["candidate"]} for item in items
    ]
    return (
        contract
        + "\n\nEvaluate exactly these candidates:\n"
        + json.dumps(visible, ensure_ascii=False, separators=(",", ":"))
    )


def validate_items(raw: dict, expected: set[str]) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get("items"), dict):
        raise ValueError("missing keyed items")
    items = raw["items"]
    if set(items) != expected:
        raise ValueError("result candidate refs differ from request")
    for ref, value in items.items():
        if not isinstance(value, dict) or value.get("action") not in VALID_ACTIONS:
            raise ValueError(f"invalid action for {ref}")
        if value.get("semantic_alignment") not in {"clear", "uncertain", "mismatch"}:
            raise ValueError(f"invalid semantic alignment for {ref}")
        precision = value.get("answer_precision") or {}
        if set(precision) != {"indonesian", "malaysian"} or any(
            item not in {"natural", "questionable", "misleading"} for item in precision.values()
        ):
            raise ValueError(f"invalid answer precision for {ref}")
        if value.get("everyday_contrast") not in {"useful", "qualified", "uncertain", "misleading"}:
            raise ValueError(f"invalid everyday contrast for {ref}")
        if not isinstance(value.get("reason"), str) or not value["reason"].strip():
            raise ValueError(f"missing reason for {ref}")
        if value.get("concrete_objection") is not None and not isinstance(
            value["concrete_objection"], str
        ):
            raise ValueError(f"invalid objection for {ref}")
    return items


def run(variant: str) -> None:
    if variant not in MODELS:
        raise ValueError("unknown variant")
    source = json.loads(INPUTS.read_text())
    artifact = (
        json.loads(RESULTS.read_text())
        if RESULTS.exists()
        else {
            "schema_version": 1,
            "input_digest": digest(INPUTS),
            "prompt_digest": digest(PROMPT),
            "models": MODELS,
            "attempts": [],
            "results": {"B_luna": {}, "C_sol": {}},
        }
    )
    if artifact["input_digest"] != digest(INPUTS) or artifact["prompt_digest"] != digest(PROMPT):
        raise ValueError("frozen inputs or experimental prompt changed")
    items = source["items"]
    # Six items/call keeps output bounded. Each variant sees byte-identical prompts.
    for index in range(0, len(items), 6):
        group = items[index : index + 6]
        pending = [
            item for item in group if item["candidate_ref"] not in artifact["results"][variant]
        ]
        if not pending:
            continue
        prompt = model_prompt(group)
        for retry in range(2):
            with tempfile.TemporaryDirectory(prefix="myid-verifier-benchmark-") as temporary:
                attempt = call_model(
                    ROOT,
                    Path(temporary),
                    f"{variant}:{index // 6}",
                    MODELS[variant],
                    prompt,
                    reasoning_effort="medium",
                )
            artifact["attempts"].append(
                {
                    **{
                        key: value
                        for key, value in attempt.items()
                        if key not in {"decision", "response_text"}
                    },
                    "variant": variant,
                    "group": index // 6,
                    "retry": retry,
                    "prompt_digest": hashlib.sha256(prompt.encode()).hexdigest(),
                }
            )
            atomic_json(RESULTS, artifact)
            try:
                if attempt["status"] != "complete":
                    raise ValueError(attempt.get("error_summary") or "model call failed")
                parsed = validate_items(
                    attempt["decision"], {item["candidate_ref"] for item in group}
                )
            except ValueError as exc:
                print(variant, index // 6, "attempt failed", exc, flush=True)
                if retry:
                    raise
                continue
            artifact["results"][variant].update(parsed)
            atomic_json(RESULTS, artifact)
            print(variant, index // 6, "complete", len(parsed), flush=True)
            break


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run"))
    parser.add_argument("--variant", choices=tuple(MODELS))
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    elif args.variant:
        run(args.variant)
    else:
        parser.error("run requires --variant")


if __name__ == "__main__":
    main()
