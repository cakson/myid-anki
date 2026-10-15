"""Seeded process gates; these fixtures do not assert linguistic truth."""

from copy import deepcopy

import pytest

from indo_malay_anki.curation.gate import decide_candidate, preaudit_reasons


def v31_fixture():
    candidate, stages = candidate_and_stages()
    stages = {
        "normalize-and-dedupe": stages["normalize-and-dedupe"],
        "independent-verification": {
            "verdict": "agree",
            "relation": "different-common-word",
            "concerns": [],
            "material_concerns": [],
            "objection_assessments": [],
            "rationale": "Mobil and kereta denote the same road passenger vehicle.",
            "cue_alignment": "aligned",
            "cue_rewrite": "",
            "cue_rationale": "Both terms denote a car in the intended sense.",
            "shared_synonym_case": "none",
            "shared_synonym_rationale": "No competing ordinary shared synonym identified.",
            "nonblocking_risk": "none",
            "risk_rationale": "",
        },
    }
    return candidate, stages


def test_v31_clear_ordinary_candidate_is_high_without_external_research():
    candidate, stages = v31_fixture()
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "accepted"
    assert decision["confidence_tier"] == "high"
    assert decision["risk"]["path"] == "ordinary-fast"


def test_v31_preference_signal_routes_audit_without_becoming_a_veto():
    candidate, stages = v31_fixture()
    verifier = stages["independent-verification"]
    verifier["preference_risk"] = {
        "signal": "credible-everyday-alternative",
        "form": "auto",
        "language": "malaysian",
        "rationale": "Auto may compete in the same sense.",
    }
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "accepted"
    assert decision["risk"]["path"] == "ordinary-fast"
    assert decision["confidence_tier"] == "medium"
    assert "credible-competing-form" in decision["review_flags"]


def test_v31_shared_synonym_routes_by_materiality():
    candidate, stages = v31_fixture()
    verifier = stages["independent-verification"]
    verifier["shared_synonym_case"] = "useful-preference"
    verifier["shared_synonym_rationale"] = (
        "The shared alternative exists, but the national preference remains useful."
    )
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "accepted"
    assert decision["confidence_tier"] == "medium"
    verifier["shared_synonym_case"] = "weak-contrast"
    verifier["shared_synonym_rationale"] = "Both terms may be ordinary in both locales."
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "hold"
    verifier["shared_synonym_case"] = "nonpreferred-alternative"
    verifier["shared_synonym_rationale"] = "The alternate is nonstandard in the target locale."
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "accepted"
    assert decision["confidence_tier"] == "high"


def test_v31_cue_correction_and_concrete_risk():
    candidate, stages = v31_fixture()
    verifier = stages["independent-verification"]
    verifier["cue_alignment"] = "correctable"
    verifier["cue_rewrite"] = "passenger car"
    verifier["cue_rationale"] = "The qualifier excludes toy cars."
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "accepted"
    assert decision["confidence_tier"] == "low"
    assert decision["cue_correction"]["to"] == "passenger car"
    verifier["cue_alignment"] = "material-risk"
    verifier["cue_rewrite"] = ""
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "hold"


def test_v31_only_substantial_nonblocking_risk_is_very_low():
    candidate, stages = v31_fixture()
    verifier = stages["independent-verification"]
    verifier["nonblocking_risk"] = "substantial"
    verifier["risk_rationale"] = (
        "A specific register uncertainty remains but does not change the answer."
    )
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "accepted"
    assert decision["confidence_tier"] == "very-low"
    verifier.pop("risk_rationale")
    assert decide_candidate(candidate, stages, policy_version="3.1.0")["outcome"] == "hold"


def test_v31_incomplete_structured_verifier_holds_and_false_friend_stays_strict():
    candidate, stages = v31_fixture()
    stages["independent-verification"].pop("cue_alignment")
    assert decide_candidate(candidate, stages, policy_version="3.1.0")["outcome"] == "hold"
    stages["independent-verification"]["cue_alignment"] = "aligned"
    stages["independent-verification"]["relation"] = "false-friend"
    decision = decide_candidate(candidate, stages, policy_version="3.1.0")
    assert decision["outcome"] == "hold"
    assert decision["risk"]["path"] == "false-friend"


def test_v32_competing_form_triggers_only_when_credible():
    candidate, stages = v31_fixture()
    verifier = stages["independent-verification"]
    verifier["competing_form"] = {
        "status": "weak-alternative",
        "form": "automobil",
        "language": "indonesian",
        "same_sense": True,
        "rationale": "The alternate is unusual in ordinary speech.",
    }
    decision = decide_candidate(candidate, stages, policy_version="3.2.0")
    assert decision["outcome"] == "accepted"
    assert decision["risk"]["path"] == "ordinary-fast"
    verifier["competing_form"] = {
        "status": "credible-everyday",
        "form": "mobil",
        "language": "malaysian",
        "same_sense": True,
        "rationale": "The alternative may be ordinary in Malaysia.",
    }
    decision = decide_candidate(candidate, stages, policy_version="3.2.0")
    assert decision["outcome"] == "hold"
    assert "targeted challenge" in decision["reason_codes"][0]


def test_v32_challenge_can_resolve_qualify_hold_or_reject():
    candidate, stages = v31_fixture()
    stages["independent-verification"]["competing_form"] = {
        "status": "credible-everyday",
        "form": "mobil",
        "language": "malaysian",
        "same_sense": True,
        "rationale": "The alternate is an everyday same-sense form.",
    }
    stages["competing-form-challenge"] = {
        "outcome": "contrast-remains-useful",
        "assessment": {
            "normal_everyday_same_sense": True,
            "materially_weakens_preference": False,
            "useful_difference_remains": True,
            "unqualified_card_misleads": False,
        },
        "rationale": "The proposed contrast remains useful in ordinary contexts.",
        "cue_rewrite": "",
        "usage_note": "",
        "support": [],
    }
    decision = decide_candidate(candidate, stages, policy_version="3.2.0")
    assert decision["outcome"] == "accepted"
    assert decision["risk"]["path"] == "escalated"
    assert decision["confidence_tier"] == "medium"
    challenge = stages["competing-form-challenge"]
    challenge["outcome"] = "contrast-needs-qualification"
    challenge["cue_rewrite"] = "passenger car"
    challenge["assessment"]["unqualified_card_misleads"] = True
    decision = decide_candidate(candidate, stages, policy_version="3.2.0")
    assert decision["outcome"] == "accepted"
    assert decision["cue_correction"]["to"] == "passenger car"
    assert decision["confidence_tier"] == "low"
    challenge["outcome"] = "preference-materially-uncertain"
    assert decide_candidate(candidate, stages, policy_version="3.2.0")["outcome"] == "hold"
    challenge["outcome"] = "no-meaningful-preference-contrast"
    decision = decide_candidate(candidate, stages, policy_version="3.2.0")
    assert decision["outcome"] == "rejected"
    assert decision["relation"] == "different-common-word"
    assert decision["reason_codes"] == ["no-meaningful-preference-contrast"]


def test_v3_ordinary_accepts_without_external_preference_proof():
    candidate, stages = candidate_and_stages()
    stages.pop("evidence-audit")
    stages.pop("adversarial-review")
    stages["independent-verification"]["concerns"] = ["A named synonym is also attested."]
    decision = decide_candidate(candidate, stages, policy_version="3.0.0")
    assert decision["outcome"] == "accepted"
    assert decision["risk"]["path"] == "ordinary-fast"
    assert decision["confidence_tier"] in {"medium", "low", "very-low"}
    assert "usage-preference-weak" in decision["review_flags"]
    assert decision["confidence_rationale"]


def test_v3_rationale_retains_candidate_specific_verifier_reason_and_caveat():
    candidate, stages = candidate_and_stages()
    stages.pop("evidence-audit")
    stages["independent-verification"]["rationale"] = (
        "Mobil and kereta both denote the intended passenger car."
    )
    stages["independent-verification"]["concerns"] = ["Kereta has another sense in Indonesian."]
    decision = decide_candidate(candidate, stages, policy_version="3.0.0")
    assert decision["outcome"] == "accepted"
    assert "Mobil and kereta" in decision["confidence_rationale"]
    assert "another sense" in decision["confidence_rationale"]
    assert (
        "Direct comparative preference evidence was not collected"
        in decision["confidence_rationale"]
    )


def test_v3_material_issue_holds_and_affirmative_defect_rejects():
    candidate, stages = candidate_and_stages()
    verifier = stages["independent-verification"]
    verifier["material_concerns"] = ["A credible competing form may be the normal choice."]
    decision = decide_candidate(candidate, stages, policy_version="3.0.0")
    assert decision["outcome"] == "hold"
    assert "confidence_tier" not in decision
    verifier["material_concerns"] = []
    verifier["affirmative_defect"] = "incorrect-translation"
    decision = decide_candidate(candidate, stages, policy_version="3.0.0")
    assert decision["outcome"] == "rejected"
    assert "incorrect-translation" in decision["reason_codes"]


def test_v3_same_rejects_before_verifier_but_false_friend_does_not():
    candidate, stages = candidate_and_stages()
    candidate["indonesian"] = "kamera"
    candidate["malaysian"] = "kamera"
    stages = {"relation-proposal": {"relation": "same", "aligned": True}}
    decision = decide_candidate(candidate, stages, policy_version="3.0.0")
    assert decision["outcome"] == "rejected"
    assert decision["reason_codes"] == ["no-meaningful-cross-language-contrast"]
    assert "confidence_tier" not in decision
    stages["relation-proposal"]["relation"] = "false-friend"
    assert decide_candidate(candidate, stages, policy_version="3.0.0")["outcome"] == "pending"


def test_v3_historical_objection_requires_explicit_assessment():
    candidate, stages = candidate_and_stages()
    stages["adversarial-review"] = {
        "verdict": "object",
        "objections": ["A specific rival term may be the common Malaysian choice."],
    }
    assert decide_candidate(candidate, stages, policy_version="3.0.0")["outcome"] == "hold"
    stages["independent-verification"]["objection_assessments"] = [
        {
            "objection": "A specific rival term may be the common Malaysian choice.",
            "material": False,
            "resolution": "The rival is regional and does not defeat the card.",
        }
    ]
    assert decide_candidate(candidate, stages, policy_version="3.0.0")["outcome"] == "accepted"


def test_v3_false_friend_cannot_use_ordinary_fast_path():
    candidate, stages = candidate_and_stages()
    stages["relation-proposal"]["relation"] = "false-friend"
    stages["independent-verification"]["relation"] = "false-friend"
    stages.pop("adversarial-review")
    decision = decide_candidate(candidate, stages, policy_version="3.0.0")
    assert decision["outcome"] == "hold"
    assert decision["risk"]["path"] == "false-friend"
    assert "confidence_tier" not in decision


def candidate_and_stages():
    candidate = {
        "candidate_id": "car-01",
        "english": "car",
        "indonesian": "mobil",
        "malaysian": "kereta",
        "sense": "road passenger vehicle",
    }
    claims = [
        {"claim_id": "id-meaning", "claim_type": "meaning", "proposition": "Indonesian sense"},
        {"claim_id": "my-meaning", "claim_type": "meaning", "proposition": "Malaysian sense"},
        {
            "claim_id": "id-preference",
            "claim_type": "preferred-choice",
            "proposition": "Indonesian preference",
        },
        {
            "claim_id": "my-preference",
            "claim_type": "preferred-choice",
            "proposition": "Malaysian preference",
        },
        {"claim_id": "relation", "claim_type": "relation", "proposition": "Aligned concept"},
    ]
    observations = []
    for group in ("source-a", "source-b"):
        for claim in claims:
            observations.append(
                {
                    "evidence_id": f"{group}-{claim['claim_id']}",
                    "claim_id": claim["claim_id"],
                    "claim_type": claim["claim_type"],
                    "source_group": group,
                    "source_title": group,
                    "publisher": group,
                    "url_or_query": f"https://{group}.test/{claim['claim_id']}",
                    "accessed_at": "2026-10-03T00:00:00Z",
                    "observation": "Observed contextual use.",
                    "page_location_or_query": "entry and context",
                    "audit_method": "retrieved-page",
                    "usage_basis": "contextual",
                    "stance": "supports",
                    "locale": "Indonesia or Malaysia",
                }
            )
    stages = {
        "generate": {"candidates": [candidate]},
        "normalize-and-dedupe": {"overlaps": []},
        "indonesian-usage": {
            "meaning": "road passenger vehicle",
            "common_use": "common",
            "preferred": "everyday",
            "register": "neutral",
            "region": "Indonesia",
            "alternatives": [],
            "claims": claims[:1] + claims[2:3],
        },
        "malaysian-usage": {
            "meaning": "road passenger vehicle",
            "common_use": "common",
            "preferred": "everyday",
            "register": "neutral",
            "region": "Malaysia",
            "alternatives": [],
            "claims": claims[1:2] + claims[3:4],
        },
        "relation-proposal": {
            "english": "car",
            "relation": "different-common-word",
            "semantic_alignment": "same neutral sense",
            "aligned": True,
            "claims": [claims[4]],
        },
        "evidence-audit": {"observations": observations},
        "independent-verification": {
            "verdict": "agree",
            "relation": "different-common-word",
            "concerns": [],
            "rationale": "Audited evidence agrees",
        },
        "adversarial-review": {
            "verdict": "agree",
            "concerns": [],
            "rationale": "No counterexample found",
        },
    }
    return candidate, stages


def test_preaudit_withholds_different_common_word_without_locale_preference_claims():
    candidate, stages = candidate_and_stages()
    stages.pop("evidence-audit")
    stages.pop("independent-verification")
    stages.pop("adversarial-review")
    stages["indonesian-usage"]["claims"] = [
        claim
        for claim in stages["indonesian-usage"]["claims"]
        if claim["claim_type"] != "preferred-choice"
    ]
    stages["malaysian-usage"]["claims"] = [
        claim
        for claim in stages["malaysian-usage"]["claims"]
        if claim["claim_type"] != "preferred-choice"
    ]
    assert "missing-within-locale-preference" in preaudit_reasons(candidate, stages)


def test_preaudit_rejects_relation_label_inconsistent_with_written_forms():
    candidate, stages = candidate_and_stages()
    stages["relation-proposal"]["relation"] = "same"
    assert "relation-form-mismatch" in preaudit_reasons(candidate, stages)
    candidate["malaysian"] = "mobil"
    assert "relation-form-mismatch" not in preaudit_reasons(candidate, stages)
    stages["relation-proposal"]["relation"] = "similar"
    assert "relation-form-mismatch" in preaudit_reasons(candidate, stages)


def test_supported_candidate_passes_only_complete_independent_gate():
    candidate, stages = candidate_and_stages()
    assert decide_candidate(candidate, stages)["outcome"] == "accepted"
    del stages["independent-verification"]
    assert decide_candidate(candidate, stages)["outcome"] == "pending"


def test_v2_ordinary_fast_accepts_without_adversarial_review():
    candidate, stages = candidate_and_stages()
    del stages["adversarial-review"]
    decision = decide_candidate(candidate, stages, policy_version="2.0.0")
    assert decision["outcome"] == "accepted"
    assert decision["risk"] == {"path": "ordinary-fast", "triggers": []}
    assert decision["skipped_stages"] == {"adversarial-review": "skipped-low-risk"}


def test_neutral_prose_and_nonmaterial_verifier_limits_do_not_force_escalation():
    candidate, stages = candidate_and_stages()
    del stages["adversarial-review"]
    stages["indonesian-usage"]["register"] = "Neutral everyday vocabulary."
    stages["malaysian-usage"]["region"] = "No material regional restriction identified."
    stages["independent-verification"]["concerns"] = ["Frequency was not quantified."]
    stages["independent-verification"]["material_concerns"] = []
    decision = decide_candidate(candidate, stages, policy_version="2.0.0")
    assert decision["outcome"] == "accepted"
    assert decision["risk"]["path"] == "ordinary-fast"


def test_historical_concrete_adversarial_objection_remains_material():
    candidate, stages = candidate_and_stages()
    stages["adversarial-review"].update(
        verdict="object", concerns=["The alleged preferred form is actually regional."]
    )
    decision = decide_candidate(candidate, stages, policy_version="2.0.0")
    assert decision["outcome"] == "pending"
    assert "historical-adversarial-objection" in decision["risk"]["triggers"]
    assert "concrete-adversarial-objection" in decision["reason_codes"]


def test_v2_missing_evidence_and_verifier_hesitation_escalate_without_rejection():
    candidate, stages = candidate_and_stages()
    del stages["adversarial-review"]
    stages["evidence-audit"]["observations"] = []
    decision = decide_candidate(candidate, stages, policy_version="2.0.0")
    assert decision["outcome"] == "pending"
    assert "weak-evidence" in decision["risk"]["triggers"]
    candidate, stages = candidate_and_stages()
    del stages["adversarial-review"]
    stages["independent-verification"]["verdict"] = "object"
    decision = decide_candidate(candidate, stages, policy_version="2.0.0")
    assert decision["outcome"] == "pending"
    assert "verifier-disagreement" in decision["risk"]["triggers"]


def test_v2_contradiction_requires_escalation_and_cannot_be_accepted():
    candidate, stages = candidate_and_stages()
    stages["evidence-audit"]["observations"][0]["stance"] = "contradicts"
    decision = decide_candidate(candidate, stages, policy_version="2.0.0")
    assert decision["outcome"] == "pending"
    assert decision["risk"]["path"] == "escalated"
    assert "contradictory-evidence" in decision["reason_codes"]


def test_v2_explicit_hold_and_typed_reject_are_distinct():
    candidate, stages = candidate_and_stages()
    assert (
        decide_candidate(
            candidate,
            stages,
            policy_version="2.0.0",
            explicit_final={"outcome": "hold", "reason": "Source unavailable"},
        )["outcome"]
        == "hold"
    )
    with pytest.raises(ValueError, match="affirmative reason_code"):
        decide_candidate(
            candidate,
            stages,
            policy_version="2.0.0",
            explicit_final={"outcome": "rejected", "reason": "Search timed out"},
        )
    decision = decide_candidate(
        candidate,
        stages,
        policy_version="2.0.0",
        explicit_final={
            "outcome": "rejected",
            "reason": "Proven wrong sense",
            "reason_code": "confirmed-semantic-mismatch",
            "evidence_ref": "source-001",
        },
    )
    assert decision["outcome"] == "rejected"
    assert decision["evidence_ref"] == "source-001"


def test_v2_false_friend_still_requires_adversarial_agreement():
    candidate, stages = candidate_and_stages()
    stages["relation-proposal"]["relation"] = "false-friend"
    stages["independent-verification"]["relation"] = "false-friend"
    stages["relation-proposal"]["contrast"] = {
        "misleading_form": "kereta",
        "misleading_language": "indonesian",
        "actual_meaning": "train",
        "claim_ids": ["relation"],
    }
    del stages["adversarial-review"]
    decision = decide_candidate(candidate, stages, policy_version="2.0.0")
    assert decision["outcome"] == "pending"
    assert decision["risk"]["path"] == "false-friend"
    assert "missing-stage:adversarial-review" in decision["reason_codes"]


def test_two_mirrors_do_not_count_as_independent_evidence():
    candidate, stages = candidate_and_stages()
    for item in stages["evidence-audit"]["observations"]:
        item["source_group"] = "one-underlying-source"
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"


def test_different_group_labels_cannot_hide_shared_publisher_or_host():
    candidate, stages = candidate_and_stages()
    for item in stages["evidence-audit"]["observations"]:
        item["publisher"] = "Same Publisher"
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"


def test_relation_can_be_derived_from_audited_meaning_and_preference_on_both_sides():
    candidate, stages = candidate_and_stages()
    for claim in stages["indonesian-usage"]["claims"]:
        claim["locale"] = "Indonesia"
    for claim in stages["malaysian-usage"]["claims"]:
        claim["locale"] = "Malaysia"
    stages["evidence-audit"]["observations"] = [
        item
        for item in stages["evidence-audit"]["observations"]
        if item["claim_type"] != "relation"
    ]
    assert decide_candidate(candidate, stages)["outcome"] == "accepted"
    stages["evidence-audit"]["observations"] = [
        item
        for item in stages["evidence-audit"]["observations"]
        if item["claim_id"] != "my-preference"
    ]
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"
    candidate, stages = candidate_and_stages()
    for item in stages["evidence-audit"]["observations"]:
        item["url_or_query"] = "https://same.example.test/different-page"
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"


def test_same_relation_is_rejected_even_with_audited_meaning_and_usage():
    candidate, stages = candidate_and_stages()
    candidate["malaysian"] = "mobil"
    stages["relation-proposal"]["relation"] = "same"
    stages["independent-verification"]["relation"] = "same"
    for role, locale in (("indonesian-usage", "Indonesia"), ("malaysian-usage", "Malaysia")):
        meaning = stages[role]["claims"][0]
        meaning["locale"] = locale
        usage = {
            "claim_id": f"{role}-usage",
            "claim_type": "locale-usage",
            "locale": locale,
            "proposition": "Common contextual use",
        }
        stages[role]["claims"] = [meaning, usage]
        for group in ("source-a", "source-b"):
            stages["evidence-audit"]["observations"].append(
                {
                    "evidence_id": f"{group}-{role}-usage",
                    "claim_id": usage["claim_id"],
                    "claim_type": "locale-usage",
                    "source_group": group,
                    "source_title": group,
                    "publisher": group,
                    "url_or_query": f"https://{group}.test/usage",
                    "accessed_at": "2026-10-04T00:00:00Z",
                    "observation": "Observed contextual use",
                    "page_location_or_query": "usage paragraph",
                    "audit_method": "retrieved-page",
                    "usage_basis": "contextual",
                    "stance": "supports",
                }
            )
    stages["evidence-audit"]["observations"] = [
        item
        for item in stages["evidence-audit"]["observations"]
        if item["claim_type"] not in {"preferred-choice", "relation"}
    ]
    decision = decide_candidate(candidate, stages)
    assert decision["outcome"] == "rejected"
    assert "no-cross-language-difference" in decision["reason_codes"]


def test_shared_proposal_is_rejected_before_expensive_evidence_and_review():
    candidate, stages = candidate_and_stages()
    candidate["malaysian"] = "mobil"
    stages["relation-proposal"]["relation"] = "same"
    for role in ("evidence-audit", "independent-verification", "adversarial-review"):
        del stages[role]
    decision = decide_candidate(candidate, stages)
    assert decision["outcome"] == "rejected"
    assert decision["reason_codes"] == ["no-cross-language-difference"]
    assert decision["stage_statuses"]["evidence-audit"] == "missing"


def test_bare_audit_flag_or_dictionary_only_preference_cannot_pass():
    candidate, stages = candidate_and_stages()
    stages["evidence-audit"]["observations"][0].pop("page_location_or_query")
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"
    candidate, stages = candidate_and_stages()
    for item in stages["evidence-audit"]["observations"]:
        if item["claim_type"] == "preferred-choice":
            item["usage_basis"] = "dictionary-only"
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"


def test_dictionary_observation_does_not_veto_independent_contextual_preference():
    candidate, stages = candidate_and_stages()
    dictionary = deepcopy(stages["evidence-audit"]["observations"][0])
    dictionary.update(
        evidence_id="dictionary-id-preference",
        claim_id="id-preference",
        claim_type="preferred-choice",
        source_group="dictionary",
        source_title="Dictionary",
        publisher="Dictionary authority",
        url_or_query="https://dictionary.test/id-preference",
        usage_basis="dictionary-only",
    )
    stages["evidence-audit"]["observations"].append(dictionary)
    assert decide_candidate(candidate, stages)["outcome"] == "accepted"


def test_conflict_ambiguous_cue_and_model_score_do_not_override_gate():
    candidate, stages = candidate_and_stages()
    stages["evidence-audit"]["observations"][0]["stance"] = "contradicts"
    stages["independent-verification"]["self_confidence"] = 1.0
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"
    candidate, stages = candidate_and_stages()
    stages["relation-proposal"]["aligned"] = False
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"


def test_false_friend_requires_structured_contrast_and_stricter_claims():
    candidate, stages = candidate_and_stages()
    stages["relation-proposal"]["relation"] = "false-friend"
    stages["independent-verification"]["relation"] = "false-friend"
    assert decide_candidate(candidate, stages)["outcome"] != "accepted"
    stages["relation-proposal"]["contrast"] = {
        "misleading_form": "form",
        "misleading_language": "malaysian",
        "actual_meaning": "a different sense",
        "claim_ids": ["contrast"],
    }
    stages["relation-proposal"]["claims"].append(
        {"claim_id": "contrast", "claim_type": "misleading-contrast", "proposition": "Contrast"}
    )
    for group in ("source-a", "source-b"):
        item = deepcopy(
            next(
                observation
                for observation in stages["evidence-audit"]["observations"]
                if observation["source_group"] == group
            )
        )
        item.update(
            {
                "evidence_id": f"{group}-contrast",
                "claim_id": "contrast",
                "claim_type": "misleading-contrast",
                "source_group": group,
            }
        )
        stages["evidence-audit"]["observations"].append(item)
    assert decide_candidate(candidate, stages)["outcome"] == "accepted"
