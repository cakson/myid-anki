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
EXTRA_ROLES = ("competing-form-challenge",)
FINAL_OUTCOMES = frozenset({"accepted", "hold", "rejected"})
STAGE_STATUSES = frozenset({"complete", "failed", "interrupted", "skipped", "missing"})
RISK_PATHS = frozenset({"ordinary-fast", "escalated", "false-friend", "not-assessed"})
OPERATION_KINDS = frozenset({"model", "research", "export", "evaluation-pause"})
OPERATION_STATUSES = frozenset({"started", "complete", "failed", "interrupted"})
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
    decision_policy_version: str | None = None

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
        policy = data.get("decision_policy_version")
        if policy is not None and policy not in {"1.0.0", "2.0.0", "3.0.0", "3.1.0", "3.2.0"}:
            raise RecordError("unsupported decision_policy_version")
        return cls(batch_id, topic, scope, limit, version, created_at, status, policy)

    def as_dict(self) -> dict[str, Any]:
        result = {name: getattr(self, name) for name in self.__dataclass_fields__}
        if self.decision_policy_version is None:
            result.pop("decision_policy_version")
        return result


def validate_operation_event(raw: Any) -> dict[str, Any]:
    """Validate one append-only attempt event; old batches simply have no such events."""
    data = require_mapping(raw, "operation event")
    safe_id(require_text(data, "operation_id"), "operation_id")
    if data.get("kind") not in OPERATION_KINDS:
        raise RecordError("invalid operation kind")
    if data.get("status") not in OPERATION_STATUSES:
        raise RecordError("invalid operation status")
    require_text(data, "at")
    candidate_ids = require_list(data, "candidate_ids")
    for candidate_id in candidate_ids:
        if not isinstance(candidate_id, str):
            raise RecordError("candidate_ids must contain strings")
        safe_id(candidate_id, "candidate_id")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise RecordError("duplicate operation candidate_id")
    for key in ("elapsed_ms", "queue_wait_ms", "input_tokens", "output_tokens", "retry"):
        value = data.get(key)
        if value is not None and (type(value) is not int or value < 0):
            raise RecordError(f"{key} must be a nonnegative integer or null")
    if data["status"] != "started" and data.get("elapsed_ms") is None:
        raise RecordError("finished operation requires elapsed_ms")
    if data["kind"] == "model" and data["status"] != "started":
        if data.get("input_tokens") is None or data.get("output_tokens") is None:
            require_text(data, "usage_unavailable_reason")
    return dict(data)


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
        "lexical-existence",
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
        "lexical-existence",
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
    if role not in AI_ROLES + EXTRA_ROLES:
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
    elif role == "competing-form-challenge":
        if result.get("outcome") not in {
            "contrast-remains-useful",
            "contrast-needs-qualification",
            "preference-materially-uncertain",
            "no-meaningful-preference-contrast",
        }:
            raise RecordError("invalid competing-form challenge outcome")
        assessment = require_mapping(result.get("assessment"), "challenge assessment")
        for key in (
            "normal_everyday_same_sense",
            "materially_weakens_preference",
            "useful_difference_remains",
            "unqualified_card_misleads",
        ):
            if type(assessment.get(key)) is not bool:
                raise RecordError(f"challenge assessment {key} must be boolean")
        require_text(result, "rationale")
        for key in ("cue_rewrite", "usage_note"):
            if not isinstance(result.get(key), str):
                raise RecordError(f"{key} must be a string")
        if not isinstance(result.get("support"), list) or any(
            not isinstance(x, str) for x in result["support"]
        ):
            raise RecordError("challenge support must be strings")
        if result["outcome"] == "contrast-needs-qualification" and not (
            result["cue_rewrite"].strip() or result["usage_note"].strip()
        ):
            raise RecordError("qualification must specify a correction")
    elif role in {"independent-verification", "adversarial-review"}:
        if result.get("verdict") not in {"agree", "object"}:
            raise RecordError("verdict must be agree or object")
        require_list(result, "concerns")
        require_text(result, "rationale")
        if role == "independent-verification":
            if result.get("relation") not in RELATIONS:
                raise RecordError("verifier must independently select a relation")
            structured_keys = {
                "cue_alignment",
                "cue_rewrite",
                "cue_rationale",
                "shared_synonym_case",
                "shared_synonym_rationale",
                "nonblocking_risk",
                "risk_rationale",
            }
            if structured_keys.intersection(result):
                if not structured_keys.issubset(result):
                    raise RecordError("structured verifier fields must be complete")
                if result["cue_alignment"] not in {"aligned", "correctable", "material-risk"}:
                    raise RecordError("invalid cue_alignment")
                if result["shared_synonym_case"] not in {
                    "none",
                    "useful-preference",
                    "weak-contrast",
                    "nonpreferred-alternative",
                }:
                    raise RecordError("invalid shared_synonym_case")
                if result["nonblocking_risk"] not in {"none", "minor", "concrete", "substantial"}:
                    raise RecordError("invalid nonblocking_risk")
                for key in ("cue_rationale", "shared_synonym_rationale"):
                    require_text(result, key)
                for key in ("cue_rewrite", "risk_rationale"):
                    if not isinstance(result[key], str):
                        raise RecordError(f"{key} must be a string")
            if "material_concerns" in result and (
                not isinstance(result["material_concerns"], list)
                or any(
                    not isinstance(value, str) or not value.strip()
                    for value in result["material_concerns"]
                )
            ):
                raise RecordError("material_concerns must be a list of nonempty strings")
            if "preference_risk" in result:
                from .preference_risk import validate_preference_risk

                try:
                    validate_preference_risk(result["preference_risk"])
                except ValueError as exc:
                    raise RecordError(str(exc)) from exc
            if "objection_assessments" in result:
                for item in require_list(result, "objection_assessments"):
                    assessment = require_mapping(item, "objection assessment")
                    require_text(assessment, "objection")
                    require_text(assessment, "resolution")
                    if type(assessment.get("material")) is not bool:
                        raise RecordError("objection material must be a boolean")
            if "affirmative_defect" in result:
                require_text(result, "affirmative_defect")
            if "competing_form" in result:
                competitor = require_mapping(result["competing_form"], "competing form")
                if competitor.get("status") not in {
                    "none",
                    "weak-alternative",
                    "credible-everyday",
                }:
                    raise RecordError("invalid competing-form status")
                if competitor.get("language") not in {"none", "indonesian", "malaysian", "both"}:
                    raise RecordError("invalid competing-form language")
                if type(competitor.get("same_sense")) is not bool:
                    raise RecordError("competing-form same_sense must be boolean")
                require_text(competitor, "rationale")
                if not isinstance(competitor.get("form"), str):
                    raise RecordError("competing-form form must be a string")
                if competitor["status"] == "credible-everyday" and (
                    not competitor["form"].strip()
                    or competitor["language"] == "none"
                    or not competitor["same_sense"]
                ):
                    raise RecordError("credible competing form needs a named same-sense form")
    return dict(data)
