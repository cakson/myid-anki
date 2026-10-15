#!/usr/bin/env python3
"""Second bounded 50-candidate Feature 003 benchmark with resumable AI calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from indo_malay_anki.curation.duplicates import comparison_key
from indo_malay_anki.curation.gate import decide_candidate
from indo_malay_anki.curation.models import role_route
from indo_malay_anki.curation.records import validate_stage_response
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results, ingest_response, init_batch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_historical_verifiers import call_model  # noqa: E402

BATCHES = (
    "cal2-daily-001",
    "cal2-shopping-001",
    "cal2-travel-001",
    "cal2-work-001",
    "cal2-social-001",
)
STATE = Path("specs/003-vocabulary-curation/second-batch-50-state.json")
MODEL = role_route(Path.cwd(), "generate")["model"]
PROMPT_VERSION = "2.1.0"
TOPICS = {
    "cal2-daily-001": ("Daily routines and home", "Daily actions and household items"),
    "cal2-shopping-001": ("Shopping and services", "Shopping, services, food and money"),
    "cal2-travel-001": ("Transport and travel", "Transport, directions and travel"),
    "cal2-work-001": ("Work and education", "Work, school and communication"),
    "cal2-social-001": ("Health, social life and qualities", "Health, social verbs and adjectives"),
}


def prompt_text(root: Path, role: str) -> str:
    name = "generate.md" if role == "generate" else "independent-verification.md"
    return (root / "curation" / "prompts" / "versions" / PROMPT_VERSION / name).read_text()


def save_attempt(root: Path, attempt: dict) -> None:
    path = root / STATE
    state = json.loads(path.read_text())
    state["operation_attempts"].append(
        {key: value for key, value in attempt.items() if key not in {"decision", "response_text"}}
    )
    atomic_json(path, state)


def request(root: Path, ref: str, prompt: str) -> dict:
    operation = ref.split(":", 1)[0]
    role = {
        "generate": "generate",
        "normalize": "normalize-and-dedupe",
        "verify": "independent-verification",
        "repair": "independent-verification",
    }[operation]
    route = role_route(root, role)
    if route["model"] != MODEL:
        raise ValueError(f"benchmark requires one configured production model: {role}")
    with tempfile.TemporaryDirectory(prefix="myid-fresh-benchmark-") as temporary:
        attempt = call_model(
            root,
            Path(temporary),
            ref,
            route["model"],
            prompt,
            reasoning_effort=route["reasoning_effort"],
        )
    attempt["role"] = role
    attempt["prompt_set_version"] = PROMPT_VERSION
    save_attempt(root, attempt)
    if attempt["status"] != "complete":
        raise RuntimeError(f"model call failed for {ref}: {attempt.get('error_summary')}")
    return attempt


def generate(root: Path) -> None:
    state_path = root / STATE
    if not state_path.exists():
        atomic_json(
            state_path,
            {
                "schema_version": 1,
                "experiment_id": "second-fresh-50",
                "phase": "generation",
                "target_candidates": 50,
                "started_at_utc": datetime.now(UTC).isoformat(),
                "prompt_set_version": PROMPT_VERSION,
                "canonical_source_digest_before": hashlib.sha256(
                    (root / "data/vocabulary.tsv").read_bytes()
                ).hexdigest(),
                "operation_attempts": [],
                "candidate_batches": list(BATCHES),
                "candidate_decisions": {},
                "model_output_failures": [],
            },
        )
    state = json.loads(state_path.read_text())
    if state["candidate_batches"] != list(BATCHES):
        raise ValueError("second-batch cohort differs from saved state")
    for batch_id in BATCHES:
        store = BatchStore(root, batch_id)
        if not (store.path / "manifest.json").exists():
            topic, scope = TOPICS[batch_id]
            store = init_batch(root, batch_id, topic, 10, scope)
        existing = list(store.candidate_ids())
        if len(existing) == 10:
            print(batch_id, "generation already complete", flush=True)
            continue
        if existing:
            raise ValueError(f"partial generation in {batch_id} requires inspection")
        archive = json.loads((store.path / "generation-archive-snapshot.json").read_text())
        compact_archive = [
            {
                "ref": item["reference"],
                "english": item["english"],
                "indonesian": item["indonesian"],
                "malaysian": item["malaysian"],
            }
            for item in archive
            if item.get("english")
        ]
        prompt = (
            prompt_text(root, "generate")
            + "\nReturn exactly ten candidates with IDs "
            + ", ".join(f"{batch_id.split('-')[1]}-{number:02d}" for number in range(1, 11))
            + ". Return JSON object with schema_version=1, role=generate, model="
            + MODEL
            + ", and result.candidates. Topic/scope and avoid-list follow.\n"
            + json.dumps(
                {
                    "topic": TOPICS[batch_id][0],
                    "scope": TOPICS[batch_id][1],
                    "archive": compact_archive,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        response_path = store.path / "second-generation-response.json"
        if response_path.exists():
            raw = json.loads(response_path.read_text())
        else:
            raw = request(root, f"generate:{batch_id}", prompt)["decision"]
            atomic_json(response_path, raw)
        validate_stage_response("generate", raw, limit=10)
        candidates = raw["result"]["candidates"]
        if len(candidates) != 10 or len({x["candidate_id"] for x in candidates}) != 10:
            raise ValueError(f"generation did not return exactly ten unique candidates: {batch_id}")
        ingest_response(store, "generate", json.dumps(raw, ensure_ascii=False), None, MODEL)
        print(batch_id, "generated", len(candidates), flush=True)


def all_candidates(root: Path) -> list[dict]:
    rows = []
    for batch_id in BATCHES:
        store = BatchStore(root, batch_id)
        for candidate_id in store.candidate_ids():
            candidate = store.candidate(candidate_id)
            rows.append({"ref": f"{batch_id}:{candidate_id}", **candidate})
    if len(rows) != 50 or len({row["ref"] for row in rows}) != 50:
        raise ValueError("benchmark requires exactly 50 unique generated candidate refs")
    return rows


def normalize(root: Path) -> None:
    cohort = all_candidates(root)
    # The historical archive includes previously investigated as well as active concepts.
    archive = json.loads(
        (root / "curation/batches/cal2-daily-001/generation-archive-snapshot.json").read_text()
    )
    compact_archive = [
        {"ref": item["reference"], "english": item["english"]}
        for item in archive
        if item.get("english")
    ]
    for batch_id in BATCHES:
        store = BatchStore(root, batch_id)
        candidate_ids = list(store.candidate_ids())
        if all("normalize-and-dedupe" in current_results(store, cid) for cid in candidate_ids):
            print(batch_id, "normalization already complete", flush=True)
            continue
        group = [row for row in cohort if row["ref"].startswith(batch_id + ":")]
        prompt = (
            "You are an independent semantic duplicate reviewer, separate from generation. "
            "Compare these ten candidates with the entire historical concept index and the "
            "other 49 fresh candidates. Catch identical cues, singular/plural, English synonyms, "
            "same learning concepts under alternate labels, and identical answer pairs. "
            "Return only JSON with `overlaps` object keyed by EVERY candidate_id in this ten-item "
            "group. Each value is a list of {other_id,type,resolution,rationale}. Resolution is "
            "reject for a confirmed duplicate, distinct for a similar label with clearly different "
            "sense, unresolved only for a real semantic question; otherwise use an empty list. "
            "Do not mark a candidate as overlapping itself. Do not generate new candidates. "
            "Prefer one canonical record for duplicate meanings.\n"
            + json.dumps(
                {"group": group, "fresh_cohort": cohort, "historical_index": compact_archive},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        response_path = store.path / "second-normalize-response.json"
        if response_path.exists():
            raw = json.loads(response_path.read_text())
        else:
            raw = request(root, f"normalize:{batch_id}", prompt)["decision"]
        overlaps = raw.get("overlaps", {}) if isinstance(raw, dict) else {}
        if set(overlaps) != set(candidate_ids) or any(
            not isinstance(x, list) for x in overlaps.values()
        ):
            raise ValueError(f"malformed normalization group: {batch_id}")
        if not response_path.exists():
            atomic_json(response_path, raw)
        removed_self = 0
        for candidate_id in candidate_ids:
            before = len(overlaps[candidate_id])
            overlaps[candidate_id] = [
                item
                for item in overlaps[candidate_id]
                if item.get("other_id") not in {candidate_id, f"{batch_id}:{candidate_id}"}
            ]
            removed_self += before - len(overlaps[candidate_id])
        if removed_self:
            atomic_json(
                store.path / "second-normalize-self-overlap-repair.json",
                {
                    "removed_self_references": removed_self,
                    "method": (
                        "discard deterministic self-overlaps; preserve original model response"
                    ),
                },
            )
        for candidate_id in candidate_ids:
            wrapped = {
                "schema_version": 1,
                "role": "normalize-and-dedupe",
                "model": MODEL,
                "result": {"overlaps": overlaps[candidate_id]},
            }
            ingest_response(
                store,
                "normalize-and-dedupe",
                json.dumps(wrapped, ensure_ascii=False),
                candidate_id,
                MODEL,
            )
        print(batch_id, "normalized", len(candidate_ids), flush=True)


def verify(root: Path) -> None:
    from indo_malay_anki.curation.workflow import finalize_reject

    all_candidates(root)
    for batch_id in BATCHES:
        store = BatchStore(root, batch_id)
        candidate_ids = list(store.candidate_ids())
        eligible = []
        for candidate_id in candidate_ids:
            candidate = store.candidate(candidate_id)
            ref = f"{batch_id}:{candidate_id}"
            same_form = comparison_key(candidate["indonesian"]) == comparison_key(
                candidate["malaysian"]
            )
            if same_form:
                if not any(
                    event.get("role") == "explicit-final" for event in store.events(candidate_id)
                ):
                    finalize_reject(
                        store,
                        candidate_id,
                        "Identical ordinary forms offer no meaningful recall contrast.",
                        "no-meaningful-cross-language-contrast",
                    )
                print(ref, "early no-contrast reject", flush=True)
                continue
            stages = current_results(store, candidate_id)
            decision = decide_candidate(candidate, stages, policy_version="3.0.0")
            if decision["outcome"] == "rejected":
                if "independent-verification" not in stages:
                    print(ref, "early duplicate reject", flush=True)
                    continue
            verifier = stages.get("independent-verification", {})
            invalid_same = verifier.get("relation") == "same" and not same_form
            if not verifier or invalid_same:
                eligible.append(candidate_id)
        for offset in range(0, len(candidate_ids), 5):
            group_ids = [cid for cid in candidate_ids[offset : offset + 5] if cid in eligible]
            if not group_ids:
                continue
            items = []
            for candidate_id in group_ids:
                candidate = store.candidate(candidate_id)
                prior = current_results(store, candidate_id)
                items.append(
                    {
                        "candidate_id": candidate_id,
                        "candidate": {
                            key: candidate[key]
                            for key in ("english", "indonesian", "malaysian", "sense", "tags")
                        },
                        "overlaps": prior.get("normalize-and-dedupe", {}).get("overlaps", []),
                    }
                )
            prompt = (
                prompt_text(root, "independent-verification")
                + "\nVerify EACH supplied candidate independently. "
                "Return JSON object with `items` keyed by every candidate_id. Each value must "
                "contain verdict (agree/object), relation, concerns (list), material_concerns "
                "(list), rationale (candidate-specific), objection_assessments (list), "
                "and optional "
                "affirmative_defect only for a confirmed error. Set objection_assessments to [] "
                "because these new candidates have no historical objections. "
                "Do not browse or generate.\n"
                + json.dumps(items, ensure_ascii=False, separators=(",", ":"))
            )
            response_path = store.path / f"second-verifier-{offset:02d}.json"
            if response_path.exists():
                raw = json.loads(response_path.read_text())
            else:
                attempt = request(root, f"verify:{batch_id}:{offset}", prompt)
                raw = attempt["decision"]
            results = raw.get("items", {}) if isinstance(raw, dict) else {}
            if not set(group_ids).issubset(results):
                raise ValueError(f"malformed verification group: {batch_id}:{offset}")
            if not response_path.exists():
                atomic_json(response_path, raw)
            for candidate_id in group_ids:
                result = results[candidate_id]
                candidate = store.candidate(candidate_id)
                normalized_same = comparison_key(candidate["indonesian"]) == comparison_key(
                    candidate["malaysian"]
                )
                error = None
                if result.get("relation") == "same" and not normalized_same:
                    error = "same is invalid because the Indonesian and Malaysian forms differ"
                elif result.get("objection_assessments"):
                    error = "new candidates have no historical objections"
                else:
                    try:
                        validate_stage_response(
                            "independent-verification",
                            {
                                "schema_version": 1,
                                "role": "independent-verification",
                                "model": MODEL,
                                "result": result,
                            },
                        )
                    except ValueError as exc:
                        error = str(exc)
                if error:
                    repair_path = (
                        store.path / f"second-verifier-{offset:02d}-{candidate_id}-repair.json"
                    )
                    if repair_path.exists():
                        repaired = json.loads(repair_path.read_text())
                    else:
                        repair_prompt = (
                            "Repair exactly one independent verifier result. The earlier output "
                            f"failed schema/semantics: {error}. `same` means effectively identical "
                            "normal word forms, not merely the same concept. For different forms "
                            "that lack a genuine national contrast, choose the plausible form "
                            "relation and identify an affirmative defect such as "
                            "artificial-synonym. "
                            "Set objection_assessments to []. Return only JSON object with key "
                            "`result`, using the same verifier fields. Do not invent facts.\n"
                            + json.dumps(
                                {"candidate": candidate, "invalid_result": result},
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                        )
                        repaired = request(
                            root,
                            f"repair:{batch_id}:{candidate_id}",
                            repair_prompt,
                        )["decision"]
                        atomic_json(repair_path, repaired)
                    replacement = repaired.get("result", {})
                    if replacement.get("relation") == "artificial-synonym":
                        replacement["relation"] = "different-common-word"
                        replacement["affirmative_defect"] = "artificial-synonym"
                    if replacement.get("relation") == "same" and not normalized_same:
                        raise ValueError(
                            f"repair retained invalid same relation: {batch_id}:{candidate_id}"
                        )
                    if replacement.get("objection_assessments"):
                        raise ValueError(f"repair invented objections: {batch_id}:{candidate_id}")
                    validate_stage_response(
                        "independent-verification",
                        {
                            "schema_version": 1,
                            "role": "independent-verification",
                            "model": MODEL,
                            "result": replacement,
                        },
                    )
                    results[candidate_id] = replacement
            atomic_json(response_path, {"items": results})
            for candidate_id in group_ids:
                wrapped = {
                    "schema_version": 1,
                    "role": "independent-verification",
                    "model": MODEL,
                    "result": results[candidate_id],
                }
                ingest_response(
                    store,
                    "independent-verification",
                    json.dumps(wrapped, ensure_ascii=False),
                    candidate_id,
                    MODEL,
                )
            print(batch_id, "verified", group_ids, flush=True)


def decisions(root: Path) -> dict:
    from indo_malay_anki.curation.report import batch_report

    state_path = root / STATE
    state = json.loads(state_path.read_text())
    rows = []
    for batch_id in BATCHES:
        store = BatchStore(root, batch_id)
        report = batch_report(store)
        if report["pending"]:
            raise ValueError(f"batch remains pending: {batch_id}")
        for item in report["decisions"]:
            candidate_id = item["candidate_id"]
            candidate = store.candidate(candidate_id)
            stages = current_results(store, candidate_id)
            verifier = stages.get("independent-verification", {})
            rationale = (
                item.get("confidence_rationale") or verifier.get("rationale")
                if item["outcome"] == "accepted"
                else item.get("decision_reason") or "; ".join(item["reason_codes"])
            )
            rows.append(
                {
                    "candidate_ref": f"{batch_id}:{candidate_id}",
                    "candidate": candidate,
                    "outcome": item["outcome"],
                    "relation": item["relation"],
                    "risk": item["risk"],
                    "confidence_tier": item.get("confidence_tier"),
                    "confidence_rationale": rationale,
                    "review_flags": item.get("review_flags", []),
                    "reason_codes": item["reason_codes"],
                    "verifier": verifier,
                }
            )
    if len(rows) != 50:
        raise ValueError("decision report must retain all 50 candidates")
    state["phase"] = "production-complete"
    state["production_ended_at_utc"] = datetime.now(UTC).isoformat()
    state["candidate_decisions"] = {row["candidate_ref"]: row for row in rows}
    atomic_json(state_path, state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("generate", "normalize", "verify", "decisions"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.phase == "generate":
        generate(root)
    elif args.phase == "normalize":
        normalize(root)
    elif args.phase == "verify":
        verify(root)
    else:
        result = decisions(root)
        print(
            json.dumps(
                {"phase": result["phase"], "decisions": len(result["candidate_decisions"])},
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
