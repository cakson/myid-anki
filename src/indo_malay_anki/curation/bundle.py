"""Bounded, inspectable prompt exchange for one independent role across a batch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .duplicates import has_self_overlap
from .records import RecordError, require_mapping, require_text, validate_stage_response
from .store import BatchStore
from .workflow import ingest_response, packet_for, utc_now


def packet_bundle(store: BatchStore, role: str, candidate_ids: list[str]) -> dict[str, Any]:
    if role == "generate":
        raise RecordError("generation uses its single batch packet")
    if not candidate_ids or len(candidate_ids) != len(set(candidate_ids)):
        raise RecordError("bundle requires distinct candidate IDs")
    packets = [packet_for(store, role, candidate_id) for candidate_id in candidate_ids]
    shared_archive = []
    bundled_refs = {f"{store.batch_id}:{candidate_id}" for candidate_id in candidate_ids}
    if role == "normalize-and-dedupe":
        by_id = {
            str(item.get("candidate_id") or item.get("id")): item
            for packet in packets
            for item in packet["context"]["archive"]
            if item.get("candidate_id") not in bundled_refs
        }
        shared_archive = list(by_id.values())
    items = []
    for packet in packets:
        context = dict(packet["context"])
        if role == "normalize-and-dedupe":
            archive = context.pop("archive")
            context["peer_candidates"] = [
                item
                for item in archive
                if item.get("candidate_id") in bundled_refs
                and item.get("candidate_id") != f"{store.batch_id}:{packet['candidate_id']}"
            ]
        items.append(
            {
                "candidate_id": packet["candidate_id"],
                "context": context,
                "input_digest": packet["input_digest"],
            }
        )
    return {
        "schema_version": 1,
        "batch_id": store.batch_id,
        "role": role,
        "prompt_set_version": store.manifest().prompt_set_version,
        "prompt": (
            "BUNDLE OUTPUT OVERRIDE: Return one JSON object with top-level schema_version, "
            "role, model, and results. The results value must be an object keyed by every "
            "candidate_id in items, with one role result for each. Do not return the singular "
            "result shape shown in the role prompt below.\n\n" + packets[0]["prompt"]
        ),
        "shared_archive": shared_archive,
        "bundle_guidance": (
            "For normalization, compare each item with the shared archive and its own "
            "peer_candidates. Neither list contains that item's own entry. The per-item "
            "deterministic overlaps still apply. "
            "Never report a candidate as overlapping itself."
            if role == "normalize-and-dedupe"
            else "Return a separate result for every listed candidate_id."
        ),
        "items": items,
        "response_contract": {
            "schema_version": 1,
            "role": role,
            "model": "actual model/tool identifier",
            "results": {candidate_id: "one role result object" for candidate_id in candidate_ids},
        },
    }


def ingest_bundle(
    store: BatchStore,
    role: str,
    response_path: Path,
    candidate_ids: list[str],
    actual_model: str | None = None,
) -> list[dict[str, Any]]:
    """Validate the entire response before appending any candidate stage events."""
    raw_text = response_path.read_text(encoding="utf-8")
    try:
        raw = json.loads(raw_text)
        data = require_mapping(raw, "bundle response")
        if data.get("schema_version") != 1 or data.get("role") != role:
            raise RecordError("bundle schema version or role mismatch")
        model = require_text(data, "model")
        results = require_mapping(data.get("results"), "bundle results")
        if set(results) != set(candidate_ids):
            raise RecordError("bundle results must match candidate IDs exactly")
        if not candidate_ids:
            raise RecordError("bundle requires candidates")
        for candidate_id in candidate_ids:
            packet_for(store, role, candidate_id)
            validated = validate_stage_response(
                role,
                {
                    "schema_version": 1,
                    "role": role,
                    "model": model,
                    "result": results[candidate_id],
                },
            )
            if role == "normalize-and-dedupe" and has_self_overlap(
                validated["result"]["overlaps"], store.batch_id, candidate_id
            ):
                raise RecordError(f"normalization result includes self-overlap: {candidate_id}")
    except (json.JSONDecodeError, RecordError) as exc:
        store.append_batch_event(
            {
                "role": f"bundle:{role}",
                "status": "failed",
                "raw_response": raw_text,
                "response_path": str(response_path),
                "failure": str(exc),
                "at": utc_now(),
            }
        )
        raise RecordError(f"malformed {role} bundle: {exc}") from exc
    events = []
    for candidate_id in candidate_ids:
        wrapped = {
            "schema_version": 1,
            "role": role,
            "model": model,
            "result": results[candidate_id],
            "bundle_response": str(response_path),
        }
        events.append(ingest_response(store, role, json.dumps(wrapped), candidate_id, actual_model))
    return events
