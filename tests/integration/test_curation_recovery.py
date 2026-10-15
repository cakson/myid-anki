"""Interrupted and corrected curation remains auditable and outside learner source."""

import json

import pytest

from indo_malay_anki.curation.records import RecordError
from indo_malay_anki.curation.report import batch_report
from indo_malay_anki.curation.workflow import (
    current_results,
    finalize_hold,
    finalize_reject,
    ingest_response,
    init_batch,
    reopen_candidate,
    revise_candidate,
)


def response(role, result):
    return json.dumps({"schema_version": 1, "role": role, "model": "fixture", "result": result})


def test_v2_preserves_candidate_identity_and_compatible_stage_after_failed_retry(tmp_path):
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir(exist_ok=True)
    config.write_text(
        '{"prompt_set_version":"1.1.0","decision_policy_version":"2.0.0"}',
        encoding="utf-8",
    )
    store = init_batch(tmp_path, "migration-001", "home", 1)
    candidate = {
        "candidate_id": "bathroom-01",
        "english": "bathroom",
        "indonesian": "kamar mandi",
        "malaysian": "bilik air",
        "sense": "room for bathing",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [candidate]}))
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "bathroom-01",
    )
    with pytest.raises(RecordError, match="malformed"):
        ingest_response(store, "normalize-and-dedupe", "{broken", "bathroom-01")
    assert store.candidate_ids() == ("bathroom-01",)
    assert "normalize-and-dedupe" in current_results(store, "bathroom-01")
    assert store.manifest().decision_policy_version == "2.0.0"
    assert any(event["status"] == "failed" for event in store.events("bathroom-01"))


@pytest.fixture(autouse=True)
def prior_prompt_version(tmp_path):
    """Recovery fixtures exercise their original packet protocol without source preflight."""
    config = tmp_path / "curation" / "config.json"
    config.parent.mkdir()
    config.write_text('{"prompt_set_version":"1.1.0"}', encoding="utf-8")


def test_hold_reopen_revision_invalidates_only_dependent_results(tmp_path):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text("unchanged\n", encoding="utf-8")
    store = init_batch(tmp_path, "home-001", "home", 1)
    candidate = {
        "candidate_id": "bathroom-01",
        "english": "bathroom",
        "indonesian": "kamar mandi",
        "malaysian": "bilik air",
        "sense": "room for bathing",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [candidate]}))
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "bathroom-01",
    )
    assert set(current_results(store, "bathroom-01")) == {"generate", "normalize-and-dedupe"}
    finalize_hold(store, "bathroom-01", "English cue needs disambiguation")
    assert batch_report(store)["status"] == "closed"
    assert source.read_text(encoding="utf-8") == "unchanged\n"
    reopen_candidate(store, "bathroom-01", "Correct the English cue")
    assert store.manifest().status == "open"
    revised = revise_candidate(
        store, "bathroom-01", {"english": "bathroom (for bathing)"}, "Disambiguate cue"
    )
    assert revised["english"] == "bathroom (for bathing)"
    assert set(current_results(store, "bathroom-01")) == {"generate"}
    assert any(event["role"] == "normalize-and-dedupe" for event in store.events("bathroom-01"))
    assert store.candidate("bathroom-01")["english"] == "bathroom (for bathing)"
    report = batch_report(store)
    assert report["status"] == "open" and report["pending"] == 1
    assert report["corrections"] >= 2
    assert source.read_text(encoding="utf-8") == "unchanged\n"


def test_tag_revision_replaces_placeholder_and_invalidates_normalization(tmp_path):
    store = init_batch(tmp_path, "school-001", "school", 1)
    ingest_response(
        store,
        "generate",
        response(
            "generate",
            {
                "candidates": [
                    {
                        "candidate_id": "pencil-01",
                        "english": "pencil",
                        "indonesian": "pensil",
                        "malaysian": "pensel",
                        "sense": "writing instrument",
                        "tags": ["topic"],
                    }
                ]
            },
        ),
    )
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "pencil-01",
    )
    revised = revise_candidate(
        store, "pencil-01", {"tags": ["school"]}, "Replace placeholder topic tag"
    )
    assert revised["tags"] == ["school"]
    assert set(current_results(store, "pencil-01")) == {"generate"}


def test_explicit_rejection_records_reason_without_inventing_review_stages(tmp_path):
    store = init_batch(tmp_path, "school-001", "school", 1)
    ingest_response(
        store,
        "generate",
        response(
            "generate",
            {
                "candidates": [
                    {
                        "candidate_id": "school-01",
                        "english": "school",
                        "indonesian": "sekolah",
                        "malaysian": "sekolah",
                        "sense": "educational institution",
                    }
                ]
            },
        ),
    )
    decision = finalize_reject(
        store, "school-01", "No demonstrated cross-language vocabulary contrast"
    )
    assert decision["outcome"] == "rejected"
    assert decision["decision_reason"] == "No demonstrated cross-language vocabulary contrast"
    assert decision["stage_statuses"]["independent-verification"] == "missing"


def test_later_batch_does_not_invalidate_prior_archive_snapshot(tmp_path):
    first = init_batch(tmp_path, "home-001", "home", 1)
    candidate = {
        "candidate_id": "room-01",
        "english": "room",
        "indonesian": "ruang",
        "malaysian": "bilik",
        "sense": "a space inside a building",
    }
    ingest_response(first, "generate", response("generate", {"candidates": [candidate]}))
    ingest_response(
        first,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "room-01",
    )
    assert "normalize-and-dedupe" in current_results(first, "room-01")
    later = init_batch(tmp_path, "food-001", "food", 1)
    ingest_response(
        later,
        "generate",
        response(
            "generate",
            {
                "candidates": [
                    {
                        "candidate_id": "food-01",
                        "english": "food",
                        "indonesian": "makanan",
                        "malaysian": "makanan",
                        "sense": "something eaten",
                    }
                ]
            },
        ),
    )
    assert "normalize-and-dedupe" in current_results(first, "room-01")


def test_malformed_role_output_stays_pending_and_can_be_retried(tmp_path):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text("unchanged\n", encoding="utf-8")
    store = init_batch(tmp_path, "home-001", "home", 1)
    candidate = {
        "candidate_id": "room-01",
        "english": "room",
        "indonesian": "ruang",
        "malaysian": "bilik",
        "sense": "space inside a building",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [candidate]}))
    with pytest.raises(RecordError, match="malformed"):
        ingest_response(store, "normalize-and-dedupe", "not JSON", "room-01")
    failed = store.events("room-01")[-1]
    assert failed["status"] == "failed" and failed["raw_response"] == "not JSON"
    assert batch_report(store)["status"] == "open"
    assert source.read_text(encoding="utf-8") == "unchanged\n"
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "room-01",
    )
    assert "normalize-and-dedupe" in current_results(store, "room-01")


def test_prompt_edit_invalidates_only_its_stage_and_downstream(tmp_path):
    prompts = tmp_path / "curation" / "prompts" / "versions" / "1.1.0"
    prompts.mkdir(parents=True)
    (prompts / "manifest.json").write_text(
        json.dumps(
            {
                "prompt_set_version": "1.1.0",
                "roles": {
                    "generate": {"prompt": "generate.md"},
                    "normalize-and-dedupe": {"prompt": "overlap.md"},
                },
            }
        ),
        encoding="utf-8",
    )
    (prompts / "generate.md").write_text("Generate one candidate", encoding="utf-8")
    overlap_prompt = prompts / "overlap.md"
    overlap_prompt.write_text("Check overlap", encoding="utf-8")
    store = init_batch(tmp_path, "home-001", "home", 1)
    candidate = {
        "candidate_id": "room-01",
        "english": "room",
        "indonesian": "ruang",
        "malaysian": "bilik",
        "sense": "space inside a building",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [candidate]}))
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "room-01",
    )
    assert set(current_results(store, "room-01")) == {"generate", "normalize-and-dedupe"}
    overlap_prompt.write_text("Check overlap with revised instructions", encoding="utf-8")
    assert set(current_results(store, "room-01")) == {"generate"}
    assert batch_report(store)["status"] == "open"


def test_replaying_identical_stage_is_idempotent_and_changed_generation_is_refused(tmp_path):
    store = init_batch(tmp_path, "home-001", "home", 1)
    candidate = {
        "candidate_id": "room-01",
        "english": "room",
        "indonesian": "ruang",
        "malaysian": "bilik",
        "sense": "space inside a building",
    }
    generation = response("generate", {"candidates": [candidate]})
    first_generation = ingest_response(store, "generate", generation)
    assert ingest_response(store, "generate", generation) == first_generation
    assert len(store.batch_events()) == 1
    overlap = response("normalize-and-dedupe", {"overlaps": []})
    first_overlap = ingest_response(store, "normalize-and-dedupe", overlap, "room-01")
    assert ingest_response(store, "normalize-and-dedupe", overlap, "room-01") == first_overlap
    assert len(store.events("room-01")) == 1
    changed = response("generate", {"candidates": [{**candidate, "english": "chamber"}]})
    with pytest.raises(RecordError, match="changes candidate content"):
        ingest_response(store, "generate", changed)
    assert store.candidate("room-01") == candidate


@pytest.mark.parametrize(
    ("field", "value"),
    [("english", "room (inside a building)"), ("indonesian", "kamar")],
)
def test_material_cue_or_answer_edit_invalidates_prior_overlap(tmp_path, field, value):
    store = init_batch(tmp_path, "home-001", "home", 1)
    candidate = {
        "candidate_id": "room-01",
        "english": "room",
        "indonesian": "ruang",
        "malaysian": "bilik",
        "sense": "space inside a building",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [candidate]}))
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "room-01",
    )
    revise_candidate(store, "room-01", {field: value}, "Clarify proposal")
    assert set(current_results(store, "room-01")) == {"generate"}
    assert store.candidate("room-01")[field] == value
    assert batch_report(store)["pending"] == 1


def test_zero_acceptance_batch_closes_with_reconciled_hold_and_reject(tmp_path):
    source = tmp_path / "data" / "vocabulary.tsv"
    source.parent.mkdir()
    source.write_text("unchanged\n", encoding="utf-8")
    store = init_batch(tmp_path, "audit-001", "audit", 2)
    candidates = [
        {
            "candidate_id": f"item-0{number}",
            "english": cue,
            "indonesian": answer,
            "malaysian": answer,
            "sense": cue,
        }
        for number, (cue, answer) in enumerate((("room", "ruang"), ("rooms", "ruang")), start=1)
    ]
    ingest_response(store, "generate", response("generate", {"candidates": candidates}))
    initial = batch_report(store)
    assert initial["status"] == "open" and initial["pending"] == 2
    finalize_hold(store, "item-01", "Evidence unavailable")
    ingest_response(
        store,
        "normalize-and-dedupe",
        response(
            "normalize-and-dedupe",
            {
                "overlaps": [
                    {
                        "other_id": "audit-001:item-01",
                        "type": "semantic",
                        "resolution": "reject",
                        "rationale": "Plural form of the same room concept",
                    }
                ]
            },
        ),
        "item-02",
    )
    closed = batch_report(store)
    assert closed["status"] == "closed"
    assert (
        closed["generated"],
        closed["accepted"],
        closed["held"],
        closed["rejected"],
        closed["pending"],
    ) == (2, 0, 1, 1, 0)
    assert closed["reason_code_distribution"]["confirmed-duplicate"] == 1
    assert source.read_text(encoding="utf-8") == "unchanged\n"


def completed_similar_concept(store):
    candidate = {
        "candidate_id": "house-01",
        "english": "sauce",
        "indonesian": "saus",
        "malaysian": "sos",
        "sense": "condiment served with food",
    }
    ingest_response(store, "generate", response("generate", {"candidates": [candidate]}))
    ingest_response(
        store,
        "normalize-and-dedupe",
        response("normalize-and-dedupe", {"overlaps": []}),
        "house-01",
    )
    for role, locale in (("indonesian-usage", "Indonesia"), ("malaysian-usage", "Malaysia")):
        ingest_response(
            store,
            role,
            response(
                role,
                {
                    "meaning": "condiment served with food",
                    "common_use": "common",
                    "preferred": "everyday",
                    "register": "neutral",
                    "region": locale,
                    "alternatives": [],
                    "claims": [
                        {
                            "claim_id": "meaning",
                            "claim_type": "meaning",
                            "locale": locale,
                            "proposition": "The proposed form denotes sauce",
                        }
                    ],
                },
            ),
            "house-01",
        )
    relation = {
        "english": "sauce",
        "relation": "similar",
        "semantic_alignment": "one condiment sense",
        "aligned": True,
        "claims": [
            {"claim_id": "relation", "claim_type": "relation", "proposition": "Similar forms"}
        ],
    }
    ingest_response(store, "relation-proposal", response("relation-proposal", relation), "house-01")
    observations = [
        {
            "evidence_id": f"{group}-{role}",
            "claim_id": f"{role}:meaning" if role != "relation-proposal" else f"{role}:relation",
            "source_group": group,
            "source_title": f"{group} sauce usage",
            "publisher": group,
            "url_or_query": f"https://{group}.test/sauce",
            "accessed_at": "2026-10-04T00:00:00Z",
            "observation": "Sauce sense observed",
            "page_location_or_query": "sauce entry",
            "audit_method": "retrieved-page",
            "stance": "supports",
            "claim_type": "meaning" if role != "relation-proposal" else "relation",
        }
        for group in ("source-a", "source-b")
        for role in ("indonesian-usage", "malaysian-usage", "relation-proposal")
    ]
    ingest_response(
        store,
        "evidence-audit",
        response("evidence-audit", {"observations": observations}),
        "house-01",
    )
    ingest_response(
        store,
        "independent-verification",
        response(
            "independent-verification",
            {"verdict": "agree", "relation": "similar", "concerns": [], "rationale": "Aligned"},
        ),
        "house-01",
    )
    ingest_response(
        store,
        "adversarial-review",
        response(
            "adversarial-review",
            {"verdict": "agree", "concerns": [], "rationale": "No objection"},
        ),
        "house-01",
    )
    return relation, observations


@pytest.mark.parametrize("changed_role", ["relation-proposal", "evidence-audit"])
def test_relation_or_evidence_revision_invalidates_prior_review(tmp_path, changed_role):
    store = init_batch(tmp_path, "home-001", "home", 1)
    relation, observations = completed_similar_concept(store)
    assert "adversarial-review" in current_results(store, "house-01")
    if changed_role == "relation-proposal":
        changed = {**relation, "semantic_alignment": "rechecked condiment sense"}
        ingest_response(store, changed_role, response(changed_role, changed), "house-01")
        expected = {
            "generate",
            "normalize-and-dedupe",
            "indonesian-usage",
            "malaysian-usage",
            "relation-proposal",
            "evidence-audit",
        }
    else:
        changed = [dict(item) for item in observations]
        changed[0]["observation"] = "Sauce sense observed in a revised source inspection"
        ingest_response(
            store, changed_role, response(changed_role, {"observations": changed}), "house-01"
        )
        expected = {
            "generate",
            "normalize-and-dedupe",
            "indonesian-usage",
            "malaysian-usage",
            "relation-proposal",
            "evidence-audit",
        }
    assert set(current_results(store, "house-01")) == expected
    assert batch_report(store)["pending"] == 1
