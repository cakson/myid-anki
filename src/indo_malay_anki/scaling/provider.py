"""Local Codex CLI adapter for bounded, durable curation calls."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from indo_malay_anki.curation.models import role_route

from .store import RunError


def call_model(
    root: Path,
    role: str,
    prompt: str,
    *,
    timeout_seconds: int = 180,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    """Return parsed JSON plus observed work, without mutating any curation artifact."""
    route = role_route(root, role)
    selected_model = model or route["model"]
    effort = reasoning_effort or route["reasoning_effort"]
    codex_bin = os.environ.get("CURATION_CODEX_BIN", "codex")
    launcher = root / "scripts" / "curation_codex.py"
    if not launcher.exists():
        raise RunError("Codex provider launcher is unavailable")
    with tempfile.TemporaryDirectory(prefix="myid-scaling-model-") as temporary:
        argv = [
            sys.executable,
            str(launcher),
            "--codex-bin",
            codex_bin,
            "--",
            "exec",
            "--json",
            "--ephemeral",
            "--skip-git-repo-check",
            "-s",
            "read-only",
            "-C",
            temporary,
            "-m",
            selected_model,
            "-c",
            f'model_reasoning_effort="{effort}"',
            "-",
        ]
        started = time.perf_counter()
        try:
            result = subprocess.run(
                argv,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RunError(f"{role} model timed out after {timeout_seconds}s") from exc
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    events: list[dict] = []
    for line in result.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    usage = next(
        (
            item.get("usage", {})
            for item in reversed(events)
            if item.get("type") == "turn.completed"
        ),
        {},
    )
    message = next(
        (
            item.get("item", {}).get("text", "")
            for item in reversed(events)
            if item.get("type") == "item.completed"
            and item.get("item", {}).get("type") == "agent_message"
        ),
        "",
    )
    if result.returncode != 0:
        raise RunError(f"{role} model failed: {result.stderr[-500:]}")
    try:
        parsed = json.loads(message)
    except json.JSONDecodeError as exc:
        raise RunError(f"{role} model returned non-JSON output") from exc
    return {
        "response": parsed,
        "raw_text": message,
        "model": selected_model,
        "effort": effort,
        "elapsed_ms": elapsed_ms,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "model_calls": 1,
        "retrievals": None,
    }
