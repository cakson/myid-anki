"""Small, strict schemas for versioned curation records."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

RELATIONS = frozenset({"same", "similar", "different-common-word", "false-friend"})
AI_ROLES = (
    "generate",
    "normalize-and-dedupe",
    "indonesian-usage",
    "malaysian-usage",
    "relation-proposal",
    "evidence-audit",
    "independent-verification",
    "adversarial-review",
)
FINAL_OUTCOMES = frozenset({"accepted", "hold", "rejected"})
STAGE_STATUSES = frozenset({"complete", "failed", "interrupted", "skipped", "missing"})
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")


class RecordError(ValueError):
    """A structured curation record violates its versioned contract."""


def require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise RecordError(f"{label} must be a JSON object with string keys")
    return value


def require_text(record: Mapping[str, Any], key: str, label: str | None = None) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise RecordError(f"{label or key} must be nonempty text without outer whitespace")
    return value


def require_list(record: Mapping[str, Any], key: str) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list):
        raise RecordError(f"{key} must be a list")
    return value


def safe_id(value: str, label: str = "id") -> str:
    if not _SAFE_ID.fullmatch(value):
        raise RecordError(f"{label} must use lowercase letters, digits, or hyphens")
    return value


@dataclass(frozen=True, slots=True)
class BatchManifest:
    batch_id: str
    topic: str
    scope: str
    candidate_limit: int
    prompt_set_version: str
    created_at: str
    status: str = "open"

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> BatchManifest:
        data = require_mapping(raw, "manifest")
        batch_id = safe_id(require_text(data, "batch_id"), "batch_id")
        topic = require_text(data, "topic")
        scope = require_text(data, "scope")
        limit = data.get("candidate_limit")
        if type(limit) is not int or not 1 <= limit <= 12:
            raise RecordError("candidate_limit must be an integer from 1 to 12")
        version = require_text(data, "prompt_set_version")
        created_at = require_text(data, "created_at")
        status = data.get("status")
        if status not in {"open", "closed"}:
            raise RecordError("status must be open or closed")
        return cls(batch_id, topic, scope, limit, version, created_at, status)

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


def validate_candidate(raw: Any) -> dict[str, Any]:
    data = require_mapping(raw, "candidate")
    candidate_id = safe_id(require_text(data, "candidate_id"), "candidate_id")
    result = dict(data)
    result["candidate_id"] = candidate_id
    for key in ("english", "indonesian", "malaysian", "sense"):
        require_text(data, key)
    if "id" in data:
        raise RecordError("generated candidates cannot contain permanent id")
    if "tags" in data:
        tags = require_list(data, "tags")
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise RecordError("tags must be nonempty strings")
    return result


def validate_claim(raw: Any) -> dict[str, Any]:
    data = require_mapping(raw, "claim")
    for key in ("claim_id", "claim_type", "proposition"):
        require_text(data, key)
    if data["claim_type"] not in {
        "meaning",
        "locale-usage",
        "preferred-choice",
        "relation",
        "misleading-contrast",
    }:
        raise RecordError("invalid claim_type")
    return dict(data)


def validate_audit_observation(raw: Any) -> dict[str, Any]:
    data = require_mapping(raw, "audit observation")
    for key in (
        "evidence_id",
        "claim_id",
        "source_group",
        "source_title",
        "publisher",
        "url_or_query",
        "accessed_at",
        "observation",
        "page_location_or_query",
        "audit_method",
        "stance",
        "claim_type",
    ):
        require_text(data, key)
    for key in ("source_group", "publisher"):
        value = data[key]
        if ";" in value or " | " in value or " + " in value:
            raise RecordError(f"{key} must identify one underlying source")
    locator = data["url_or_query"]
    if " | " in locator or locator.count("https://") + locator.count("http://") > 1:
        raise RecordError("url_or_query must identify one source, not a joined comparison")
    if data["audit_method"] not in {"retrieved-page", "corpus-query", "manual-inspection"}:
        raise RecordError("invalid audit_method")
    if data["stance"] not in {"supports", "contradicts", "inconclusive"}:
        raise RecordError("invalid evidence stance")
    if data["claim_type"] not in {
        "meaning",
        "locale-usage",
        "preferred-choice",
        "relation",
        "misleading-contrast",
    }:
        raise RecordError("invalid claim_type")
    if data["claim_type"] == "preferred-choice" and data.get("usage_basis") not in {
        "contextual",
        "comparative",
        "dictionary-only",
    }:
        raise RecordError("preferred-choice evidence requires usage_basis")
    return dict(data)


def validate_stage_response(role: str, raw: Any, *, limit: int = 12) -> dict[str, Any]:
    if role not in AI_ROLES:
        raise RecordError(f"unknown role: {role}")
    data = require_mapping(raw, "response")
    if data.get("schema_version") != 1:
        raise RecordError("schema_version must be 1")
    if data.get("role") != role:
        raise RecordError("response role does not match requested role")
    require_text(data, "model")
    result = require_mapping(data.get("result"), "result")
    if role == "generate":
        candidates = require_list(result, "candidates")
        if len(candidates) > limit:
            raise RecordError("candidate limit exceeded")
        validated = [validate_candidate(candidate) for candidate in candidates]
        ids = [candidate["candidate_id"] for candidate in validated]
        if len(ids) != len(set(ids)):
            raise RecordError("duplicate candidate_id in generation")
    elif role == "normalize-and-dedupe":
        for overlap in require_list(result, "overlaps"):
            item = require_mapping(overlap, "overlap")
            require_text(item, "other_id")
            if item.get("resolution") not in {
                "distinct",
                "merge",
                "reject",
                "unresolved",
                "retrospective",
            }:
                raise RecordError("invalid overlap resolution")
            require_text(item, "rationale")
    elif role in {"indonesian-usage", "malaysian-usage"}:
        for key in ("meaning", "common_use", "preferred", "register", "region"):
            require_text(result, key)
        require_list(result, "alternatives")
        for claim in require_list(result, "claims"):
            validate_claim(claim)
    elif role == "relation-proposal":
        if result.get("relation") not in RELATIONS:
            raise RecordError("invalid relation")
        require_text(result, "english")
        require_text(result, "semantic_alignment")
        if type(result.get("aligned")) is not bool:
            raise RecordError("aligned must be an explicit boolean")
        for claim in require_list(result, "claims"):
            validate_claim(claim)
        if result["relation"] == "false-friend":
            contrast = require_mapping(result.get("contrast"), "false-friend contrast")
            for key in ("misleading_form", "misleading_language", "actual_meaning"):
                require_text(contrast, key)
            if contrast["misleading_language"] not in {"indonesian", "malaysian"}:
                raise RecordError("invalid misleading_language")
            require_list(contrast, "claim_ids")
    elif role == "evidence-audit":
        for observation in require_list(result, "observations"):
            validate_audit_observation(observation)
    elif role in {"independent-verification", "adversarial-review"}:
        if result.get("verdict") not in {"agree", "object"}:
            raise RecordError("verdict must be agree or object")
        require_list(result, "concerns")
        require_text(result, "rationale")
        if role == "independent-verification":
            if result.get("relation") not in RELATIONS:
                raise RecordError("verifier must independently select a relation")
    return dict(data)
