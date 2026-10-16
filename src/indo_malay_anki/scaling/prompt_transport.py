"""Experimental compact transport for read-only efficiency replay.

Production curation continues to use the full Feature 003 packet. This helper keeps
the replay serialization reproducible without changing the authoritative packet.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def compact_overlap_prompt(packet: Mapping[str, Any]) -> str:
    if packet.get("role") != "normalize-and-dedupe":
        raise ValueError("compact overlap transport requires normalize-and-dedupe")
    context = packet["context"]
    archive = context["archive"]
    compact = {
        "schema_version": 1,
        "batch_id": packet["batch_id"],
        "candidate_id": packet["candidate_id"],
        "role": packet["role"],
        "prompt_set_version": packet["prompt_set_version"],
        "input_digest": packet["input_digest"],
        "topic": context["topic"],
        "scope": context["scope"],
        "candidate": context["candidate"],
        "deterministic_overlaps": context["deterministic_overlaps"],
        "archive_columns": ["id", "english", "indonesian", "malaysian", "sense", "tags"],
        "archive_rows": [
            [
                item.get("candidate_id") or item.get("id"),
                item.get("english"),
                item.get("indonesian"),
                item.get("malaysian"),
                item.get("sense", ""),
                item.get("tags", []),
            ]
            for item in archive
        ],
    }
    return (
        packet["prompt"]
        + "\nCURATION_PACKET_COMPACT_JSON\n"
        + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
    )
