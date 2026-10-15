"""Ordered prompt exchange and resumable candidate stage records."""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .duplicates import find_deterministic_overlaps, has_self_overlap
from .gate import decide_candidate, preaudit_reasons, preverification_reasons
from .packets import digest, make_packet
from .records import (
    AI_ROLES,
    BatchManifest,
    RecordError,
    validate_candidate,
    validate_stage_response,
)
from .store import BatchStore, atomic_json, read_json

DEPENDENCIES = {
    "normalize-and-dedupe": ("generate",),
    "indonesian-usage": ("normalize-and-dedupe",),
    "malaysian-usage": ("normalize-and-dedupe",),
    "relation-proposal": ("indonesian-usage", "malaysian-usage"),
    "evidence-audit": ("relation-proposal",),
    "independent-verification": ("evidence-audit",),
    "adversarial-review": ("independent-verification",),
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def init_batch(
    root: Path, batch_id: str, topic: str, limit: int, scope: str = "Everyday usage"
) -> BatchStore:
    config_path = root / "curation" / "config.json"
    if not config_path.exists():
        config_path = Path(__file__).resolve().parents[3] / "curation" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest = BatchManifest.from_dict(
        {
            "batch_id": batch_id,
            "topic": topic,
            "scope": scope,
            "candidate_limit": limit,
            "prompt_set_version": config["prompt_set_version"],
            "created_at": utc_now(),
            "status": "open",
        }
    )
    store = BatchStore(root, batch_id)
    store.create(manifest)
    # Freeze a compact concept index before discovery, so later batches do not spend
    # generation and review calls rediscovering concepts already investigated.
    prior = archive_candidates(root, batch_id)
    atomic_json(
        store.path / "generation-archive-snapshot.json",
        [
            {
                "reference": item.get("candidate_id") or item.get("id"),
                "english": item.get("english", ""),
                "indonesian": item.get("indonesian", ""),
                "malaysian": item.get("malaysian", ""),
            }
            for item in prior
        ],
    )
    return store


def archive_candidates(
    root: Path, batch_id: str, candidate_id: str | None = None
) -> list[dict[str, Any]]:
    archive: list[dict[str, Any]] = []
    batches = root / "curation" / "batches"
    if batches.exists():
        for folder in sorted(batches.iterdir()):
            if not folder.is_dir():
                continue
            store = BatchStore(root, folder.name)
            for other_id in store.candidate_ids():
                if folder.name == batch_id and other_id == candidate_id:
                    continue
                item = store.candidate(other_id)
                archive.append({**item, "candidate_id": f"{folder.name}:{other_id}"})
    source = root / "data" / "vocabulary.tsv"
    if source.exists():
        with source.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                archive.append(
                    {key: row.get(key, "") for key in ("id", "english", "indonesian", "malaysian")}
                )
    return archive


def frozen_archive(store: BatchStore, candidate_id: str) -> list[dict[str, Any]]:
    """Keep a batch's research archive stable as later batches are created."""
    candidate_path = store.candidate_path(candidate_id) / "archive-snapshot.json"
    path = candidate_path if candidate_path.exists() else store.path / "archive-snapshot.json"
    if path.exists():
        archive = read_json(path)
        if not isinstance(archive, list):
            raise RecordError("archive snapshot must be a list")
    else:
        archive = archive_candidates(store.root, store.batch_id)
        atomic_json(path, archive)
    own_id = f"{store.batch_id}:{candidate_id}"
    return [item for item in archive if item.get("candidate_id") != own_id]


def _latest(events: tuple[dict[str, Any], ...], role: str) -> dict[str, Any] | None:
    return next((event for event in reversed(events) if event.get("role") == role), None)


def _namespace_claim_ids(role: str, result: dict[str, Any]) -> dict[str, Any]:
    """Give each role its own claim IDs without changing the AI's claim text."""
    if role not in {"indonesian-usage", "malaysian-usage", "relation-proposal"}:
        return result
    prefix = f"{role}:"
    namespaced = dict(result)
    claims = []
    for claim in result["claims"]:
        claim_id = claim["claim_id"]
        claims.append(
            {**claim, "claim_id": claim_id if claim_id.startswith(prefix) else prefix + claim_id}
        )
    namespaced["claims"] = claims
    leads = result.get("source_leads")
    if isinstance(leads, list):
        namespaced["source_leads"] = [
            {
                **lead,
                "claim_ids": [
                    claim_id if claim_id.startswith(prefix) else prefix + claim_id
                    for claim_id in lead.get("claim_ids", [])
                ],
            }
            if isinstance(lead, dict)
            else lead
            for lead in leads
        ]
    contrast = result.get("contrast")
    if isinstance(contrast, dict):
        namespaced["contrast"] = {
            **contrast,
            "claim_ids": [
                claim_id if claim_id.startswith(prefix) else prefix + claim_id
                for claim_id in contrast.get("claim_ids", [])
            ],
        }
    return namespaced


def current_results(store: BatchStore, candidate_id: str) -> dict[str, dict[str, Any]]:
    """Reuse only successful records whose current packet digest still matches."""
    manifest = store.manifest()
    candidate = store.candidate(candidate_id)
    results: dict[str, dict[str, Any]] = {}
    generation = _latest(store.batch_events(), "generate")
    if generation and generation.get("status") == "complete":
        packet = packet_for(store, "generate")
        if generation.get("input_digest") == packet["input_digest"]:
            results["generate"] = generation["result"]
    events = store.events(candidate_id)
    for role in AI_ROLES[1:]:
        if any(required not in results for required in DEPENDENCIES[role]):
            continue
        event = _latest(events, role)
        if event is None or event.get("status") != "complete":
            continue
        if role == "independent-verification":
            verifier_position = max(index for index, item in enumerate(events) if item is event)
            relation_position = max(
                index
                for index, item in enumerate(events)
                if item.get("role") == "relation-proposal" and item.get("status") == "complete"
            )
            if relation_position > verifier_position:
                continue
        archive = frozen_archive(store, candidate_id) if role == "normalize-and-dedupe" else None
        deterministic = (
            find_deterministic_overlaps(candidate, archive or []) if archive is not None else None
        )
        packet = make_packet(
            store.root,
            manifest,
            role,
            candidate=candidate,
            stages=results,
            archive=archive,
            deterministic_overlaps=deterministic,
        )
        if role == "normalize-and-dedupe" and event.get("input_digest") != packet["input_digest"]:
            legacy = archive_candidates(store.root, store.batch_id, candidate_id)
            legacy_packet = make_packet(
                store.root,
                manifest,
                role,
                candidate=candidate,
                stages=results,
                archive=legacy,
                deterministic_overlaps=find_deterministic_overlaps(candidate, legacy),
            )
            if event.get("input_digest") == legacy_packet["input_digest"]:
                archive = legacy
                packet = legacy_packet
        if (
            role == "independent-verification"
            and event.get("input_digest") != packet["input_digest"]
            and "relation_proposal_digest" not in event
        ):
            legacy_packet = make_packet(
                store.root,
                manifest,
                role,
                candidate=candidate,
                stages=results,
                bind_relation=False,
            )
            if event.get("input_digest") == legacy_packet["input_digest"]:
                packet = legacy_packet
        if event.get("input_digest") == packet["input_digest"]:
            results[role] = event["result"]
    return results


def packet_for(store: BatchStore, role: str, candidate_id: str | None = None) -> dict[str, Any]:
    manifest = store.manifest()
    if role == "generate":
        archive_path = store.path / "generation-archive-snapshot.json"
        archive = read_json(archive_path) if archive_path.exists() else None
        if archive is not None and not isinstance(archive, list):
            raise RecordError("generation archive snapshot must be a list")
        return make_packet(store.root, manifest, role, archive=archive)
    if candidate_id is None:
        raise RecordError(f"{role} requires --candidate")
    candidate = store.candidate(candidate_id)
    stages = current_results(store, candidate_id)
    if any(required not in stages for required in DEPENDENCIES[role]):
        raise RecordError(f"{role} is out of order for {candidate_id}")
    if role == "evidence-audit":
        reasons = preaudit_reasons(candidate, stages)
        if reasons:
            raise RecordError(
                f"evidence-audit is withheld for {candidate_id}: {', '.join(reasons)}"
            )
    if role in {"independent-verification", "adversarial-review"}:
        reasons = preverification_reasons(candidate, stages)
        if reasons:
            raise RecordError(f"{role} is withheld for {candidate_id}: {', '.join(reasons)}")
    if role == "adversarial-review":
        verifier = stages["independent-verification"]
        relation = stages["relation-proposal"]["relation"]
        if verifier.get("verdict") != "agree" or verifier.get("relation") != relation:
            raise RecordError(
                f"adversarial-review is withheld for {candidate_id}: verifier-disagreement"
            )
    archive = frozen_archive(store, candidate_id) if role == "normalize-and-dedupe" else None
    deterministic = (
        find_deterministic_overlaps(candidate, archive or []) if archive is not None else None
    )
    return make_packet(
        store.root,
        manifest,
        role,
        candidate=candidate,
        stages=stages,
        archive=archive,
        deterministic_overlaps=deterministic,
    )


def ingest_response(
    store: BatchStore,
    role: str,
    raw_text: str,
    candidate_id: str | None = None,
    actual_model: str | None = None,
) -> dict[str, Any]:
    """Persist raw failures and valid role output without promoting learner data."""
    if store.manifest().status == "closed":
        raise RecordError("closed batch must be reopened before new stage output")
    try:
        packet = packet_for(store, role, candidate_id)
    except RecordError as exc:
        target = candidate_id if candidate_id in store.candidate_ids() else None
        event = {
            "role": role,
            "status": "failed",
            "raw_response": raw_text,
            "failure": str(exc),
            "at": utc_now(),
        }
        if target:
            store.append_event(target, event)
        else:
            store.append_batch_event(event)
        raise
    prior_events = store.events(candidate_id) if candidate_id else store.batch_events()
    prior = _latest(prior_events, role)
    if (
        prior is not None
        and prior.get("status") == "complete"
        and prior.get("input_digest") == packet["input_digest"]
        and prior.get("raw_response") == raw_text
        and (actual_model is None or prior.get("model") == actual_model)
    ):
        return prior
    try:
        parsed = json.loads(raw_text)
        response = validate_stage_response(role, parsed, limit=store.manifest().candidate_limit)
        if (
            role == "normalize-and-dedupe"
            and candidate_id is not None
            and has_self_overlap(response["result"]["overlaps"], store.batch_id, candidate_id)
        ):
            raise RecordError("normalization result includes self-overlap")
    except (json.JSONDecodeError, RecordError) as exc:
        event = {
            "role": role,
            "status": "failed",
            "raw_response": raw_text,
            "failure": str(exc),
            "input_digest": packet["input_digest"],
            "at": utc_now(),
        }
        if candidate_id:
            store.append_event(candidate_id, event)
        else:
            store.append_batch_event(event)
        raise RecordError(f"malformed {role} response: {exc}") from exc
    result = response["result"]
    if role in {"indonesian-usage", "malaysian-usage", "relation-proposal"}:
        result = _namespace_claim_ids(role, result)
    if role == "normalize-and-dedupe":
        provided = {item["other_id"]: item for item in result["overlaps"]}
        for match in packet["context"]["deterministic_overlaps"]:
            provided.setdefault(match["other_id"], match)
        result = {**result, "overlaps": list(provided.values())}
    event = {
        "role": role,
        "status": "complete",
        "response": response,
        "result": result,
        "raw_response": raw_text,
        "input_digest": packet["input_digest"],
        "prompt_set_version": store.manifest().prompt_set_version,
        "model": actual_model or response["model"],
        "reported_model": response["model"],
        "tool": (
            "codex-cli"
            if actual_model and actual_model.endswith("/codex-cli")
            else response.get("tool", response["model"])
        ),
        "upstream_digest": digest(packet["context"]),
        **(
            {"relation_proposal_digest": packet["relation_proposal_digest"]}
            if role == "independent-verification"
            else {}
        ),
        "at": utc_now(),
    }
    if role == "generate":
        existing = set(store.candidate_ids())
        generated = {item["candidate_id"] for item in result["candidates"]}
        if existing and generated != existing:
            raise RecordError("generation replay changes candidate IDs; use a new batch")
        if existing and any(
            store.candidate(item["candidate_id"]) != item for item in result["candidates"]
        ):
            raise RecordError("generation replay changes candidate content; use a revision")
        for item in result["candidates"]:
            if item["candidate_id"] not in existing:
                store.save_candidate(item["candidate_id"], item)
        store.append_batch_event(event)
    else:
        assert candidate_id is not None
        store.append_event(candidate_id, event)
    return event


def check_candidate(store: BatchStore, candidate_id: str) -> dict[str, Any]:
    results = current_results(store, candidate_id)
    explicit = _latest(store.events(candidate_id), "explicit-final")
    decision = decide_candidate(
        store.candidate(candidate_id),
        results,
        explicit_final=explicit.get("decision") if explicit else None,
    )
    decision["candidate_id"] = candidate_id
    decision["checked_at"] = utc_now()
    store.append_event(
        candidate_id,
        {
            "role": "decision",
            "status": "complete",
            "result": decision,
            "at": decision["checked_at"],
        },
    )
    return decision


def finalize_hold(store: BatchStore, candidate_id: str, reason: str) -> dict[str, Any]:
    return _finalize_candidate(store, candidate_id, reason, "hold")


def finalize_reject(store: BatchStore, candidate_id: str, reason: str) -> dict[str, Any]:
    """Stop spending curation calls on a known unsuitable proposal."""
    return _finalize_candidate(store, candidate_id, reason, "rejected")


def _finalize_candidate(
    store: BatchStore, candidate_id: str, reason: str, outcome: str
) -> dict[str, Any]:
    if not reason.strip() or candidate_id not in store.candidate_ids():
        raise RecordError(f"finalize-{outcome} requires an existing candidate and a reason")
    store.append_event(
        candidate_id,
        {
            "role": "explicit-final",
            "status": "complete",
            "decision": {"outcome": outcome, "reason": reason.strip()},
            "at": utc_now(),
        },
    )
    return check_candidate(store, candidate_id)


def reopen_candidate(store: BatchStore, candidate_id: str, reason: str) -> dict[str, Any]:
    """Resume a held/rejected candidate without removing its decision history."""
    if not reason.strip() or candidate_id not in store.candidate_ids():
        raise RecordError("reopen requires an existing candidate and a reason")
    explicit = _latest(store.events(candidate_id), "explicit-final")
    if explicit is None or explicit.get("decision") is None:
        raise RecordError("candidate has no final hold or rejection to reopen")
    store.append_event(
        candidate_id,
        {
            "role": "explicit-final",
            "status": "complete",
            "decision": None,
            "reason": reason.strip(),
            "at": utc_now(),
        },
    )
    manifest = store.manifest()
    if manifest.status == "closed":
        store.save_manifest(replace(manifest, status="open"))
    return check_candidate(store, candidate_id)


def revise_candidate(
    store: BatchStore, candidate_id: str, changes: dict[str, Any], reason: str
) -> dict[str, Any]:
    """Record a material proposal correction and invalidate dependent stage packets."""
    if store.manifest().status != "open":
        raise RecordError("closed batch must be reopened before candidate revision")
    if (
        not reason.strip()
        or not changes
        or set(changes) - {"english", "indonesian", "malaysian", "sense", "tags"}
    ):
        raise RecordError("revision requires a reason and supported changed fields")
    explicit = _latest(store.events(candidate_id), "explicit-final")
    if explicit is not None and explicit.get("decision") is not None:
        raise RecordError("reopen the final candidate decision before revision")
    before = store.candidate(candidate_id)
    updated = validate_candidate({**before, **changes})
    if updated == before:
        raise RecordError("revision does not change the candidate")
    store.append_event(
        candidate_id,
        {
            "role": "proposal-revision",
            "status": "complete",
            "before": before,
            "result": updated,
            "reason": reason.strip(),
            "at": utc_now(),
        },
    )
    return updated


def close_manifest(store: BatchStore) -> None:
    manifest = store.manifest()
    store.save_manifest(replace(manifest, status="closed"))
