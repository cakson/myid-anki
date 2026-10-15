"""Permanent, logically append-only concept ID assignment records."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .records import RecordError
from .store import read_json

_ID = re.compile(r"[0-9]{6}\Z", re.ASCII)


def validate_ledger(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise RecordError("ID ledger must have schema_version 1")
    assignments = raw.get("assignments")
    if not isinstance(assignments, list):
        raise RecordError("ID ledger assignments must be a list")
    seen_ids: set[str] = set()
    seen_origins: set[tuple[str, str]] = set()
    for item in assignments:
        if not isinstance(item, dict):
            raise RecordError("ID assignment must be an object")
        for key in ("id", "batch_id", "candidate_id", "assigned_at", "semantic_concept_key"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise RecordError(f"ID assignment requires {key}")
        if not _ID.fullmatch(item["id"]) or item["id"] in seen_ids:
            raise RecordError("ID assignments must be unique six-digit strings")
        origin = (item["batch_id"], item["candidate_id"])
        if origin in seen_origins:
            raise RecordError("candidate has more than one permanent ID")
        seen_ids.add(item["id"])
        seen_origins.add(origin)
    return raw


def load_ledger(root: Path) -> dict[str, Any]:
    path = root / "curation" / "id-ledger.json"
    if not path.exists():
        return {"schema_version": 1, "assignments": []}
    return validate_ledger(read_json(path))


def allocate_id(ledger: Mapping[str, Any]) -> str:
    used = {int(item["id"]) for item in ledger["assignments"]}
    next_id = max(used, default=0) + 1
    if next_id > 999999:
        raise RecordError("six-digit concept ID space exhausted")
    return f"{next_id:06d}"


def assigned_id(ledger: Mapping[str, Any], batch_id: str, candidate_id: str) -> str | None:
    for item in ledger["assignments"]:
        if item["batch_id"] == batch_id and item["candidate_id"] == candidate_id:
            return str(item["id"])
    return None


def append_assignment(
    ledger: dict[str, Any],
    *,
    concept_id: str,
    batch_id: str,
    candidate_id: str,
    assigned_at: str,
    semantic_concept_key: str,
) -> None:
    if assigned_id(ledger, batch_id, candidate_id) is not None:
        raise RecordError("candidate already has a permanent ID")
    ledger["assignments"].append(
        {
            "id": concept_id,
            "batch_id": batch_id,
            "candidate_id": candidate_id,
            "assigned_at": assigned_at,
            "semantic_concept_key": semantic_concept_key,
        }
    )
    validate_ledger(ledger)


def active_status(ledger: Mapping[str, Any], active_ids: set[str]) -> dict[str, str]:
    return {
        item["id"]: "active" if item["id"] in active_ids else "retired"
        for item in ledger["assignments"]
    }
