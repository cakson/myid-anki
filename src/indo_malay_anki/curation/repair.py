"""Conservative, recorded cleanup of malformed AI evidence bundle records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .records import RecordError, require_mapping, validate_audit_observation
from .store import atomic_json


def strip_invalid_evidence(raw: dict[str, Any]) -> dict[str, Any]:
    """Drop malformed observations, never invent or rewrite supporting evidence."""
    data = require_mapping(raw, "audit bundle")
    if data.get("schema_version") != 1 or data.get("role") != "evidence-audit":
        raise RecordError("expected a version 1 evidence-audit bundle")
    results = require_mapping(data.get("results"), "results")
    corrected: dict[str, Any] = {}
    removed: dict[str, list[dict[str, str]]] = {}
    for candidate_id, result in results.items():
        item = require_mapping(result, "candidate audit result")
        observations = item.get("observations")
        if not isinstance(observations, list):
            raise RecordError(f"{candidate_id} has no observations list")
        valid = []
        failures = []
        for observation in observations:
            try:
                valid.append(validate_audit_observation(observation))
            except RecordError as exc:
                failures.append(
                    {
                        "evidence_id": str(observation.get("evidence_id", "unknown"))
                        if isinstance(observation, dict)
                        else "unknown",
                        "reason": str(exc),
                    }
                )
        corrected[candidate_id] = {
            **item,
            "observations": valid,
            "removed_invalid_evidence": failures,
        }
        if failures:
            removed[candidate_id] = failures
    return {
        **data,
        "results": corrected,
        "curation_transform": {
            "name": "strip-invalid-evidence",
            "version": 1,
            "removed": removed,
            "rule": "Only malformed observations were removed; no support was added or rewritten.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.response.resolve() == args.output.resolve():
        parser.error("output must differ from original response")
    corrected = strip_invalid_evidence(json.loads(args.response.read_text(encoding="utf-8")))
    atomic_json(args.output, corrected)
    print(json.dumps(corrected["curation_transform"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
