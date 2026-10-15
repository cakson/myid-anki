#!/usr/bin/env python3
"""Fixed Batch 2 challenge replay; keeps production, audit, and v3.1 records immutable."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from indo_malay_anki.curation.gate import decide_candidate
from indo_malay_anki.curation.models import role_route
from indo_malay_anki.curation.records import validate_stage_response
from indo_malay_anki.curation.store import BatchStore, atomic_json
from indo_malay_anki.curation.workflow import current_results

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_historical_verifiers import call_model  # noqa: E402

SPEC = Path("specs/003-vocabulary-curation")
FROZEN = SPEC / "second-batch-50-policy-replay.json"
PRODUCTION = SPEC / "second-batch-50-state.json"
AUDIT = SPEC / "second-batch-50-audit.json"
OUT = SPEC / "second-batch-50-competing-form-replay.json"
REPORT = SPEC / "second-batch-50-competing-form-replay.md"
UNSAFE = {"should-hold", "should-reject", "materially-misleading"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verifier_for(prior: dict, ref: str) -> dict:
    return prior.get("historical_objection_results", {}).get(
        ref, prior["verifier_results"].get(ref, {})
    )


def inputs(prior: dict, production: dict) -> list[dict]:
    selected = []
    for ref, old in sorted(production["candidate_decisions"].items()):
        v = verifier_for(prior, ref)
        old_decision = prior["candidate_results"][ref]["replay"]
        if (
            old_decision["outcome"] == "accepted"
            and old_decision["relation"] == "different-common-word"
            and v.get("shared_synonym_case") == "useful-preference"
        ):
            selected.append(
                {
                    "ref": ref,
                    "candidate": old["candidate"],
                    "verifier_alternative_reason": v["shared_synonym_rationale"],
                    "verifier_risk_reason": v.get("risk_rationale", ""),
                    "verifier_cue_alignment": v.get("cue_alignment"),
                    "verifier_cue_rewrite": v.get("cue_rewrite", ""),
                }
            )
    return selected


def main() -> None:
    root = Path.cwd()
    paths = {"prior": FROZEN, "production": PRODUCTION, "audit": AUDIT}
    digests = {key: sha(root / path) for key, path in paths.items()}
    prior = json.loads((root / FROZEN).read_text())
    production = json.loads((root / PRODUCTION).read_text())
    audit = json.loads((root / AUDIT).read_text())
    if len(production["candidate_decisions"]) != 50 or len(audit["results"]) != 40:
        raise ValueError("fixed Batch 2 inputs changed")
    selected = inputs(prior, production)
    state = (
        json.loads((root / OUT).read_text())
        if (root / OUT).exists()
        else {
            "schema_version": 1,
            "input_digests": digests,
            "policy_version": "3.2.0",
            "prompt_set_version": "2.3.0",
            "selected_refs": [item["ref"] for item in selected],
            "attempts": [],
            "responses": {},
            "candidate_results": {},
        }
    )
    if state["input_digests"] != digests or state["selected_refs"] != [
        item["ref"] for item in selected
    ]:
        raise ValueError("frozen cohort changed during challenge replay")
    route = role_route(root, "competing-form-challenge")
    prompt = (root / "curation/prompts/versions/2.3.0/competing-form-challenge.md").read_text()
    start = time.perf_counter()
    for index in range(0, len(selected), 4):
        group = selected[index : index + 4]
        refs = [item["ref"] for item in group]
        if all(ref in state["responses"] for ref in refs):
            continue
        request = (
            prompt
            + "\nFor each candidate, first classify the named alternative as `none`, "
            + "`weak-alternative`, or `credible-everyday`. Return JSON object `items` "
            + "keyed by exact ref. Each item must contain `competing_form` with status, "
            + "form, language (`indonesian`, `malaysian`, `both`, `none`), same_sense "
            + "boolean, and concrete rationale. If and only if status is `credible-everyday`, "
            + "return `challenge` with outcome, assessment booleans, rationale, cue_rewrite, "
            + "usage_note, and support as specified above. Otherwise challenge must be null. "
            + "The four assessment keys must be EXACTLY "
            + "normal_everyday_same_sense, materially_weakens_preference, "
            + "useful_difference_remains, unqualified_card_misleads. "
            + "Use only these candidates and prior verifier leads; the independent audit "
            + "is hidden. A shared form is not automatically a veto.\n"
            + json.dumps(group, ensure_ascii=False, separators=(",", ":"))
        )
        valid = None
        for retry in range(2):
            with tempfile.TemporaryDirectory(prefix="myid-competitor-") as temp:
                attempt = call_model(
                    root,
                    Path(temp),
                    f"cal2-competing-{index // 4 + 1}-try-{retry + 1}",
                    route["model"],
                    request,
                    reasoning_effort=route["reasoning_effort"],
                )
            response = attempt.get("decision") or {}
            items = response.get("items", {}) if isinstance(response, dict) else {}
            try:
                if set(items) != set(refs):
                    raise ValueError("challenge response has missing or extra refs")
                for ref in refs:
                    item = items[ref]
                    competitor = item["competing_form"]
                    if competitor["status"] not in {
                        "none",
                        "weak-alternative",
                        "credible-everyday",
                    }:
                        raise ValueError(f"bad competing-form status for {ref}")
                    if not isinstance(competitor.get("rationale"), str):
                        raise ValueError(f"missing competing-form rationale for {ref}")
                    if competitor["status"] == "credible-everyday":
                        if not competitor.get("form") or not competitor.get("same_sense"):
                            raise ValueError(f"credible alternative is unnamed for {ref}")
                        validate_stage_response(
                            "competing-form-challenge",
                            {
                                "schema_version": 1,
                                "role": "competing-form-challenge",
                                "model": route["model"],
                                "result": item["challenge"],
                            },
                        )
                    elif item.get("challenge") is not None:
                        raise ValueError(f"challenge ran without credible rival for {ref}")
                valid = items
            except (KeyError, TypeError, ValueError) as exc:
                attempt["validation_error"] = str(exc)
                state.setdefault("invalid_responses", []).append(
                    {"refs": refs, "response": response, "error": str(exc)}
                )
            state["attempts"].append(
                {
                    key: value
                    for key, value in attempt.items()
                    if key not in {"decision", "response_text"}
                }
            )
            if valid is not None:
                state["responses"].update(valid)
                atomic_json(root / OUT, state)
                break
            atomic_json(root / OUT, state)
        if valid is None:
            raise RuntimeError(f"bounded competing-form challenge failed: {refs}")
        print("challenged group", index // 4 + 1, refs, flush=True)
    if "challenge_elapsed_seconds" not in state:
        state["challenge_elapsed_seconds"] = round(time.perf_counter() - start, 3)
    independent = [
        {
            "ref": ref,
            "candidate": production["candidate_decisions"][ref]["candidate"],
            "named_competing_form": response["competing_form"],
        }
        for ref, response in sorted(state["responses"].items())
        if response["competing_form"]["status"] == "credible-everyday"
    ]
    independent_start = time.perf_counter()
    for index in range(0, len(independent), 4):
        group = independent[index : index + 4]
        refs = [item["ref"] for item in group]
        if all(ref in state.get("independent_challenges", {}) for ref in refs):
            continue
        request = (
            prompt
            + "\nYou are independent of the first verifier. The only prior finding "
            + "supplied is a named potentially everyday competing form; its credibility "
            + "and effect are yours to challenge. Do not assume the proposed national "
            + "preference is true. Return JSON object `items` keyed by exact ref, with "
            + "each value a complete challenge result (no wrapper). Use exactly the "
            + "assessment keys normal_everyday_same_sense, materially_weakens_preference, "
            + "useful_difference_remains, unqualified_card_misleads. If model knowledge "
            + "cannot decide whether both forms are comparably ordinary, choose "
            + "preference-materially-uncertain. No audit results are provided.\n"
            + json.dumps(group, ensure_ascii=False, separators=(",", ":"))
        )
        valid = None
        for retry in range(2):
            with tempfile.TemporaryDirectory(prefix="myid-independent-competitor-") as temp:
                attempt = call_model(
                    root,
                    Path(temp),
                    f"cal2-independent-{index // 4 + 1}-try-{retry + 1}",
                    route["model"],
                    request,
                    reasoning_effort=route["reasoning_effort"],
                )
            response = attempt.get("decision") or {}
            items = response.get("items", {}) if isinstance(response, dict) else {}
            try:
                if set(items) != set(refs):
                    raise ValueError("independent challenge has missing or extra refs")
                for ref in refs:
                    validate_stage_response(
                        "competing-form-challenge",
                        {
                            "schema_version": 1,
                            "role": "competing-form-challenge",
                            "model": route["model"],
                            "result": items[ref],
                        },
                    )
                valid = items
            except (KeyError, TypeError, ValueError) as exc:
                attempt["validation_error"] = str(exc)
                state.setdefault("invalid_responses", []).append(
                    {"refs": refs, "response": response, "error": str(exc)}
                )
            state["attempts"].append(
                {
                    key: value
                    for key, value in attempt.items()
                    if key not in {"decision", "response_text"}
                }
            )
            if valid is not None:
                state.setdefault("independent_challenges", {}).update(valid)
                atomic_json(root / OUT, state)
                break
            atomic_json(root / OUT, state)
        if valid is None:
            raise RuntimeError(f"bounded independent challenge failed: {refs}")
        print("independent challenge", index // 4 + 1, refs, flush=True)
    if "independent_elapsed_seconds" not in state:
        state["independent_elapsed_seconds"] = round(time.perf_counter() - independent_start, 3)
    for ref, row in sorted(production["candidate_decisions"].items()):
        batch, cid = ref.split(":", 1)
        store = BatchStore(root, batch)
        if store.candidate(cid) != row["candidate"]:
            raise ValueError(f"candidate changed: {ref}")
        stages = {
            "normalize-and-dedupe": current_results(store, cid).get("normalize-and-dedupe", {})
        }
        verifier = verifier_for(prior, ref)
        if verifier:
            verifier = dict(verifier)
            response = state["responses"].get(ref)
            if response:
                verifier["competing_form"] = response["competing_form"]
                if response["competing_form"]["status"] == "credible-everyday":
                    stages["competing-form-challenge"] = state["independent_challenges"][ref]
            else:
                verifier["competing_form"] = {
                    "status": "weak-alternative"
                    if verifier.get("shared_synonym_case") == "nonpreferred-alternative"
                    else "none",
                    "form": "",
                    "language": "none",
                    "same_sense": False,
                    "rationale": (
                        "No credible everyday rival was identified in the frozen verifier record."
                    ),
                }
            stages["independent-verification"] = verifier
            if ref in prior.get("historical_objection_results", {}):
                stages["adversarial-review"] = {
                    "verdict": "object",
                    "objections": row["reason_codes"],
                }
        else:
            stages["relation-proposal"] = {"relation": "same", "aligned": True}
        decision = decide_candidate(row["candidate"], stages, policy_version="3.2.0")
        state["candidate_results"][ref] = {
            "previous": prior["candidate_results"][ref]["replay"],
            "new": decision,
            "audit_verdict": audit["results"].get(ref, {}).get("verdict"),
        }
    atomic_json(root / OUT, state)
    report(root, state)


def report(root: Path, state: dict) -> None:
    rows = state["candidate_results"]
    outcomes = Counter(item["new"]["outcome"] for item in rows.values())
    tiers = Counter(
        item["new"].get("confidence_tier")
        for item in rows.values()
        if item["new"]["outcome"] == "accepted"
    )
    challenge_outcomes = Counter(
        item["outcome"] for item in state.get("independent_challenges", {}).values()
    )
    credible = sum(
        item["competing_form"]["status"] == "credible-everyday"
        for item in state["responses"].values()
    )
    changed = [
        ref for ref, item in rows.items() if item["previous"]["outcome"] != item["new"]["outcome"]
    ]
    unsafe_rows = {ref: item for ref, item in rows.items() if item["audit_verdict"] in UNSAFE}
    production_caught = {
        ref for ref, item in unsafe_rows.items() if item["new"]["outcome"] in {"hold", "rejected"}
    }
    audit_queue = set()
    for ref, item in rows.items():
        decision = item["new"]
        if decision["outcome"] != "accepted":
            continue
        tier = decision.get("confidence_tier")
        flags = set(decision.get("review_flags", []))
        if tier in {"low", "very-low"} or decision["relation"] == "false-friend":
            audit_queue.add(ref)
        elif flags & {
            "competing-form-qualified",
            "competing-form-reviewed",
            "concrete-nonblocking-risk",
            "historical-objection",
        }:
            audit_queue.add(ref)
        elif tier == "medium" and int(hashlib.sha256(ref.encode()).hexdigest(), 16) % 4 == 0:
            audit_queue.add(ref)
        elif tier == "high" and int(hashlib.sha256(ref.encode()).hexdigest(), 16) % 10 == 0:
            audit_queue.add(ref)
    unsafe_audit = set(unsafe_rows) & audit_queue
    known_good = {ref for ref, item in rows.items() if item["audit_verdict"] == "confirmed-good"}
    attempts = state["attempts"]
    input_tokens = sum(x.get("input_tokens") or 0 for x in attempts)
    output_tokens = sum(x.get("output_tokens") or 0 for x in attempts)
    lines = [
        "# Batch 2 targeted competing-form replay",
        "",
        "This is a read-only replay of the same 50 candidates. The prior production decisions, "
        "v3.1 replay, independent audit, and 34-card promotion preview remain unchanged.",
        "",
        f"- Decisions: {dict(outcomes)}; accepted confidence: {dict(tiers)}",
        f"- Potential named-alternative records inspected: {len(state['selected_refs'])}; "
        f"credible everyday competitors: {credible}",
        f"- Challenge outcomes: {dict(challenge_outcomes)}",
        f"- Added model calls: {len(attempts)}; "
        f"detector elapsed: {state['challenge_elapsed_seconds']} s; "
        f"independent challenge elapsed: {state['independent_elapsed_seconds']} s; "
        f"input/output tokens: {input_tokens}/{output_tokens}; monetary cost unavailable",
        f"- Changed decisions from v3.1: {len(changed)} — {', '.join(changed) or 'none'}",
        "",
        "## Six known unsafe or unresolved cards",
        "",
        "| Candidate | Original | v3.1 | Trigger | Challenge | v3.2 | Audit agrees? |",
        "|---|---|---|---|---|---|---|",
    ]
    production = json.loads((root / PRODUCTION).read_text())
    for ref, item in sorted(unsafe_rows.items()):
        original = production["candidate_decisions"][ref]["outcome"]
        response = state["responses"].get(ref, {})
        challenge = state.get("independent_challenges", {}).get(ref, {})
        now = item["new"]
        agreement = "yes" if now["outcome"] in {"hold", "rejected"} else "no"
        lines.append(
            f"| {ref} | {original} | {item['previous']['outcome']} | "
            f"{response.get('competing_form', {}).get('status', 'none')} | "
            f"{challenge.get('outcome', '—')} | {now['outcome']} / "
            f"{now.get('confidence_tier', '—')} | {agreement} |"
        )
    lines += [
        "",
        "## Simulated targeted audit",
        "",
        "Audit all accepted low/very-low and false friends; audit medium/high with concrete "
        "review flags (including a named credible competitor) plus deterministic 25% "
        "medium and 10% high samples.",
        "",
        f"- Accepted routed to audit: {len(audit_queue)}",
        f"- Known unsafe caught by production HOLD/REJECT: {len(production_caught)} / 6",
        f"- Remaining known unsafe routed to audit: {len(unsafe_audit - production_caught)} / 6",
        f"- Total known unsafe caught by production plus simulated audit: "
        f"{len(production_caught | unsafe_audit)} / 6",
        f"- Confirmed-good cards routed to audit: {len(known_good & audit_queue)} / 24",
        "",
        "## Candidate outcomes",
        "",
        "| Candidate | v3.1 | Competitor | Challenge | v3.2 | Audit |",
        "|---|---|---|---|---|---|",
    ]
    for ref, item in sorted(rows.items()):
        response = state["responses"].get(ref, {})
        lines.append(
            f"| {ref} | {item['previous']['outcome']} | "
            f"{response.get('competing_form', {}).get('status', 'none')} | "
            f"{state.get('independent_challenges', {}).get(ref, {}).get('outcome', '—')} | "
            f"{item['new']['outcome']} / {item['new'].get('confidence_tier', '—')} | "
            f"{item['audit_verdict'] or 'not audited'} |"
        )
    (root / REPORT).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(dict(outcomes), dict(tiers), "credible", credible, "calls", len(attempts), flush=True)


if __name__ == "__main__":
    main()
