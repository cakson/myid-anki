#!/usr/bin/env python3
"""Read-only, resumable Batch 2 policy replay with fresh compact Luna verification."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

from indo_malay_anki.curation.duplicates import comparison_key
from indo_malay_anki.curation.gate import decide_candidate
from indo_malay_anki.curation.models import role_route
from indo_malay_anki.curation.records import validate_stage_response
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_historical_verifiers import call_model  # noqa: E402

SPEC = Path("specs/003-vocabulary-curation")
SOURCE = SPEC / "second-batch-50-state.json"
AUDIT = SPEC / "second-batch-50-audit.json"
OUTPUT = SPEC / "second-batch-50-policy-replay.json"
REPORT = SPEC / "second-batch-50-policy-replay.md"
REQUIRED = {
    "cue_alignment",
    "cue_rewrite",
    "cue_rationale",
    "shared_synonym_case",
    "shared_synonym_rationale",
    "nonblocking_risk",
    "risk_rationale",
    "verdict",
    "relation",
    "concerns",
    "material_concerns",
    "rationale",
    "objection_assessments",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    root = Path.cwd()
    frozen = json.loads((root / SOURCE).read_text())
    audit = json.loads((root / AUDIT).read_text())
    if len(frozen["candidate_decisions"]) != 50 or len(audit["results"]) != 40:
        raise ValueError("frozen Batch 2 cohort or audit changed")
    fingerprints = {"source": sha(root / SOURCE), "audit": sha(root / AUDIT)}
    state = (
        json.loads((root / OUTPUT).read_text())
        if (root / OUTPUT).exists()
        else {
            "schema_version": 1,
            "frozen_input_sha256": fingerprints,
            "prompt_set_version": "2.2.0",
            "decision_policy_version": "3.1.0",
            "model_attempts": [],
            "verifier_results": {},
            "candidate_results": {},
        }
    )
    if state["frozen_input_sha256"] != fingerprints:
        raise ValueError("frozen inputs changed since replay started")
    prompt = (root / "curation/prompts/versions/2.2.0/independent-verification.md").read_text()
    route = role_route(root, "independent-verification")
    candidates = frozen["candidate_decisions"]
    queue = []
    for ref, old in sorted(candidates.items()):
        batch, cid = ref.split(":", 1)
        store = BatchStore(root, batch)
        if store.candidate(cid) != old["candidate"]:
            raise ValueError(f"frozen candidate changed: {ref}")
        candidate = old["candidate"]
        if comparison_key(candidate["indonesian"]) != comparison_key(candidate["malaysian"]):
            queue.append({"ref": ref, "candidate": candidate, "old_relation": old.get("relation")})
    started = time.perf_counter()
    for index in range(0, len(queue), 5):
        group = queue[index : index + 5]
        refs = [item["ref"] for item in group]
        if all(ref in state["verifier_results"] for ref in refs):
            continue
        request = (
            prompt
            + "\nEvaluate each existing candidate independently. Return ONLY a JSON object "
            + "with an `items` object keyed by each exact candidate ref. Every item must include "
            + "all verifier fields listed above. Do not generate new candidates. Audit outcomes "
            + "are withheld from you. For `verdict=object`, give a concrete objection. "
            + "Set verdict to EXACTLY `agree` or `object`; use `object` for material "
            + "concerns. Set relation to EXACTLY one of `same`, `similar`, "
            + "`different-common-word`, `false-friend`. Do not use absent frequency "
            + "data alone as an objection.\n"
            + json.dumps(group, ensure_ascii=False, separators=(",", ":"))
        )
        valid = None
        for retry in range(2):
            with tempfile.TemporaryDirectory(prefix="myid-cal2-replay-") as tmp:
                attempt = call_model(
                    root,
                    Path(tmp),
                    f"cal2-replay-{index // 5 + 1}-try-{retry + 1}",
                    route["model"],
                    request,
                    reasoning_effort=route["reasoning_effort"],
                )
            response = attempt.get("decision") or {}
            items = response.get("items", {}) if isinstance(response, dict) else {}
            try:
                if set(items) != set(refs):
                    raise ValueError("missing or unexpected candidate refs")
                for ref in refs:
                    if not REQUIRED <= set(items[ref]):
                        raise ValueError(f"missing structured fields for {ref}")
                    validate_stage_response(
                        "independent-verification",
                        {
                            "schema_version": 1,
                            "role": "independent-verification",
                            "model": route["model"],
                            "result": items[ref],
                        },
                    )
                valid = items
            except (ValueError, TypeError) as exc:
                attempt["validation_error"] = str(exc)
                state.setdefault("invalid_responses", []).append(
                    {"group_refs": refs, "response": response, "error": str(exc)}
                )
            state["model_attempts"].append(
                {
                    key: value
                    for key, value in attempt.items()
                    if key not in {"decision", "response_text"}
                }
            )
            if valid is not None:
                state["verifier_results"].update(valid)
                atomic_json(root / OUTPUT, state)
                break
            atomic_json(root / OUTPUT, state)
        if valid is None:
            raise RuntimeError(f"verifier failed bounded validation for {refs}")
        print("verified", index // 5 + 1, refs, flush=True)
    # A prior HOLD/REJECT may contain a concrete objection. The first compact
    # verifier pass deliberately excluded history, so resolve those objections
    # separately without consulting the independent audit or rewriting old events.
    historical = [
        {
            "ref": ref,
            "candidate": old["candidate"],
            "original_outcome": old["outcome"],
            "objections": old.get("reason_codes", []),
            "first_verifier": state["verifier_results"][ref],
        }
        for ref, old in sorted(candidates.items())
        if old["outcome"] in {"hold", "rejected"} and ref in state["verifier_results"]
    ]
    historical_start = time.perf_counter()
    for index in range(0, len(historical), 3):
        group = historical[index : index + 3]
        refs = [item["ref"] for item in group]
        if all(ref in state.get("historical_objection_results", {}) for ref in refs):
            continue
        request = (
            prompt
            + "\nReassess these existing candidates against their EXACT prior concrete "
            + "objections. Prior HOLD/REJECT status is not itself negative evidence, "
            + "but do not discard the stated reason. Return an `items` object keyed "
            + "by exact ref with all structured verifier fields. For each objection, "
            + "include {objection: exact original text, material: boolean, "
            + "resolution: specific explanation} in objection_assessments. If a "
            + "material objection remains, add a material_concern or affirmative_defect. "
            + "Use verdict EXACTLY `agree` or `object`; omit affirmative_defect when absent. "
            + "The independent audit is not provided.\n"
            + json.dumps(group, ensure_ascii=False, separators=(",", ":"))
        )
        valid = None
        for retry in range(2):
            with tempfile.TemporaryDirectory(prefix="myid-cal2-objection-") as tmp:
                attempt = call_model(
                    root,
                    Path(tmp),
                    f"cal2-history-{index // 3 + 1}-try-{retry + 1}",
                    route["model"],
                    request,
                    reasoning_effort=route["reasoning_effort"],
                )
            response = attempt.get("decision") or {}
            items = response.get("items", {}) if isinstance(response, dict) else {}
            try:
                if set(items) != set(refs):
                    raise ValueError("missing or unexpected historical refs")
                for item in group:
                    ref = item["ref"]
                    if not REQUIRED <= set(items[ref]):
                        raise ValueError(f"missing structured fields for {ref}")
                    assessed = {
                        entry.get("objection")
                        for entry in items[ref]["objection_assessments"]
                        if isinstance(entry, dict)
                    }
                    if not set(item["objections"]) <= assessed:
                        raise ValueError(f"historical objection unassessed: {ref}")
                    validate_stage_response(
                        "independent-verification",
                        {
                            "schema_version": 1,
                            "role": "independent-verification",
                            "model": route["model"],
                            "result": items[ref],
                        },
                    )
                valid = items
            except (ValueError, TypeError) as exc:
                attempt["validation_error"] = str(exc)
                state.setdefault("invalid_responses", []).append(
                    {"group_refs": refs, "response": response, "error": str(exc)}
                )
            state["model_attempts"].append(
                {
                    key: value
                    for key, value in attempt.items()
                    if key not in {"decision", "response_text"}
                }
            )
            if valid is not None:
                state.setdefault("historical_objection_results", {}).update(valid)
                atomic_json(root / OUTPUT, state)
                break
            atomic_json(root / OUTPUT, state)
        if valid is None:
            raise RuntimeError(f"historical objection verification failed for {refs}")
        print("historical objections assessed", refs, flush=True)
    if "historical_objection_replay_seconds" not in state:
        state["historical_objection_replay_seconds"] = round(
            time.perf_counter() - historical_start, 3
        )
    for ref, old in sorted(candidates.items()):
        batch, cid = ref.split(":", 1)
        store = BatchStore(root, batch)
        candidate = old["candidate"]
        stages = {
            "normalize-and-dedupe": current_results(store, cid).get("normalize-and-dedupe", {})
        }
        if ref in state["verifier_results"]:
            stages["independent-verification"] = state.get("historical_objection_results", {}).get(
                ref, state["verifier_results"][ref]
            )
            if ref in state.get("historical_objection_results", {}):
                stages["adversarial-review"] = {
                    "verdict": "object",
                    "objections": old["reason_codes"],
                }
        else:
            stages["relation-proposal"] = {"relation": "same", "aligned": True}
        decision = decide_candidate(candidate, stages, policy_version="3.1.0")
        state["candidate_results"][ref] = {
            "original": {
                key: old.get(key)
                for key in ("outcome", "relation", "confidence_tier", "reason_codes")
            },
            "replay": decision,
            "audit_verdict": audit["results"].get(ref, {}).get("verdict"),
        }
    if "active_replay_seconds" not in state:
        state["active_replay_seconds"] = round(time.perf_counter() - started, 3)
    atomic_json(root / OUTPUT, state)
    outcomes = Counter(item["replay"]["outcome"] for item in state["candidate_results"].values())
    tiers = Counter(
        item["replay"].get("confidence_tier")
        for item in state["candidate_results"].values()
        if item["replay"]["outcome"] == "accepted"
    )
    calibration = defaultdict(Counter)
    changed = []
    for ref, item in state["candidate_results"].items():
        new = item["replay"]
        old = item["original"]
        verdict = item["audit_verdict"]
        if verdict:
            calibration[new.get("confidence_tier", new["outcome"])][verdict] += 1
        if old["outcome"] != new["outcome"] or old.get("relation") != new.get("relation"):
            changed.append(ref)
    attempts = state["model_attempts"]
    unsafe = {"materially-misleading", "should-hold", "should-reject"}
    unsafe_items = [
        (ref, item)
        for ref, item in state["candidate_results"].items()
        if item["audit_verdict"] in unsafe
    ]
    unsafe_low_or_very_low = sum(
        item["replay"].get("confidence_tier") in {"low", "very-low"} for _, item in unsafe_items
    )
    unsafe_blocked = sum(
        item["replay"]["outcome"] in {"hold", "rejected"} for _, item in unsafe_items
    )
    confirmed_good_very_low = sum(
        item["audit_verdict"] == "confirmed-good"
        and item["replay"].get("confidence_tier") == "very-low"
        for item in state["candidate_results"].values()
    )
    unsafe_medium_or_high = sum(
        item["audit_verdict"] in unsafe
        and item["replay"].get("confidence_tier") in {"medium", "high"}
        for item in state["candidate_results"].values()
    )
    fast_accepts = sum(
        item["replay"]["outcome"] == "accepted"
        and item["replay"].get("risk", {}).get("path") == "ordinary-fast"
        for item in state["candidate_results"].values()
    )
    escalations = sum(
        item["replay"].get("risk", {}).get("path") in {"escalated", "false-friend"}
        for item in state["candidate_results"].values()
    )
    inputs = [
        item["input_tokens"] for item in attempts if isinstance(item.get("input_tokens"), int)
    ]
    outputs = [
        item["output_tokens"] for item in attempts if isinstance(item.get("output_tokens"), int)
    ]
    total_replay_seconds = round(
        state["active_replay_seconds"] + state["historical_objection_replay_seconds"], 3
    )
    lines = [
        "# Batch 2 fixed-corpus policy replay",
        "",
        "Historical state and audit were read only. No candidates were generated or promoted.",
        "",
        f"- Frozen candidates: {len(candidates)}; model: {route['model']}; "
        f"verifier calls: {len(attempts)}",
        f"- Replay decisions: {dict(outcomes)}; accepted confidence: {dict(tiers)}",
        f"- Fast-path accepts: {fast_accepts}; escalations: {escalations}",
        f"- Active replay elapsed: {state['active_replay_seconds']} seconds",
        f"- Additional historical-objection assessment: "
        f"{state['historical_objection_replay_seconds']} seconds; "
        f"total active time about {total_replay_seconds} seconds",
        f"- Recorded verifier tokens: input {sum(inputs)}, output {sum(outputs)}; "
        "cost unavailable (no price recorded)",
        f"- Decisions or relations changed: {len(changed)} — "
        f"{', '.join(changed) if changed else 'none'}",
        f"- Previously audited unsafe/unresolved: {len(unsafe_items)}; replay HOLD/REJECT: "
        f"{unsafe_blocked}; accepted low/very-low: {unsafe_low_or_very_low}; "
        f"accepted medium/high: {unsafe_medium_or_high}",
        f"- Confirmed-good cards still very-low: {confirmed_good_very_low}",
        "",
        "## Audit calibration",
        "",
        "| Replay tier or outcome | Audit findings |",
        "|---|---|",
    ]
    lines += [f"| {tier} | {dict(counts)} |" for tier, counts in sorted(calibration.items())]
    lines += [
        "",
        "## Candidate comparison",
        "",
        "| Candidate | Old | Replay | Old → new relation | Old → new tier | "
        "Fast path | Audit | Reason / routing |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for ref, item in sorted(state["candidate_results"].items()):
        old, new = item["original"], item["replay"]
        verifier = state.get("historical_objection_results", {}).get(
            ref, state["verifier_results"].get(ref, {})
        )
        route_detail = ", ".join(
            str(verifier.get(key, ""))
            for key in ("cue_alignment", "shared_synonym_case", "nonblocking_risk")
            if verifier.get(key)
        )
        fast_path = (
            new["outcome"] == "accepted" and new.get("risk", {}).get("path") == "ordinary-fast"
        )
        lines.append(
            f"| {ref} | {old['outcome']} | {new['outcome']} | "
            f"{old.get('relation') or '—'} → {new.get('relation') or '—'} | "
            f"{old.get('confidence_tier') or '—'} → {new.get('confidence_tier') or '—'} | "
            f"{fast_path} | "
            f"{item['audit_verdict'] or 'not audited'} | "
            f"{'; '.join(new.get('reason_codes', []))}; {route_detail} |"
        )
    REPORT_PATH = root / REPORT
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(dict(outcomes), dict(tiers), f"calls={len(attempts)}", flush=True)


if __name__ == "__main__":
    main()
