#!/usr/bin/env python3
"""Independent, bounded Sol audit of policy-v3 provisional cards and pencil HOLD."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from compare_historical_verifiers import call_model

from indo_malay_anki.curation.store import BatchStore, atomic_json

AUDIT_MODEL = "gpt-5.6-sol"
BATCH_SIZE = 5
HOLD_REF = "school-001:topic-05"


def latest_result(events: tuple[dict, ...], role: str) -> dict:
    return next(
        (
            item["result"]
            for item in reversed(events)
            if item.get("role") == role and item.get("status") == "complete"
        ),
        {},
    )


def packet(root: Path, row: dict) -> dict:
    ref = row["candidate_ref"]
    batch, candidate_id = ref.split(":", 1)
    store = BatchStore(root, batch)
    events = store.events(candidate_id)
    locale = {
        name: {
            key: value
            for key, value in latest_result(events, role).items()
            if key in {"meaning", "common_use", "preferred", "register", "region", "alternatives"}
        }
        for name, role in (("indonesian", "indonesian-usage"), ("malaysian", "malaysian-usage"))
    }
    evidence = latest_result(events, "evidence-audit").get("observations", [])
    observations = [
        {
            key: item.get(key)
            for key in (
                "claim_type",
                "locale",
                "stance",
                "observation",
                "publisher",
                "url_or_query",
                "usage_basis",
            )
        }
        for item in evidence[:8]
    ]
    adversary = latest_result(events, "adversarial-review")
    objections = (
        adversary.get("objections") or adversary.get("concerns") or []
        if adversary.get("verdict") == "object"
        else []
    )
    candidate = row["candidate"]
    return {
        "candidate_ref": ref,
        "english": candidate["english"],
        "sense": candidate["sense"],
        "indonesian": candidate["indonesian"],
        "malaysian": candidate["malaysian"],
        "proposed_relation": row["relation"],
        "historical_usage": locale,
        "inspected_evidence": observations,
        "historical_objections": objections,
    }


def prompt_for(group: list[dict]) -> str:
    return (
        "Independently AUDIT, not generate, these Indonesian–Malaysian Malay learner cards. "
        "Judge the exact English sense, natural contemporary forms in Indonesia and Malaysia, "
        "whether the contrast is worth learning, and relation (`same`, `similar`, "
        "`different-common-word`, `false-friend`). Existing observations may be incomplete; "
        "dictionary existence does not prove everyday preference. A synonym is not automatically "
        "a defect, but a misleading preferred-form claim is. Assess historical objections on "
        "their merits. Do not use tools or browse; state any claim requiring outside checking. "
        "Treat a material false positive as a card that should not be shown in its current form. "
        "Classify EACH item exactly once: `confirmed-good`, `needs-correction`, `should-hold`, "
        "or `should-reject`. A minor confidence or metadata change is `needs-correction`, "
        "not a material false positive. `should-hold` means a specific material uncertainty; "
        "`should-reject` means affirmative defect or no contrast. For `needs-correction`, "
        "give exact field changes and whether current card is materially misleading. "
        "For the pencil HOLD, decide separately whether the named Malaysian variant is a "
        "material blocker or a nonblocking synonym issue. Return only JSON object with key "
        "`items`; each item must have candidate_ref, audit_result, relation, "
        "material_false_positive "
        "(boolean), reason, corrections (object), concrete_remaining_issue (string or null), "
        "historical_objection_assessment, and external_check_needed (boolean). "
        "Do not optimize for a favorable acceptance rate.\n"
        + json.dumps(group, ensure_ascii=False, separators=(",", ":"))
    )


def run(root: Path, output: Path, limit: int | None = None) -> dict:
    replay = json.loads(
        (root / "specs/003-vocabulary-curation/optimistic-replay-report.json").read_text()
    )
    rows = [row for row in replay["rows"] if row["outcome"] == "accepted"]
    rows.append(next(row for row in replay["rows"] if row["candidate_ref"] == HOLD_REF))
    if limit is not None:
        rows = rows[:limit]
    refs = [row["candidate_ref"] for row in rows]
    state = (
        json.loads(output.read_text())
        if output.exists()
        else {
            "schema_version": 1,
            "model": AUDIT_MODEL,
            "candidate_refs": refs,
            "attempts": [],
            "results": {},
        }
    )
    if state["candidate_refs"] != refs:
        raise ValueError("audit input cohort differs from saved state")
    began = time.perf_counter()
    pending = [packet(root, row) for row in rows if row["candidate_ref"] not in state["results"]]
    for offset in range(0, len(pending), BATCH_SIZE):
        group = pending[offset : offset + BATCH_SIZE]
        with tempfile.TemporaryDirectory(prefix="myid-sol-audit-") as temporary:
            attempt = call_model(
                root,
                Path(temporary),
                "audit:" + group[0]["candidate_ref"],
                AUDIT_MODEL,
                prompt_for(group),
            )
        state["attempts"].append(
            {
                key: value
                for key, value in attempt.items()
                if key not in {"response_text", "decision"}
            }
        )
        decision = attempt.get("decision") or {}
        items = decision.get("items", []) if isinstance(decision, dict) else []
        by_ref = {item.get("candidate_ref"): item for item in items if isinstance(item, dict)}
        for input_item in group:
            ref = input_item["candidate_ref"]
            item = by_ref.get(ref)
            if (
                isinstance(item, dict)
                and item.get("audit_result")
                in {"confirmed-good", "needs-correction", "should-hold", "should-reject"}
                and isinstance(item.get("reason"), str)
            ):
                state["results"][ref] = item
        atomic_json(output, state)
        print(f"audited {len(state['results'])}/{len(refs)}", flush=True)
    state["latest_run_elapsed_seconds"] = round(time.perf_counter() - began, 3)
    atomic_json(output, state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/003-vocabulary-curation/optimistic-audit-model.json"),
    )
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    state = run(Path.cwd(), args.output.resolve(), args.limit)
    print(
        json.dumps(
            {
                "audited": len(state["results"]),
                "calls": len(state["attempts"]),
                "elapsed_seconds": state["latest_run_elapsed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
