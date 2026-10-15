"""Deterministic candidate disposition from separate, inspectable stages."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Any

from .duplicates import overlap_allows_new_id
from .evidence import assess_evidence
from .packets import digest
from .preference_risk import preference_flags
from .records import AI_ROLES, RELATIONS

AFFIRMATIVE_REJECTION_CODES = frozenset(
    {
        "confirmed-duplicate",
        "no-cross-language-difference",
        "no-meaningful-cross-language-contrast",
        "no-meaningful-preference-contrast",
        "confirmed-semantic-mismatch",
        "incorrect-translation",
        "confirmed-misleading-usage",
        "artificial-synonym",
        "low-learning-value",
        "false-friend-disproved",
    }
)
REJECTION_CODES_REQUIRING_REFERENCE = frozenset(
    {
        "confirmed-semantic-mismatch",
        "incorrect-translation",
        "confirmed-misleading-usage",
        "false-friend-disproved",
    }
)


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


def _confirmed_no_contrast(
    candidate: Mapping[str, Any], stages: Mapping[str, Mapping[str, Any]]
) -> bool:
    """Filter exact ordinary matches, but leave plausible false friends for review."""
    if _relation_form_reasons(candidate, "same"):
        return False
    proposal = stages.get("relation-proposal", {})
    verifier = stages.get("independent-verification", {})
    if proposal.get("relation") == "false-friend" or verifier.get("relation") == "false-friend":
        return False
    return (
        (proposal.get("relation") == "same" and proposal.get("aligned") is True)
        or verifier.get("relation") == "same"
        and verifier.get("verdict") == "agree"
    )


def _v3_decision(
    candidate: Mapping[str, Any], stages: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Optimistic ordinary gate; historical evidence and objections remain inspectable."""
    proposal = stages.get("relation-proposal", {})
    verifier = stages.get("independent-verification", {})
    proposed = str(proposal.get("relation", ""))
    relation = str(verifier.get("relation") or proposed)
    overlaps = stages.get("normalize-and-dedupe", {}).get("overlaps", [])
    duplicate = isinstance(overlaps, list) and any(
        isinstance(item, dict) and item.get("resolution") in {"merge", "reject"}
        for item in overlaps
    )
    unresolved_overlap = isinstance(overlaps, list) and any(
        isinstance(item, dict) and item.get("resolution") == "unresolved" for item in overlaps
    )
    historical = stages.get("adversarial-review", {})
    historical_objections = (
        historical.get("objections") or historical.get("concerns") or []
        if historical.get("verdict") == "object"
        else []
    )
    assessments = verifier.get("objection_assessments", [])
    assessed = {
        item.get("objection"): item
        for item in assessments
        if isinstance(item, dict) and isinstance(item.get("objection"), str)
    }
    unresolved_historical = [
        objection
        for objection in historical_objections
        if objection not in assessed or assessed[objection].get("material") is True
    ]
    contradictions = [
        item
        for item in stages.get("evidence-audit", {}).get("observations", [])
        if isinstance(item, dict) and item.get("stance") == "contradicts"
    ]
    material = [
        str(item)
        for item in verifier.get("material_concerns", [])
        if isinstance(item, str) and item.strip()
    ]
    reasons: list[str] = []
    outcome = "pending"
    tier = "high" if relation == "false-friend" else "low"
    path = "false-friend" if relation == "false-friend" else "ordinary-fast"
    flags: set[str] = set()
    if duplicate:
        outcome, reasons = "rejected", ["confirmed-duplicate"]
    elif _confirmed_no_contrast(candidate, stages):
        outcome, relation, reasons = (
            "rejected",
            "same",
            ["no-meaningful-cross-language-contrast"],
        )
    elif not verifier:
        reasons = ["missing-independent-verification"]
    else:
        if proposed in RELATIONS and proposed != relation:
            flags.add("relation-corrected")
        if not stages.get("evidence-audit", {}).get("observations"):
            flags.add("limited-evidence")
        if relation == "different-common-word":
            observations = stages.get("evidence-audit", {}).get("observations", [])
            if not any(
                item.get("claim_type") == "preferred-choice"
                and item.get("usage_basis") in {"comparative", "contextual"}
                and item.get("stance") == "supports"
                for item in observations
                if isinstance(item, dict)
            ):
                flags.add("usage-preference-weak")
        if historical_objections:
            flags.add("historical-objection")
        if verifier.get("concerns") and not material:
            flags.add("limited-verifier-agreement")
        if unresolved_overlap:
            material.append("Unresolved semantic overlap could create a duplicate concept.")
        if unresolved_historical:
            material.extend(
                f"Unresolved historical objection: {item}" for item in unresolved_historical
            )
        if contradictions:
            material.append("Claim-linked evidence contradicts the proposed card.")
        if relation not in RELATIONS:
            material.append("The verified relation is missing or invalid.")
        if relation == "same":
            outcome, reasons = "rejected", ["no-meaningful-cross-language-contrast"]
        elif verifier.get("affirmative_defect"):
            outcome, reasons = "rejected", [str(verifier["affirmative_defect"])]
        elif verifier.get("verdict") != "agree" and not material:
            material.append("The independent verifier disagrees without resolving the pairing.")
        if outcome == "pending" and material:
            outcome, reasons, path = "hold", material, "escalated"
            tier = "high" if relation == "false-friend" else "medium"
        elif outcome == "pending" and relation == "false-friend":
            adversary = stages.get("adversarial-review", {})
            evidence_ok, evidence_reasons = assess_evidence(
                [
                    claim
                    for role in ("indonesian-usage", "malaysian-usage", "relation-proposal")
                    for claim in stages.get(role, {}).get("claims", [])
                ],
                stages.get("evidence-audit", {}).get("observations", []),
                relation="false-friend",
            )
            if not evidence_ok or adversary.get("verdict") != "agree":
                outcome, reasons = "hold", evidence_reasons or ["false-friend-review-incomplete"]
            else:
                outcome, reasons = "accepted", ["strict-false-friend-gate-passed"]
        elif outcome == "pending":
            outcome, reasons = "accepted", ["ordinary-verifier-agreement"]
    risk = {"tier": tier, "path": path, "triggers": reasons if path != "ordinary-fast" else []}
    decision = _decision(outcome, reasons, stages, relation, policy_version="3.0.0", risk=risk)
    decision["review_flags"] = sorted(flags) if outcome == "accepted" else []
    if proposed in RELATIONS and proposed != relation:
        decision["relation_correction"] = {"from": proposed, "to": relation}
    if outcome == "accepted":
        if relation == "false-friend":
            confidence = "medium"
        elif len(flags) >= 3:
            confidence = "very-low"
        elif "relation-corrected" in flags or "historical-objection" in flags:
            confidence = "low"
        elif flags:
            confidence = "medium"
        else:
            confidence = "high"
        decision["confidence_tier"] = confidence
        rationale = str(verifier.get("rationale", "")).strip()
        if not rationale:
            rationale = (
                f"The verifier supports {candidate.get('english', 'this cue')} as a "
                f"{relation} contrast."
            )
        caveats = [
            str(item).strip()
            for item in verifier.get("concerns", [])
            if isinstance(item, str) and item.strip()
        ]
        if caveats and caveats[0].casefold() not in rationale.casefold():
            rationale += " Verifier caveat: " + caveats[0].rstrip(".") + "."
        if "usage-preference-weak" in flags:
            rationale += " Direct comparative preference evidence was not collected."
        decision["confidence_rationale"] = rationale
    return decision


V31_CUE_ALIGNMENT = frozenset({"aligned", "correctable", "material-risk"})
V31_SYNONYM_CASES = frozenset(
    {"none", "useful-preference", "weak-contrast", "nonpreferred-alternative"}
)
V31_NONBLOCKING_RISKS = frozenset({"none", "minor", "concrete", "substantial"})


def _v31_decision(
    candidate: Mapping[str, Any], stages: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Apply structured cue/synonym routing and risk-based confidence to the v3 fast path."""
    verifier = stages.get("independent-verification", {})
    if not verifier:
        decision = _v3_decision(candidate, stages)
        decision["decision_policy_version"] = "3.1.0"
        return decision
    cue = verifier.get("cue_alignment")
    synonym = verifier.get("shared_synonym_case")
    risk = verifier.get("nonblocking_risk")
    material = list(verifier.get("material_concerns", []))
    if cue not in V31_CUE_ALIGNMENT or synonym not in V31_SYNONYM_CASES:
        material.append("Structured cue/synonym verification is incomplete.")
    if risk not in V31_NONBLOCKING_RISKS:
        material.append("Structured nonblocking-risk assessment is incomplete.")
    if not str(verifier.get("rationale", "")).strip():
        material.append("Candidate-specific verifier rationale is missing.")
    if not str(verifier.get("cue_rationale", "")).strip():
        material.append("Cue and sense alignment was not explained.")
    if not str(verifier.get("shared_synonym_rationale", "")).strip():
        material.append("Shared-synonym assessment was not explained.")
    cue_rewrite = str(verifier.get("cue_rewrite", "")).strip()
    if cue == "material-risk":
        material.append("The English cue may misalign the two target-language senses.")
    elif cue == "correctable":
        if (
            not cue_rewrite
            or cue_rewrite.casefold() == str(candidate.get("english", "")).casefold()
        ):
            material.append("A specific corrected English cue is required.")
    elif cue_rewrite:
        material.append("An unexplained cue rewrite requires review.")
    if synonym == "weak-contrast" and not verifier.get("affirmative_defect"):
        material.append("A shared ordinary synonym may defeat the claimed national preference.")
    if risk != "none" and not str(verifier.get("risk_rationale", "")).strip():
        material.append("A concrete reason for the nonblocking risk is missing.")
    revised_verifier = {**verifier, "material_concerns": material}
    revised_stages = {**stages, "independent-verification": revised_verifier}
    decision = _v3_decision(candidate, revised_stages)
    decision["decision_policy_version"] = "3.1.0"
    if decision["outcome"] != "accepted":
        return decision
    flags: set[str] = set()
    if decision.get("relation_correction"):
        flags.add("relation-corrected")
    if cue == "correctable":
        flags.add("cue-corrected")
        decision["cue_correction"] = {"from": candidate["english"], "to": cue_rewrite}
    if synonym == "useful-preference":
        flags.add("shared-synonym-preference")
    elif synonym == "nonpreferred-alternative":
        flags.add("nonpreferred-alternative")
    if risk in {"concrete", "substantial"}:
        flags.add(f"{risk}-nonblocking-risk")
    # Preference risk affects confidence and audit priority, never the v3.1
    # ACCEPT/HOLD/REJECT gate. Historical verifier results lack this field.
    preference = verifier.get("preference_risk")
    if isinstance(preference, dict):
        flags.update(preference_flags(preference))
    if "historical-objection" in decision.get("review_flags", []):
        flags.add("historical-objection")
    if decision["relation"] == "false-friend":
        confidence = "medium"
    elif risk == "substantial":
        confidence = "very-low"
    elif (
        risk == "concrete"
        or cue == "correctable"
        or decision.get("relation_correction")
        or "historical-objection" in flags
    ):
        confidence = "low"
    elif risk == "minor" or synonym == "useful-preference":
        confidence = "medium"
    else:
        confidence = "high"
    if preference_flags(preference) and confidence == "high":
        confidence = "medium"
    rationale = str(verifier.get("rationale", "")).strip()
    if cue == "correctable":
        rationale += f" The concise cue is narrowed to {cue_rewrite}."
    if risk != "none":
        reason = str(verifier.get("risk_rationale", "")).strip()
        if reason.casefold() not in rationale.casefold():
            rationale += f" Review concern: {reason.rstrip('.')}."
    decision["confidence_tier"] = confidence
    decision["confidence_rationale"] = rationale.strip()
    decision["review_flags"] = sorted(flags)
    decision["confidence_basis"]["cue_alignment"] = cue
    decision["confidence_basis"]["shared_synonym_case"] = synonym
    decision["confidence_basis"]["nonblocking_risk"] = risk
    if isinstance(preference, dict):
        decision["confidence_basis"]["preference_risk"] = preference
    return decision


def _v32_decision(
    candidate: Mapping[str, Any], stages: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Challenge only a named, credible same-sense everyday competitor."""
    base = _v31_decision(candidate, stages)
    base["decision_policy_version"] = "3.2.0"
    if base["outcome"] != "accepted" or base["relation"] != "different-common-word":
        return base
    verifier = stages.get("independent-verification", {})
    competitor = verifier.get("competing_form")
    if not isinstance(competitor, dict):
        return _v32_hold(base, "Structured competing-form assessment is missing.")
    status = competitor.get("status")
    if status not in {"none", "weak-alternative", "credible-everyday"}:
        return _v32_hold(base, "Structured competing-form status is invalid.")
    if status != "credible-everyday":
        base["confidence_basis"]["competing_form"] = status
        return base
    if (
        not str(competitor.get("form", "")).strip()
        or competitor.get("language") not in {"indonesian", "malaysian", "both"}
        or competitor.get("same_sense") is not True
    ):
        return _v32_hold(base, "A credible everyday competitor must be named in the same sense.")
    challenge = stages.get("competing-form-challenge", {})
    if not challenge:
        return _v32_hold(base, "A named credible everyday competitor needs a targeted challenge.")
    outcome = challenge.get("outcome")
    rationale = str(challenge.get("rationale", "")).strip()
    assessment = challenge.get("assessment", {})
    if not rationale or not isinstance(assessment, dict):
        return _v32_hold(base, "Targeted challenge result is incomplete.")
    if outcome == "preference-materially-uncertain":
        return _v32_hold(
            base, f"Targeted preference challenge unresolved: {rationale}", completed=True
        )
    if outcome == "no-meaningful-preference-contrast":
        base.update(
            outcome="rejected",
            reason_codes=["no-meaningful-preference-contrast"],
            rejection_reason=rationale,
            risk={"tier": "medium", "path": "escalated", "triggers": ["credible-competing-form"]},
        )
        for key in ("confidence_tier", "confidence_rationale", "review_flags"):
            base.pop(key, None)
        base["stage_statuses"]["competing-form-challenge"] = "complete"
        return base
    if outcome not in {"contrast-remains-useful", "contrast-needs-qualification"}:
        return _v32_hold(base, "Targeted challenge outcome is invalid.")
    if assessment.get("normal_everyday_same_sense") is not True:
        return _v32_hold(
            base,
            "Challenge did not resolve whether the named form is everyday usage.",
            completed=True,
        )
    if assessment.get("useful_difference_remains") is not True:
        return _v32_hold(
            base, "Challenge did not establish a useful preference difference.", completed=True
        )
    if assessment.get("unqualified_card_misleads") and outcome == "contrast-remains-useful":
        return _v32_hold(
            base, "The unqualified card may mislead; a correction is required.", completed=True
        )
    if outcome == "contrast-needs-qualification":
        rewrite = str(challenge.get("cue_rewrite", "")).strip()
        note = str(challenge.get("usage_note", "")).strip()
        if assessment.get("unqualified_card_misleads") and not rewrite:
            return _v32_hold(
                base,
                "Learner-visible qualification is needed but no corrected cue was supplied.",
                completed=True,
            )
        if not rewrite and not note:
            return _v32_hold(
                base, "Qualification outcome lacks an applicable correction.", completed=True
            )
        if rewrite:
            base["cue_correction"] = {"from": candidate["english"], "to": rewrite}
            base.setdefault("review_flags", []).append("cue-corrected")
        if note:
            base["usage_note_correction"] = note
        base["confidence_tier"] = "low"
        base.setdefault("review_flags", []).append("competing-form-qualified")
    else:
        if base["confidence_tier"] == "high":
            base["confidence_tier"] = "medium"
        base.setdefault("review_flags", []).append("competing-form-reviewed")
    base["review_flags"] = sorted(set(base["review_flags"]))
    base["confidence_rationale"] += f" Competing form {competitor['form']}: {rationale}"
    base["confidence_basis"]["competing_form"] = status
    base["confidence_basis"]["challenge_outcome"] = outcome
    base["risk"] = {"tier": "medium", "path": "escalated", "triggers": ["credible-competing-form"]}
    base["stage_statuses"]["competing-form-challenge"] = "complete"
    return base


def _v32_hold(base: dict[str, Any], reason: str, *, completed: bool = False) -> dict[str, Any]:
    base.update(
        outcome="hold",
        reason_codes=[reason],
        risk={"tier": "medium", "path": "escalated", "triggers": ["credible-competing-form"]},
    )
    for key in ("confidence_tier", "confidence_rationale", "review_flags"):
        base.pop(key, None)
    base["stage_statuses"]["competing-form-challenge"] = "complete" if completed else "missing"
    return base


def _decision(
    outcome: str,
    reasons: list[str],
    stages: Mapping[str, Any],
    relation: str = "",
    *,
    policy_version: str = "1.0.0",
    risk: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    statuses = {role: "complete" if role in stages else "missing" for role in AI_ROLES}
    if policy_version in {"3.0.0", "3.1.0", "3.2.0"}:
        for optional in (
            "indonesian-usage",
            "malaysian-usage",
            "relation-proposal",
            "evidence-audit",
            "adversarial-review",
        ):
            if optional not in stages and risk is not None and risk.get("path") == "ordinary-fast":
                statuses[optional] = "skipped-by-policy"
    elif risk is not None and outcome == "accepted" and risk["path"] == "ordinary-fast":
        if "adversarial-review" not in stages:
            statuses["adversarial-review"] = "skipped"
    result = {
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
        "decision_policy_version": policy_version,
        "risk": dict(risk) if risk is not None else {"path": "not-assessed", "triggers": []},
        "skipped_stages": (
            {
                role: "skipped-by-policy"
                for role, status in statuses.items()
                if status == "skipped-by-policy"
            }
            if policy_version in {"3.0.0", "3.1.0", "3.2.0"}
            else {"adversarial-review": "skipped-low-risk"}
            if statuses["adversarial-review"] == "skipped"
            else {}
        ),
    }
    if policy_version == "2.0.0":
        result["input_digest"] = digest(stages)
        result["evidence_digest"] = (
            digest(stages["evidence-audit"]) if "evidence-audit" in stages else None
        )
        result["required_stages"] = [
            role
            for role in AI_ROLES
            if role != "adversarial-review"
            or risk is None
            or risk.get("path") in {"escalated", "false-friend"}
        ]
    return result


def classify_risk(
    candidate: Mapping[str, Any], stages: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """Classify material risk from recorded claims, evidence and verifier output."""
    relation_result = stages.get("relation-proposal", {})
    relation = str(relation_result.get("relation", ""))
    if relation not in RELATIONS:
        return {"path": "not-assessed", "triggers": ["missing-relation"]}
    if relation == "false-friend":
        return {"path": "false-friend", "triggers": ["false-friend"]}
    required_for_assessment = (
        "normalize-and-dedupe",
        "indonesian-usage",
        "malaysian-usage",
        "relation-proposal",
        "evidence-audit",
        "independent-verification",
    )
    missing_for_assessment = [role for role in required_for_assessment if role not in stages]
    if missing_for_assessment:
        return {
            "path": "not-assessed",
            "triggers": [f"missing-stage:{role}" for role in missing_for_assessment],
        }
    triggers: set[str] = set()
    if relation_result.get("aligned") is False or relation_result.get("english") != candidate.get(
        "english"
    ):
        triggers.add("semantic-ambiguity")
    if _relation_form_reasons(candidate, relation):
        triggers.add("relation-form-mismatch")
    if not overlap_allows_new_id(
        stages.get("normalize-and-dedupe", {}).get("overlaps", []),
        legacy_id=candidate.get("legacy_id"),
    ):
        triggers.add("semantic-overlap")
    required = (
        "normalize-and-dedupe",
        "indonesian-usage",
        "malaysian-usage",
        "relation-proposal",
        "evidence-audit",
    )
    if all(role in stages for role in required):
        for reason in preverification_reasons(candidate, stages):
            if reason == "contradictory-evidence":
                triggers.add("conflicting-evidence")
            elif reason.startswith("unsupported-claim:") or reason in {
                "insufficient-independent-sources",
                "dictionary-only-preference",
                "missing-within-locale-preference",
                "missing-audit-observations",
                "uninspected-evidence",
            }:
                triggers.add("weak-evidence")
            elif reason in {"cue-mismatch", "semantic-mismatch-or-ambiguity"}:
                triggers.add("semantic-ambiguity")
            elif reason == "unresolved-overlap":
                triggers.add("semantic-overlap")
            else:
                triggers.add(reason)
    for role in ("indonesian-usage", "malaysian-usage"):
        usage = stages.get(role, {})
        if any(
            word in str(usage.get("common_use", "")).casefold()
            for word in ("rare", "uncommon", "archaic", "niche", "specialized")
        ):
            triggers.add("rarity")
        register = str(usage.get("register", "")).casefold().strip(" .;:")
        neutral_register = register in {
            "neutral",
            "standard",
            "everyday",
            "common",
        } or register.startswith(("neutral everyday", "neutral standard", "neutral;"))
        material_register = any(
            word in register
            for word in ("formal only", "colloquial only", "archaic", "regional only")
        )
        if register and not neutral_register and material_register:
            triggers.add("register-ambiguity")
        region = str(usage.get("region", "")).casefold().strip(" .;:")
        expected = "indonesia" if role == "indonesian-usage" else "malaysia"
        material_region = any(
            word in region for word in ("limited to", "only in", "regional only", "not nationwide")
        )
        if region and material_region and expected not in region:
            triggers.add("regional-ambiguity")
        for flag in usage.get("risk_flags", []):
            if isinstance(flag, str):
                triggers.add(flag)
    for flag in relation_result.get("risk_flags", []):
        if isinstance(flag, str):
            triggers.add(flag)
    verifier = stages.get("independent-verification")
    if verifier is not None:
        if verifier.get("verdict") != "agree" or verifier.get("relation") != relation:
            triggers.add("verifier-disagreement")
        if verifier.get("material_concerns", verifier.get("concerns")):
            triggers.add("verifier-concern")
    adversary = stages.get("adversarial-review", {})
    if adversary.get("verdict") == "object" and (
        adversary.get("objections") or adversary.get("concerns")
    ):
        triggers.add("historical-adversarial-objection")
    return {
        "path": "escalated" if triggers else "ordinary-fast",
        "triggers": sorted(triggers),
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


def _decide_candidate_v1(
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


def decide_candidate(
    candidate: Mapping[str, Any],
    stages: Mapping[str, Mapping[str, Any]],
    *,
    explicit_final: Mapping[str, Any] | None = None,
    policy_version: str = "1.0.0",
) -> dict[str, Any]:
    """Apply a manifest-pinned decision policy without rewriting older batch history."""
    if policy_version == "1.0.0":
        return _decide_candidate_v1(candidate, stages, explicit_final=explicit_final)
    if policy_version in {"3.0.0", "3.1.0", "3.2.0"}:
        if explicit_final is not None:
            outcome = explicit_final.get("outcome")
            reason = explicit_final.get("reason", "")
            if outcome == "rejected":
                code = explicit_final.get("reason_code")
                if (
                    code not in AFFIRMATIVE_REJECTION_CODES
                    or not isinstance(reason, str)
                    or not reason.strip()
                ):
                    raise ValueError("policy v3 rejection requires an affirmative reason")
                result = _decision("rejected", [code], stages, policy_version=policy_version)
                result["decision_reason"] = reason
                return result
            if (
                outcome == "hold"
                and isinstance(reason, str)
                and reason.strip()
                and explicit_final.get("material_issue")
            ):
                result = _decision(
                    "hold", ["material-unresolved-issue"], stages, policy_version=policy_version
                )
                result["decision_reason"] = reason
                return result
            raise ValueError("policy v3 hold requires a concrete material issue")
        if policy_version == "3.2.0":
            return _v32_decision(candidate, stages)
        if policy_version == "3.1.0":
            return _v31_decision(candidate, stages)
        return _v3_decision(candidate, stages)
    if policy_version != "2.0.0":
        raise ValueError(f"unsupported decision policy: {policy_version}")
    relation = str(stages.get("relation-proposal", {}).get("relation", ""))
    risk = classify_risk(candidate, stages)
    if explicit_final is not None:
        outcome = explicit_final.get("outcome")
        reason = explicit_final.get("reason")
        if outcome == "hold" and isinstance(reason, str) and reason.strip():
            decision = _decision(
                "hold",
                ["explicit-hold"],
                stages,
                relation,
                policy_version=policy_version,
                risk=risk,
            )
        elif outcome == "rejected" and isinstance(reason, str) and reason.strip():
            code = explicit_final.get("reason_code")
            reference = explicit_final.get("evidence_ref")
            if code not in AFFIRMATIVE_REJECTION_CODES:
                raise ValueError("policy v2 rejection requires an affirmative reason_code")
            if code in REJECTION_CODES_REQUIRING_REFERENCE and not reference:
                raise ValueError(f"{code} requires evidence_ref")
            decision = _decision(
                "rejected",
                [str(code)],
                stages,
                relation,
                policy_version=policy_version,
                risk=risk,
            )
            if reference:
                decision["evidence_ref"] = reference
        else:
            raise ValueError("explicit final decision requires hold/rejected and a reason")
        decision["decision_reason"] = reason
        return decision
    overlaps = stages.get("normalize-and-dedupe", {}).get("overlaps", [])
    if isinstance(overlaps, list) and any(
        isinstance(item, dict) and item.get("resolution") in {"merge", "reject"}
        for item in overlaps
    ):
        return _decision(
            "rejected",
            ["confirmed-duplicate"],
            stages,
            relation,
            policy_version=policy_version,
            risk=risk,
        )
    if _shared_vocabulary(candidate, relation):
        return _decision(
            "rejected",
            ["no-cross-language-difference"],
            stages,
            relation,
            policy_version=policy_version,
            risk=risk,
        )
    base_roles = (
        "generate",
        "normalize-and-dedupe",
        "indonesian-usage",
        "malaysian-usage",
        "relation-proposal",
        "evidence-audit",
        "independent-verification",
    )
    missing = [role for role in base_roles if role not in stages]
    if missing:
        return _decision(
            "pending",
            [f"missing-stage:{role}" for role in missing],
            stages,
            relation,
            policy_version=policy_version,
            risk=risk,
        )
    reasons = preverification_reasons(candidate, stages)
    verifier = stages["independent-verification"]
    if verifier.get("verdict") != "agree" or verifier.get("relation") != relation:
        reasons.append("verifier-disagreement")
    if verifier.get("material_concerns", verifier.get("concerns")):
        reasons.append("verifier-concern")
    if relation == "false-friend":
        adversary = stages.get("adversarial-review")
        if adversary is None:
            reasons.append("missing-stage:adversarial-review")
        elif adversary.get("verdict") != "agree" or adversary.get("concerns"):
            reasons.append("false-friend-adversarial-objection")
    elif risk["path"] == "escalated":
        if "adversarial-review" not in stages:
            reasons.append("missing-stage:adversarial-review")
        else:
            adversary = stages["adversarial-review"]
            if adversary.get("verdict") == "object":
                if adversary.get("objections") or adversary.get("concerns"):
                    reasons.append("concrete-adversarial-objection")
                else:
                    reasons.append("unresolved-adversarial-objection")
    if reasons:
        return _decision(
            "pending",
            sorted(set(reasons)),
            stages,
            relation,
            policy_version=policy_version,
            risk=risk,
        )
    return _decision(
        "accepted",
        ["all-applicable-gates-passed"],
        stages,
        relation,
        policy_version=policy_version,
        risk=risk,
    )
