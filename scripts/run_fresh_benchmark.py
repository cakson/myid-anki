#!/usr/bin/env python3
"""Bounded fresh 50-candidate Feature 003 benchmark with resumable AI calls."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from indo_malay_anki.curation.duplicates import comparison_key
from indo_malay_anki.curation.gate import decide_candidate
from indo_malay_anki.curation.records import validate_stage_response
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results, ingest_response, packet_for

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_historical_verifiers import call_model  # noqa: E402

BATCHES = (
    "fresh-food-001",
    "fresh-home-001",
    "fresh-travel-001",
    "fresh-work-001",
    "fresh-actions-001",
)
STATE = Path("specs/003-vocabulary-curation/fresh-batch-50-state.json")
MODEL = "gpt-5.6-luna"


def save_attempt(root: Path, attempt: dict) -> None:
    path = root / STATE
    state = json.loads(path.read_text())
    state["operation_attempts"].append(
        {key: value for key, value in attempt.items() if key not in {"decision", "response_text"}}
    )
    atomic_json(path, state)


def request(root: Path, ref: str, prompt: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="myid-fresh-benchmark-") as temporary:
        attempt = call_model(root, Path(temporary), ref, MODEL, prompt)
    save_attempt(root, attempt)
    if attempt["status"] != "complete":
        raise RuntimeError(f"model call failed for {ref}: {attempt.get('error_summary')}")
    return attempt


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
        (root / "curation/batches/fresh-food-001/generation-archive-snapshot.json").read_text()
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
        attempt = request(root, f"normalize:{batch_id}", prompt)
        raw = attempt["decision"]
        overlaps = raw.get("overlaps", {}) if isinstance(raw, dict) else {}
        if set(overlaps) != set(candidate_ids) or any(
            not isinstance(x, list) for x in overlaps.values()
        ):
            raise ValueError(f"malformed normalization group: {batch_id}")
        atomic_json(store.path / "fresh-normalize-response.json", raw)
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
                packet = packet_for(store, "independent-verification", candidate_id)
                items.append({"candidate_id": candidate_id, "context": packet["context"]})
            prompt = (
                "Independently verify these Indonesian–Malaysian Malay vocabulary pairs. "
                "You did not generate them. For EACH candidate decide if both terms naturally "
                "express the same exact English sense and teach a useful national contrast. "
                "Choose relation same/similar/different-common-word/false-friend yourself. "
                "IMPORTANT: `same` means the Indonesian and Malaysian WORD FORMS are effectively "
                "identical and provide no recall contrast; it does NOT mean the meanings align. "
                "When different words express the same meaning, choose `similar` if recognizably "
                "related, otherwise `different-common-word`. Reject artificial national contrasts "
                "where the proposed Malaysian form is merely a formal synonym of a shared "
                "ordinary word. "
                "For ordinary pairs, do not demand external evidence absent concrete risk. "
                "A mere alternate synonym or missing frequency statistic is nonblocking. "
                "Name material semantic, register, regional, duplicate or preferred-form concerns "
                "specifically. False friends require later strict evidence and adversarial review. "
                "Return JSON object with `items` keyed by every candidate_id. Each value must "
                "contain verdict (agree/object), relation, concerns (list), material_concerns "
                "(list), rationale (candidate-specific), objection_assessments (list), "
                "and optional "
                "affirmative_defect only for a confirmed error. Set objection_assessments to [] "
                "because these new candidates have no historical objections. "
                "Do not browse or generate.\n"
                + json.dumps(items, ensure_ascii=False, separators=(",", ":"))
            )
            response_path = store.path / f"fresh-verifier-{offset:02d}.json"
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
                        store.path / f"fresh-verifier-{offset:02d}-{candidate_id}-repair.json"
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
                verifier.get("rationale")
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
    parser.add_argument("phase", choices=("normalize", "verify", "decisions"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.phase == "normalize":
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
