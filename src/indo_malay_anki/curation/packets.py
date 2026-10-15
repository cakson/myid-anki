"""Versioned prompt packets with role-specific context allowlists."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .records import AI_ROLES, BatchManifest, RecordError
from .source_inspections import load_source_inspections


def digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _prompt(root: Path, role: str, version: str) -> str:
    if role not in AI_ROLES:
        raise RecordError(f"unknown role: {role}")
    manifest_path = root / "curation" / "prompts" / "versions" / version / "manifest.json"
    if not manifest_path.exists():
        manifest_path = (
            Path(__file__).resolve().parents[3]
            / "curation"
            / "prompts"
            / "versions"
            / version
            / "manifest.json"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("prompt_set_version") != version:
            raise RecordError(f"prompt manifest version mismatch: {version}")
        filename = manifest["roles"][role]["prompt"]
        if Path(filename).name != filename:
            raise RecordError("prompt manifest path must be a filename")
        return (manifest_path.parent / filename).read_text(encoding="utf-8")
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RecordError(f"Cannot load role prompt: {exc}") from exc


def make_packet(
    root: Path,
    manifest: BatchManifest,
    role: str,
    *,
    candidate: Mapping[str, Any] | None = None,
    stages: Mapping[str, Mapping[str, Any]] | None = None,
    archive: list[Mapping[str, Any]] | None = None,
    deterministic_overlaps: list[Mapping[str, Any]] | None = None,
    bind_relation: bool = True,
) -> dict[str, Any]:
    """Build a packet; verifier context deliberately excludes generation rationale and verdict."""
    stages = stages or {}
    context: dict[str, Any] = {"topic": manifest.topic, "scope": manifest.scope}
    if role == "generate":
        context["candidate_limit"] = manifest.candidate_limit
        if archive is not None:
            context["previously_investigated_concepts"] = archive
            context["archive_rule"] = (
                "Avoid these concepts, including synonyms and minor form variants. "
                "They may be accepted, held, or rejected; propose new concepts instead."
            )
    else:
        if candidate is None:
            raise RecordError(f"{role} requires a candidate")
        context["candidate"] = {
            key: candidate.get(key)
            for key in (
                "candidate_id",
                "legacy_id",
                "english",
                "indonesian",
                "malaysian",
                "sense",
                "tags",
            )
            if key in candidate
        }
    if role == "normalize-and-dedupe":
        context["archive"] = archive or []
        context["deterministic_overlaps"] = deterministic_overlaps or []
    elif role in {"indonesian-usage", "malaysian-usage"}:
        context["overlaps"] = stages.get("normalize-and-dedupe", {}).get("overlaps", [])
        if manifest.prompt_set_version in {"1.2.0", "1.3.0", "1.4.0", "1.5.0"}:
            inspections = load_source_inspections(
                root
                / "curation"
                / "batches"
                / manifest.batch_id
                / "source-inspections"
                / f"{candidate['candidate_id']}.json",
                required=True,
            )
            locale = "Indonesia" if role == "indonesian-usage" else "Malaysia"
            context["source_inspections"] = [
                source for source in inspections["sources"] if source["locale"] == locale
            ]
    elif role == "relation-proposal":
        context["indonesian_usage"] = stages.get("indonesian-usage", {})
        context["malaysian_usage"] = stages.get("malaysian-usage", {})
    elif role == "evidence-audit":
        context["claims"] = [
            claim
            for stage in ("indonesian-usage", "malaysian-usage", "relation-proposal")
            for claim in stages.get(stage, {}).get("claims", [])
        ]
        context["source_leads"] = [
            lead
            for stage in ("indonesian-usage", "malaysian-usage", "relation-proposal")
            for lead in stages.get(stage, {}).get("source_leads", [])
        ]
        inspection_path = (
            root
            / "curation"
            / "batches"
            / manifest.batch_id
            / "source-inspections"
            / f"{candidate['candidate_id']}.json"
        )
        inspections = load_source_inspections(
            inspection_path,
            required=manifest.prompt_set_version in {"1.2.0", "1.3.0", "1.4.0", "1.5.0"},
        )
        if inspections is not None:
            context["source_inspections"] = inspections
    elif role == "independent-verification":
        context["indonesian_usage"] = stages.get("indonesian-usage", {})
        context["malaysian_usage"] = stages.get("malaysian-usage", {})
        context["audited_evidence"] = stages.get("evidence-audit", {}).get("observations", [])
    elif role == "adversarial-review":
        context["relation_proposal"] = stages.get("relation-proposal", {})
        context["indonesian_usage"] = stages.get("indonesian-usage", {})
        context["malaysian_usage"] = stages.get("malaysian-usage", {})
        context["audited_evidence"] = stages.get("evidence-audit", {}).get("observations", [])
        context["verifier"] = stages.get("independent-verification", {})
    packet = {
        "schema_version": 1,
        "batch_id": manifest.batch_id,
        "candidate_id": candidate.get("candidate_id") if candidate else None,
        "role": role,
        "prompt_set_version": manifest.prompt_set_version,
        "prompt": _prompt(root, role, manifest.prompt_set_version),
        "context": context,
    }
    if role == "independent-verification" and bind_relation:
        packet["relation_proposal_digest"] = digest(stages.get("relation-proposal", {}))
    packet["input_digest"] = digest(packet)
    return packet
