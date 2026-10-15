"""Validate source-first research notes before spending locale-role calls."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .records import RecordError

LOCALES = {"Indonesia", "Malaysia"}
SOURCE_KINDS = {"dictionary", "contextual", "comparative"}
ACCESS_METHODS = {"retrieved-page", "corpus-query", "manual-inspection"}


def load_source_inspections(path: Path, *, required: bool) -> dict[str, Any] | None:
    """Keep observed source notes separate from audited, claim-linked evidence."""
    if not path.exists():
        if required:
            raise RecordError(f"source preflight is required before locale research: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecordError(f"Cannot load source inspections: {exc}") from exc
    if not required:
        # Historical packets used free-form inspection notes. Their digest must remain stable.
        return data
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise RecordError("source inspections require schema_version 1")
    try:
        recorded = datetime.fromisoformat(str(data["recorded_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise RecordError("source inspections need ISO recorded_at") from exc
    if recorded.tzinfo is None:
        raise RecordError("source inspections need timezone in recorded_at")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise RecordError("source inspections require at least one source")
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise RecordError(f"source inspection {index} must be an object")
        for key in (
            "source_group",
            "publisher",
            "url_or_query",
            "page_location_or_query",
            "observation",
            "limitations",
        ):
            value = source.get(key)
            if not isinstance(value, str) or not value.strip():
                raise RecordError(f"source inspection {index} needs {key}")
        for key in ("source_group", "publisher"):
            if any(separator in source[key] for separator in (";", " | ", " + ")):
                raise RecordError(f"source inspection {index} joins sources in {key}")
        locator = source["url_or_query"]
        if " | " in locator or locator.count("https://") + locator.count("http://") > 1:
            raise RecordError(f"source inspection {index} joins URLs")
        if source.get("locale") not in LOCALES:
            raise RecordError(f"source inspection {index} has invalid locale")
        if source.get("source_kind") not in SOURCE_KINDS:
            raise RecordError(f"source inspection {index} has invalid source_kind")
        if source.get("access_method") not in ACCESS_METHODS:
            raise RecordError(f"source inspection {index} has invalid access_method")
        try:
            accessed = datetime.fromisoformat(str(source["accessed_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError) as exc:
            raise RecordError(f"source inspection {index} needs ISO accessed_at") from exc
        if accessed.tzinfo is None:
            raise RecordError(f"source inspection {index} needs timezone in accessed_at")
    if {source["locale"] for source in sources} != LOCALES:
        raise RecordError("source inspections need sources for Indonesia and Malaysia")
    if len({source["source_group"].casefold() for source in sources}) < 2:
        raise RecordError("source inspections need two independent source groups")
    return data
