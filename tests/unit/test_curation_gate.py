"""Seeded process gates; these fixtures do not assert linguistic truth."""

from copy import deepcopy

from indo_malay_anki.curation.gate import decide_candidate, preaudit_reasons


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
