"""Parent-run lifecycle and orchestration over Feature 003 slices."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime

from indo_malay_anki.curation.records import validate_stage_response
from indo_malay_anki.curation.report import batch_report
from indo_malay_anki.curation.store import BatchStore, atomic_json, read_json
from indo_malay_anki.curation.workflow import (
    check_candidate,
    current_results,
    finalize_hold,
    finalize_reject,
    ingest_response,
    init_batch,
    packet_for,
    reopen_accepted_for_correction,
    reopen_candidate,
    revise_candidate,
)

from .provider import call_model
from .redundancy import ExclusionIndex
from .store import RunError, RunStore, digest, file_digest

TRANSITIONS = {
    "draft": {"allocation-approved"},
    "allocation-approved": {"generating"},
    "generating": {"curating"},
    "curating": {"awaiting-risk-audit"},
    "awaiting-risk-audit": {"promotion-ready"},
    "promotion-ready": {"promoting", "qa-monitoring"},
    "promoting": {"promotion-ready", "qa-monitoring"},
    "qa-monitoring": {"complete", "promotion-ready"},
    "complete": set(),
}


def transition(store: RunStore, new_state: str, *, reason: str | None = None) -> dict:
    manifest = store.load()
    prior = manifest["state"]
    if prior == "complete":
        raise RunError("complete run is terminal")
    if new_state == prior:
        return manifest
    if new_state not in TRANSITIONS.get(prior, set()):
        raise RunError(f"invalid transition: {prior} -> {new_state}")
    updated = {**manifest, "state": new_state}
    store.save(updated, expected_digest=store.manifest_digest())
    store.append_event(
        "state", "complete", details={"from": prior, "to": new_state, "reason": reason}
    )
    return store.load()


def pause(store: RunStore, reason: str) -> dict:
    manifest = store.load()
    if manifest["state"] == "complete":
        raise RunError("complete run is terminal")
    if manifest["state"] == "paused":
        return manifest
    if not reason.strip():
        raise RunError("pause requires a reason")
    updated = {**manifest, "prior_state": manifest["state"], "state": "paused"}
    store.save(updated, expected_digest=store.manifest_digest())
    store.append_event("pause", "complete", details={"reason": reason})
    return store.load()


def resume(store: RunStore, resolution: str) -> dict:
    manifest = store.load()
    if manifest["state"] != "paused" or not manifest.get("prior_state"):
        raise RunError("run is not paused")
    if not resolution.strip():
        raise RunError("resume requires a resolution")
    updated = {**manifest, "state": manifest["prior_state"], "prior_state": None}
    store.save(updated, expected_digest=store.manifest_digest())
    store.append_event("resume", "complete", details={"resolution": resolution})
    return store.load()


def checkpoint_current(store: RunStore, kind: str, input_digest: str) -> bool:
    """Completed work is reusable only if its referenced output still matches."""
    return store.completed_checkpoint(kind, input_digest) is not None


def reconcile_artifacts(store: RunStore) -> dict[str, str]:
    """Check recorded slice and canonical artifact digests before resuming work."""
    manifest = store.load()
    mismatches: dict[str, str] = {}
    if manifest["state"] in {
        "allocation-approved",
        "generating",
        "curating",
        "awaiting-risk-audit",
    } and manifest.get("baseline_source_digest"):
        source = store.root / "data" / "vocabulary.tsv"
        if not source.exists() or file_digest(source) != manifest["baseline_source_digest"]:
            mismatches["baseline_source_digest"] = str(source)
    references = list(manifest.get("slices", []))
    for field, path in (
        ("source_digest", store.root / "data" / "vocabulary.tsv"),
        ("ledger_digest", store.root / "curation" / "id-ledger.json"),
    ):
        if manifest.get(field):
            if not path.exists() or file_digest(path) != manifest[field]:
                mismatches[field] = str(path)
    for reference in references:
        from indo_malay_anki.curation.store import BatchStore

        slice_store = BatchStore(store.root, reference["slice_id"])
        if not slice_store.path.exists() or set(slice_store.candidate_ids()) != set(
            reference.get("candidate_ids", [])
        ):
            mismatches[reference["slice_id"]] = "candidate roster mismatch"
            continue
        if not reference.get("manifest_digest"):
            continue
        path = store.root / "curation" / "batches" / reference["slice_id"] / "manifest.json"
        if not path.exists() or file_digest(path) != reference["manifest_digest"]:
            mismatches[reference["slice_id"]] = str(path)
    return mismatches


def _generation_prompt(store: RunStore, slice_store: BatchStore, category: str, count: int) -> str:
    packet = packet_for(slice_store, "generate")
    request = {
        "run_id": store.run_id,
        "slice_id": slice_store.batch_id,
        "category": category,
        "count": count,
        "instruction": (
            "Return exactly count common, useful contrastive concepts in this category. "
            "Prioritize different-common-word, then useful similar, then valuable false-friend. "
            "Avoid identical forms, semantic synonyms, and anything in the archive. "
            "Use unique candidate IDs within this slice and the existing generate response schema."
        ),
    }
    return (
        packet["prompt"]
        + "\nCURATION_PACKET_JSON\n"
        + json.dumps(packet, ensure_ascii=False)
        + "\nSCALING_REQUEST_JSON\n"
        + json.dumps(request)
    )


def _envelope_response(role: str, answer: dict) -> dict:
    """Adapt a model's prompt-native result to Feature 003's ingest envelope."""
    raw = answer["response"]
    if (
        isinstance(raw, dict)
        and raw.get("schema_version") == 1
        and raw.get("role") == role
        and isinstance(raw.get("model"), str)
        and raw["model"].strip()
        and isinstance(raw.get("result"), dict)
    ):
        return raw
    if not isinstance(raw, dict):
        raise RunError("model response must be a JSON object")
    if role == "generate" and isinstance(raw.get("candidates"), list):
        result = {"candidates": raw["candidates"]}
    elif role == "normalize-and-dedupe" and isinstance(raw.get("overlaps"), list):
        result = raw
    elif role != "generate" and (raw.get("type") == role or raw.get("role") == role):
        result = {
            key: value for key, value in raw.items() if key not in {"type", "version", "role"}
        }
    else:
        result = raw
    return {
        "schema_version": 1,
        "role": role,
        "model": answer.get("model") or raw.get("model") or "unknown",
        "result": result,
    }


def _archive_failed_capture(store: RunStore, path, *, kind: str, error: Exception) -> None:
    failed = path.parent / "failed"
    failed.mkdir(parents=True, exist_ok=True)
    ordinal = 1
    while (failed / f"{path.stem}-attempt-{ordinal:03d}.json").exists():
        ordinal += 1
    archived = failed / f"{path.stem}-attempt-{ordinal:03d}.json"
    path.replace(archived)
    store.append_event(
        kind,
        "failed",
        details={
            "response_path": str(archived.relative_to(store.root)),
            "error": str(error),
        },
    )


def _recover_generation_capture(store: RunStore, answer_path, count: int) -> dict | None:
    """Revalidate retained attempts after a compatible adapter repair."""
    failed = answer_path.parent / "failed"
    for path in sorted(failed.glob(f"{answer_path.stem}-attempt-*.json"), reverse=True):
        answer = read_json(path)
        try:
            response = _envelope_response("generate", answer)
            validated = validate_stage_response("generate", response, limit=count)
            if len(validated["result"]["candidates"]) != count:
                continue
        except (KeyError, TypeError, ValueError):
            continue
        atomic_json(answer_path, answer)
        store.append_event(
            "generation-response-recovery",
            "complete",
            details={
                "source_path": str(path.relative_to(store.root)),
                "active_path": str(answer_path.relative_to(store.root)),
            },
        )
        return answer
    return None


def generate_run(store: RunStore, *, provider=call_model, semantic_provider=call_model) -> dict:
    """Fill a frozen allocation through at-most-12-candidate Feature 003 slices.

    Persist every provider answer before validating it. A retry replays that answer,
    so an interruption after the expensive call cannot regenerate its proposals.
    """
    manifest = store.load()
    if (
        manifest["state"] == "curating"
        and manifest["admitted_count"] == manifest["requested_count"]
    ):
        return manifest
    if manifest["state"] not in {"allocation-approved", "generating"}:
        raise RunError("generation requires approved allocation")
    if manifest["allocation"] is None:
        raise RunError("allocation is not frozen")
    if reconcile_artifacts(store):
        raise RunError("run artifacts changed before generation resume")
    if manifest["state"] == "allocation-approved":
        manifest = transition(store, "generating")
    index = ExclusionIndex.from_root(store.root, store.run_id)
    admitted_by_category = {category: 0 for category in manifest["allocation"]}
    for item in manifest["slices"]:
        admitted_by_category[item["category"]] += item["admitted"]
    proposed = manifest.get("proposed_count", 0)
    for category, target in manifest["allocation"].items():
        while admitted_by_category[category] < target:
            manifest = store.load()
            if proposed >= manifest["proposal_cap"]:
                pause(store, "proposal cap reached before requested count")
                raise RunError("proposal cap reached before requested count")
            ordinal = len(manifest["slices"]) + 1
            slice_id = f"{store.run_id}-s{ordinal:03d}"
            count = min(
                12, target - admitted_by_category[category], manifest["proposal_cap"] - proposed
            )
            slice_store = BatchStore(store.root, slice_id)
            if not slice_store.path.exists():
                slice_store = init_batch(store.root, slice_id, category, count)
            answer_path = store.path / "generation-responses" / f"{slice_id}.json"
            if answer_path.exists():
                answer = read_json(answer_path)
            else:
                answer = _recover_generation_capture(store, answer_path, count)
                if answer is None:
                    answer = provider(
                        store.root,
                        "generate",
                        _generation_prompt(store, slice_store, category, count),
                    )
                    atomic_json(answer_path, answer)
            try:
                response = _envelope_response("generate", answer)
                validated = validate_stage_response("generate", response, limit=count)
                proposals = validated["result"]["candidates"]
                if len(proposals) != count:
                    raise RunError(
                        f"generation slice {slice_id} returned {len(proposals)} proposals; "
                        f"expected {count}"
                    )
            except (KeyError, TypeError, ValueError) as exc:
                _archive_failed_capture(store, answer_path, kind="generation-response", error=exc)
                raise
            screen_path = store.path / "generation-responses" / f"{slice_id}-screen.json"
            if screen_path.exists():
                screen = read_json(screen_path)
                if (
                    screen.get("response_digest")
                    != hashlib.sha256(json.dumps(response, sort_keys=True).encode()).hexdigest()
                ):
                    raise RunError("captured generation response changed during resume")
                admitted = screen["admitted_candidates"]
                screened = screen["screened"]
            else:
                admitted = []
                screened = []
                for candidate in proposals:

                    def resolve_semantic(new, old, *, slice_id=slice_id):
                        review_path = (
                            store.path
                            / "generation-responses"
                            / "semantic"
                            / f"{slice_id}--{new['candidate_id']}.json"
                        )
                        packet = {
                            "new": new,
                            "prior": old,
                            "task": "same concept or distinct sense",
                        }
                        packet_digest = digest(packet)
                        if review_path.exists():
                            review = read_json(review_path)
                            if review["packet_digest"] != packet_digest:
                                raise RunError("stale semantic review response")
                        else:
                            prompt = (
                                "Compare two vocabulary concept records. Return only JSON with "
                                "outcome ('same' or 'distinct') and a short candidate-specific "
                                "rationale. Distinct means meaningfully different English sense "
                                "and contrast, not merely alternate English wording.\n"
                                + json.dumps(packet, ensure_ascii=False)
                            )
                            answer = semantic_provider(store.root, "generate", prompt)
                            review = {"packet_digest": packet_digest, **answer}
                            atomic_json(review_path, review)
                        outcome = review["response"].get("outcome")
                        if outcome not in {"same", "distinct"}:
                            raise RunError("semantic review returned invalid outcome")
                        store.append_event(
                            "semantic-review",
                            "complete",
                            details={
                                "slice_id": slice_id,
                                "candidate_id": new["candidate_id"],
                                "prior_ref": old["ref"],
                                "outcome": outcome,
                                "rationale": review["response"].get("rationale"),
                                "elapsed_ms": review.get("elapsed_ms"),
                                "model_calls": review.get("model_calls"),
                                "input_tokens": review.get("input_tokens"),
                                "output_tokens": review.get("output_tokens"),
                            },
                        )
                        return outcome

                    result = index.screen(candidate, resolver=resolve_semantic)
                    if result["outcome"] in {"admitted", "distinct-sense"}:
                        admitted.append(candidate)
                        index.add(f"{slice_id}:{candidate['candidate_id']}", candidate)
                    else:
                        screened.append(
                            {"candidate_id": candidate["candidate_id"], "reason": result["outcome"]}
                        )
                atomic_json(
                    screen_path,
                    {
                        "proposed": len(proposals),
                        "admitted": len(admitted),
                        "admitted_candidates": admitted,
                        "screened": screened,
                        "response_digest": hashlib.sha256(
                            json.dumps(response, sort_keys=True).encode()
                        ).hexdigest(),
                    },
                )
            accepted_response = {**response, "result": {"candidates": admitted}}
            ingest_response(
                slice_store,
                "generate",
                json.dumps(accepted_response),
                actual_model=answer.get("model"),
            )
            entry = {
                "slice_id": slice_id,
                "category": category,
                "requested": count,
                "proposed": len(proposals),
                "admitted": len(admitted),
                "candidate_ids": [item["candidate_id"] for item in admitted],
                "screened": screened,
                "elapsed_ms": answer.get("elapsed_ms"),
                "input_tokens": answer.get("input_tokens"),
                "output_tokens": answer.get("output_tokens"),
            }
            updated = {
                **manifest,
                "slices": [*manifest["slices"], entry],
                "admitted_count": manifest["admitted_count"] + len(admitted),
                "screened_out_count": manifest.get("screened_out_count", 0) + len(screened),
                "proposed_count": proposed + len(proposals),
            }
            store.save(updated, expected_digest=store.manifest_digest())
            store.append_event("generation-slice", "complete", details=entry)
            from .qa import evaluate_brakes

            evaluate_brakes(store)
            proposed += len(proposals)
            admitted_by_category[category] += len(admitted)
    manifest = store.load()
    if manifest["admitted_count"] != manifest["requested_count"]:
        raise RunError("generation count did not match frozen allocation")
    return transition(store, "curating")


def _curation_stage(
    store: RunStore,
    slice_store: BatchStore,
    candidate_id: str,
    role: str,
    provider,
) -> None:
    if role in current_results(slice_store, candidate_id):
        return
    packet = packet_for(slice_store, role, candidate_id)
    folder = store.path / "curation-responses" / slice_store.batch_id / candidate_id
    path = folder / f"{role}.json"
    if path.exists():
        captured = read_json(path)
        if captured.get("input_digest") != packet["input_digest"]:
            raise RunError(f"stale captured response: {slice_store.batch_id}:{candidate_id}:{role}")
    else:
        try:
            prompt = (
                packet["prompt"]
                + "\nCURATION_PACKET_JSON\n"
                + json.dumps(packet, ensure_ascii=False)
            )
            answer = provider(store.root, role, prompt)
        except Exception as exc:
            store.append_event(
                "curation-call",
                "failed",
                input_digest=packet["input_digest"],
                details={
                    "slice_id": slice_store.batch_id,
                    "candidate_id": candidate_id,
                    "role": role,
                    "error": str(exc),
                },
            )
            raise
        captured = {"input_digest": packet["input_digest"], **answer}
        atomic_json(path, captured)
    try:
        ingest_response(
            slice_store,
            role,
            json.dumps(_envelope_response(role, captured)),
            candidate_id,
            actual_model=captured.get("model"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        _archive_failed_capture(store, path, kind="curation-response", error=exc)
        raise
    store.append_event(
        "curation-call",
        "complete",
        input_digest=packet["input_digest"],
        details={
            "slice_id": slice_store.batch_id,
            "candidate_id": candidate_id,
            "role": role,
            "elapsed_ms": captured.get("elapsed_ms"),
            "input_tokens": captured.get("input_tokens"),
            "output_tokens": captured.get("output_tokens"),
            "model_calls": captured.get("model_calls"),
            "retrievals": captured.get("retrievals"),
        },
    )


def curate_run(store: RunStore, *, provider=call_model) -> dict:
    """Run the frozen v3.1 optimistic stage route and close settled slices."""
    manifest = store.load()
    if manifest["state"] not in {
        "curating",
        "awaiting-risk-audit",
        "promotion-ready",
        "qa-monitoring",
    }:
        raise RunError("curation requires a generated run")
    if reconcile_artifacts(store):
        raise RunError("run artifacts changed before curation resume")
    for item in manifest["slices"]:
        if not item["candidate_ids"]:
            continue
        slice_store = BatchStore(store.root, item["slice_id"])
        if slice_store.manifest().decision_policy_version != "3.1.0":
            raise RunError("production slice does not use frozen policy v3.1")
        for candidate_id in item["candidate_ids"]:
            if slice_store.manifest().status == "closed":
                continue
            if check_candidate(slice_store, candidate_id)["outcome"] in {"hold", "rejected"}:
                continue
            stages = current_results(slice_store, candidate_id)
            if "normalize-and-dedupe" not in stages:
                _curation_stage(store, slice_store, candidate_id, "normalize-and-dedupe", provider)
            decision = check_candidate(slice_store, candidate_id)
            if decision["outcome"] == "rejected":
                continue
            stages = current_results(slice_store, candidate_id)
            if "independent-verification" not in stages:
                _curation_stage(
                    store, slice_store, candidate_id, "independent-verification", provider
                )
            decision = check_candidate(slice_store, candidate_id)
            if decision["outcome"] in {"accepted", "rejected"}:
                continue
            verifier = current_results(slice_store, candidate_id).get(
                "independent-verification", {}
            )
            if (
                decision.get("relation") == "false-friend"
                and verifier.get("verdict") == "agree"
                and not verifier.get("material_concerns")
            ):
                for role in (
                    "indonesian-usage",
                    "malaysian-usage",
                    "relation-proposal",
                    "evidence-audit",
                    "adversarial-review",
                ):
                    if role not in current_results(slice_store, candidate_id):
                        _curation_stage(store, slice_store, candidate_id, role, provider)
                check_candidate(slice_store, candidate_id)
        report = batch_report(slice_store)
        store.append_event(
            "curation-slice",
            "complete",
            details={
                "slice_id": item["slice_id"],
                "accepted": report["accepted"],
                "held": report["held"],
                "rejected": report["rejected"],
                "pending": report["pending"],
            },
        )
        from .qa import evaluate_brakes

        evaluate_brakes(store)
    if all(
        not item["candidate_ids"]
        or BatchStore(store.root, item["slice_id"]).manifest().status == "closed"
        for item in manifest["slices"]
    ):
        if manifest["state"] == "curating":
            return transition(store, "awaiting-risk-audit")
    return store.load()


def resolve_candidate(
    store: RunStore,
    reference: str,
    action: str,
    reason: str,
    *,
    changes: dict | None = None,
    reason_code: str | None = None,
) -> dict:
    from indo_malay_anki.curation.ids import assigned_id, load_ledger

    from .promotion import withdraw_candidate

    slice_id, separator, candidate_id = reference.partition(":")
    if not separator or not reason.strip() or action not in {"correct", "hold", "reject"}:
        raise RunError("resolve requires slice:candidate, action, and reason")
    if action == "correct" and not changes:
        raise RunError("correction requires changed fields")
    if action == "reject" and not reason_code:
        raise RunError("rejection requires an affirmative reason code")
    manifest = store.load()
    if not any(
        item["slice_id"] == slice_id and candidate_id in item["candidate_ids"]
        for item in manifest["slices"]
    ):
        raise RunError("candidate is not in this production run")
    slice_store = BatchStore(store.root, slice_id)
    assigned = assigned_id(load_ledger(store.root), slice_id, candidate_id)
    if assigned:
        withdraw_candidate(store, slice_id, candidate_id, reason=reason)
    if slice_store.manifest().status == "closed":
        decision = check_candidate(slice_store, candidate_id)
        if decision["outcome"] == "accepted":
            reopen_accepted_for_correction(slice_store, candidate_id, reason)
        else:
            reopen_candidate(slice_store, candidate_id, reason)
    if action == "correct":
        result = revise_candidate(slice_store, candidate_id, changes, reason)
    elif action == "hold":
        result = finalize_hold(slice_store, candidate_id, reason)
    else:
        result = finalize_reject(slice_store, candidate_id, reason, reason_code=reason_code)
    batch_report(slice_store)
    store.append_event(
        "correction",
        "complete",
        details={
            "slice_id": slice_id,
            "candidate_id": candidate_id,
            "action": action,
            "reason": reason,
            "changes": changes,
            "reason_code": reason_code,
        },
    )
    return result


def build_run(store: RunStore) -> dict:
    from indo_malay_anki.builder import OUTPUT_RELATIVE_PATH, build_package
    from indo_malay_anki.validator import validate_vocabulary

    manifest = store.load()
    if manifest["state"] not in {"promotion-ready", "qa-monitoring"}:
        raise RunError("build requires completed production decisions")
    if (store.root / "curation" / "export-journal.json").exists():
        raise RunError("cannot build while export recovery is pending")
    started = time.perf_counter()
    vocabulary = validate_vocabulary(store.root / "data" / "vocabulary.tsv", store.root / "media")
    output = build_package(vocabulary, store.root / OUTPUT_RELATIVE_PATH, store.root / "templates")
    result = {
        "source_digest": file_digest(store.root / "data" / "vocabulary.tsv"),
        "package_digest": file_digest(output),
        "notes": len(vocabulary.concepts),
        "cards": len(vocabulary.concepts),
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "built_at": datetime.now(UTC).isoformat(),
    }
    atomic_json(store.path / "build.json", result)
    store.append_event("build", "complete", details=result)
    return result


def close_run(store: RunStore) -> dict:
    from .qa import clean_population
    from .report import run_report

    manifest = store.load()
    if manifest["state"] != "qa-monitoring":
        raise RunError("closure requires QA-monitoring state")
    if manifest["admitted_count"] != manifest["requested_count"]:
        raise RunError("closure requires the requested admitted count")
    if any(item.get("active") for item in manifest.get("brakes", [])):
        raise RunError("active safety brake blocks closure")
    if (store.root / "curation" / "export-journal.json").exists():
        raise RunError("unresolved export journal blocks closure")
    roster_path = store.path / "qa" / "roster.json"
    if not roster_path.exists():
        raise RunError("random QA roster has not been selected")
    roster = read_json(roster_path)
    if roster["population_digest"] != digest(clean_population(store)):
        raise RunError("random QA roster is stale")
    for item in roster["sample"]:
        path = store.path / "qa" / "findings" / f"{item['slice_id']}--{item['candidate_id']}.json"
        if not path.exists():
            raise RunError("random QA sample is incomplete")
        finding = read_json(path)
        if not finding["resolved"]:
            raise RunError("unresolved material QA finding")
    build_path = store.path / "build.json"
    if not build_path.exists() or read_json(build_path)["source_digest"] != file_digest(
        store.root / "data" / "vocabulary.tsv"
    ):
        raise RunError("current canonical source has no valid offline build")
    report = run_report(store, final=False)
    if sum(report["decision_counts"].values()) != manifest["requested_count"]:
        raise RunError("final decision counts do not reconcile")
    if report["decision_counts"].get("pending", 0):
        raise RunError("pending production decisions block closure")
    if report["risk_audit"]["pending"]:
        raise RunError("pending risk audit dispositions block closure")
    from indo_malay_anki.builder import OUTPUT_RELATIVE_PATH

    package = store.root / OUTPUT_RELATIVE_PATH
    if not package.exists() or read_json(build_path)["package_digest"] != file_digest(package):
        raise RunError("offline build artifact is missing or stale")
    transition(store, "complete")
    return run_report(store, final=True)
