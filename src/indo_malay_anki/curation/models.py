"""Central model routing for the offline, file-backed curation workflow."""

from __future__ import annotations

import json
from pathlib import Path

from .records import AI_ROLES, EXTRA_ROLES, RecordError

REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh", "max"}


def config_path(root: Path) -> Path:
    local = root / "curation" / "config.json"
    if local.exists():
        return local
    return Path(__file__).resolve().parents[3] / "curation" / "config.json"


def role_route(root: Path, role: str) -> dict[str, str]:
    """Return the configured model for a role without changing packet digests."""
    if role not in AI_ROLES + EXTRA_ROLES:
        raise RecordError(f"unknown curation role: {role}")
    try:
        config = json.loads(config_path(root).read_text(encoding="utf-8"))
        route = config["role_models"][role]
        model = route["model"]
        effort = route["reasoning_effort"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RecordError(f"invalid curation model route for {role}: {exc}") from exc
    if not isinstance(model, str) or not model.strip():
        raise RecordError(f"invalid model for {role}")
    if effort not in REASONING_EFFORTS:
        raise RecordError(f"invalid reasoning effort for {role}")
    return {"role": role, "model": model, "reasoning_effort": effort}
