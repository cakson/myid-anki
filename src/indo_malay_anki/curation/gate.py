"""Deterministic candidate disposition from separate, inspectable stages."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Any

from .duplicates import overlap_allows_new_id
from .evidence import assess_evidence
from .records import AI_ROLES, RELATIONS


def _relation_form_reasons(candidate: Mapping[str, Any], relation: str) -> list[str]:
    """Catch labels that visibly contradict the proposed answer forms."""
    left = unicodedata.normalize("NFKC", str(candidate.get("indonesian", ""))).casefold()
    right = unicodedata.normalize("NFKC", str(candidate.get("malaysian", ""))).casefold()
    same_form = " ".join(left.split()) == " ".join(right.split())
    if (relation == "same" and not same_form) or (
        relation in {"similar", "different-common-word"} and same_form
    ):
        return ["relation-form-mismatch"]
    return []


def _shared_vocabulary(candidate: Mapping[str, Any], relation: str) -> bool:
    """Identical ordinary forms have no cross-language recall value for this deck."""
    return relation == "same" and not _relation_form_reasons(candidate, relation)


def _decision(
    outcome: str, reasons: list[str], stages: Mapping[str, Any], relation: str = ""
) -> dict[str, Any]:
    statuses = {role: "complete" if role in stages else "missing" for role in AI_ROLES}
    return {
        "outcome": outcome,
        "relation": relation,
        "reason_codes": sorted(set(reasons)),
        "confidence_basis": {
            "completed_stages": [role for role, status in statuses.items() if status == "complete"],
            "uncompleted_stages": [
                role for role, status in statuses.items() if status != "complete"
            ],
            "evidence": "audited" if "evidence-audit" in stages else "missing",
        },
        "stage_statuses": statuses,
    }


def preverification_reasons(
    candidate: Mapping[str, Any], stages: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    """Screen cheap deterministic and evidence failures before costly review roles."""
    required = (
        "normalize-and-dedupe",
        "indonesian-usage",
        "malaysian-usage",
        "relation-proposal",
        "evidence-audit",
    )
    missing = [f"missing-stage:{role}" for role in required if role not in stages]
    if missing:
        return missing
    reasons: list[str] = []
    overlaps = stages["normalize-and-dedupe"].get("overlaps", [])
    if not isinstance(overlaps, list) or not overlap_allows_new_id(
        overlaps, legacy_id=candidate.get("legacy_id")
    ):
        reasons.append("unresolved-overlap")
    relation_result = stages["relation-proposal"]
    relation = str(relation_result.get("relation", ""))
    if relation not in RELATIONS:
        reasons.append("invalid-relation")
    reasons.extend(_relation_form_reasons(candidate, relation))
    if _shared_vocabulary(candidate, relation):
        reasons.append("no-cross-language-difference")
    if relation_result.get("aligned") is not True:
        reasons.append("semantic-mismatch-or-ambiguity")
    if relation_result.get("english") != candidate.get("english"):
        reasons.append("cue-mismatch")
    indonesian = stages["indonesian-usage"]
    malaysian = stages["malaysian-usage"]
    claims = (
        list(indonesian.get("claims", []))
        + list(malaysian.get("claims", []))
        + list(relation_result.get("claims", []))
    )
    observations = stages["evidence-audit"].get("observations")
    if not isinstance(observations, list):
        reasons.append("missing-audit-observations")
        observations = []
    evidence_ok, evidence_reasons = assess_evidence(claims, observations, relation=relation)
    if not evidence_ok:
        reasons.extend(evidence_reasons)
    if relation == "different-common-word":
        for locale in (indonesian, malaysian):
            if not any(
                claim.get("claim_type") == "preferred-choice" for claim in locale.get("claims", [])
            ):
                reasons.append("missing-within-locale-preference")
    if relation == "false-friend":
        contrast = relation_result.get("contrast")
        if (
            not isinstance(contrast, dict)
            or not all(
                isinstance(contrast.get(key), str) and contrast[key].strip()
                for key in ("misleading_form", "misleading_language", "actual_meaning")
            )
            or not contrast.get("claim_ids")
        ):
            reasons.append("incomplete-false-friend-contrast")
    return sorted(set(reasons))


def preaudit_reasons(
    candidate: Mapping[str, Any], stages: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    """Reject structural or semantic failures before external research is requested."""
    required = (
        "normalize-and-dedupe",
        "indonesian-usage",
        "malaysian-usage",
        "relation-proposal",
    )
    missing = [f"missing-stage:{role}" for role in required if role not in stages]
    if missing:
        return missing
    reasons = []
    overlaps = stages["normalize-and-dedupe"].get("overlaps", [])
    if not isinstance(overlaps, list) or not overlap_allows_new_id(
        overlaps, legacy_id=candidate.get("legacy_id")
    ):
        reasons.append("unresolved-overlap")
    relation = stages["relation-proposal"]
    relation_value = str(relation.get("relation", ""))
    reasons.extend(_relation_form_reasons(candidate, relation_value))
    if _shared_vocabulary(candidate, relation_value):
        reasons.append("no-cross-language-difference")
    if relation.get("aligned") is not True:
        reasons.append("semantic-mismatch-or-ambiguity")
    if relation.get("english") != candidate.get("english"):
        reasons.append("cue-mismatch")
    if relation.get("relation") == "different-common-word" and any(
        not any(
            claim.get("claim_type") == "preferred-choice"
            for claim in stages[role].get("claims", [])
        )
        for role in ("indonesian-usage", "malaysian-usage")
    ):
        reasons.append("missing-within-locale-preference")
    claims = [
        claim
        for role in ("indonesian-usage", "malaysian-usage", "relation-proposal")
        for claim in stages[role].get("claims", [])
    ]
    claim_ids = [claim.get("claim_id") for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        reasons.append("duplicate-claim-id")
    return reasons


def decide_candidate(
    candidate: Mapping[str, Any],
    stages: Mapping[str, Mapping[str, Any]],
    *,
    explicit_final: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return accepted only when all independent process gates pass.

    An explicit early hold/rejection records why work stopped. Failed automatic checks remain
    pending until corrected or deliberately finalized, except a confirmed duplicate.
    """
    if explicit_final is not None:
        outcome = explicit_final.get("outcome")
        reason = explicit_final.get("reason", "")
        if outcome not in {"hold", "rejected"} or not reason.strip():
            raise ValueError("explicit final decision requires hold/rejected and a reason")
        decision = _decision(outcome, [f"explicit-{outcome}"], stages)
        decision["decision_reason"] = reason
        return decision

    missing = [role for role in AI_ROLES if role not in stages]
    overlap_result = stages.get("normalize-and-dedupe", {})
    overlaps = overlap_result.get("overlaps", [])
    if isinstance(overlaps, list) and any(
        isinstance(item, dict) and item.get("resolution") in {"merge", "reject"}
        for item in overlaps
    ):
        return _decision("rejected", ["confirmed-duplicate"], stages)
    relation_result = stages.get("relation-proposal", {})
    relation = str(relation_result.get("relation", ""))
    if _shared_vocabulary(candidate, relation):
        return _decision("rejected", ["no-cross-language-difference"], stages, relation)
    if missing:
        return _decision("pending", ["missing-stage:" + role for role in missing], stages)

    relation_result = stages["relation-proposal"]
    reasons = preverification_reasons(candidate, stages)

    verifier = stages["independent-verification"]
    adversary = stages["adversarial-review"]
    if verifier.get("verdict") != "agree" or verifier.get("relation") != relation:
        reasons.append("verifier-disagreement")
    if adversary.get("verdict") != "agree" or adversary.get("concerns"):
        reasons.append("adversarial-objection")
    if reasons:
        return _decision("pending", reasons, stages, relation)
    return _decision("accepted", ["all-gates-passed"], stages, relation)
