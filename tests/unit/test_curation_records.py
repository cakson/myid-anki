"""Foundational curation schema and persistence checks."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from indo_malay_anki.curation.packets import make_packet
from indo_malay_anki.curation.records import (
    BatchManifest,
    RecordError,
    validate_audit_observation,
    validate_candidate,
    validate_operation_event,
    validate_stage_response,
)
from indo_malay_anki.curation.store import BatchStore


def manifest(**changes):
    source = BatchManifest(
        "transport-001", "transport", "Everyday travel", 12, "1.0.0", "2026-10-03T00:00:00Z"
    )
    return replace(source, **changes)


def test_manifest_rejects_unsafe_id_and_unbounded_candidates():
    for changes in ({"batch_id": "../escape"}, {"candidate_limit": 13}, {"candidate_limit": 0}):
        with pytest.raises(RecordError):
            BatchManifest.from_dict(manifest(**changes).as_dict())


def test_generation_requires_structured_candidate_without_permanent_id():
    candidate = {
        "candidate_id": "car-01",
        "english": "car",
        "indonesian": "mobil",
        "malaysian": "kereta",
        "sense": "road passenger vehicle",
    }
    response = {
        "schema_version": 1,
        "role": "generate",
        "model": "tool-a",
        "result": {"candidates": [candidate]},
    }
    assert (
        validate_stage_response("generate", response, limit=1)["result"]["candidates"][0][
            "candidate_id"
        ]
        == "car-01"
    )
    with pytest.raises(RecordError):
        validate_stage_response("generate", response, limit=0)
    with pytest.raises(RecordError):
        validate_candidate({**candidate, "id": "000001"})
    with pytest.raises(RecordError):
        validate_stage_response("indonesian-usage", response)


def test_structured_verifier_fields_are_atomic_and_validate_routing_values():
    result = {
        "verdict": "agree",
        "relation": "similar",
        "concerns": [],
        "material_concerns": [],
        "objection_assessments": [],
        "rationale": "The spelling difference is useful.",
        "cue_alignment": "aligned",
        "cue_rewrite": "",
        "cue_rationale": "Both answers denote the same food.",
        "shared_synonym_case": "none",
        "shared_synonym_rationale": "none",
        "nonblocking_risk": "none",
        "risk_rationale": "",
    }
    envelope = {
        "schema_version": 1,
        "role": "independent-verification",
        "model": "tool-a",
        "result": result,
    }
    assert validate_stage_response("independent-verification", envelope)["result"] == result
    with pytest.raises(RecordError, match="complete"):
        validate_stage_response(
            "independent-verification",
            {**envelope, "result": {k: v for k, v in result.items() if k != "cue_rationale"}},
        )
    with pytest.raises(RecordError, match="shared_synonym_case"):
        validate_stage_response(
            "independent-verification",
            {**envelope, "result": {**result, "shared_synonym_case": "unknown"}},
        )
    credible = {
        "status": "credible-everyday",
        "form": "kereta",
        "language": "indonesian",
        "same_sense": True,
        "rationale": "This form may be an everyday competitor.",
    }
    assert (
        validate_stage_response(
            "independent-verification",
            {**envelope, "result": {**result, "competing_form": credible}},
        )["result"]["competing_form"]
        == credible
    )
    with pytest.raises(RecordError, match="named same-sense"):
        validate_stage_response(
            "independent-verification",
            {**envelope, "result": {**result, "competing_form": {**credible, "form": ""}}},
        )


def test_competing_form_challenge_requires_explicit_outcome_and_assessment():
    challenge = {
        "outcome": "contrast-remains-useful",
        "assessment": {
            "normal_everyday_same_sense": True,
            "materially_weakens_preference": False,
            "useful_difference_remains": True,
            "unqualified_card_misleads": False,
        },
        "rationale": "The proposed preference remains useful.",
        "cue_rewrite": "",
        "usage_note": "",
        "support": [],
    }
    envelope = {
        "schema_version": 1,
        "role": "competing-form-challenge",
        "model": "tool-a",
        "result": challenge,
    }
    assert validate_stage_response("competing-form-challenge", envelope)["result"] == challenge
    with pytest.raises(RecordError, match="qualification"):
        validate_stage_response(
            "competing-form-challenge",
            {**envelope, "result": {**challenge, "outcome": "contrast-needs-qualification"}},
        )


def test_competing_form_packet_excludes_optimistic_verifier_conclusion(tmp_path):
    batch = manifest(prompt_set_version="2.3.0", decision_policy_version="3.2.0")
    candidate = {
        "candidate_id": "car-01",
        "english": "car",
        "indonesian": "mobil",
        "malaysian": "kereta",
        "sense": "passenger vehicle",
    }
    stages = {
        "independent-verification": {
            "relation": "different-common-word",
            "rationale": "Optimistic preference conclusion that should not reach the challenger.",
            "competing_form": {
                "status": "credible-everyday",
                "form": "mobil",
                "language": "malaysian",
                "same_sense": True,
                "rationale": "The term may be ordinary in Malaysia.",
            },
        }
    }
    packet = make_packet(
        tmp_path, batch, "competing-form-challenge", candidate=candidate, stages=stages
    )
    assert packet["context"]["named_competing_form"]["form"] == "mobil"
    assert "verifier_rationale" not in packet["context"]


def test_audit_observation_requires_source_group_method_and_location():
    observation = {
        "evidence_id": "e1",
        "claim_id": "c1",
        "source_group": "kbbi",
        "source_title": "KBBI",
        "publisher": "Badan Bahasa",
        "url_or_query": "https://example.test",
        "accessed_at": "2026-10-03T00:00:00Z",
        "observation": "The page labels the sense as common.",
        "page_location_or_query": "entry: mobil",
        "audit_method": "retrieved-page",
        "stance": "supports",
        "claim_type": "meaning",
    }
    assert validate_audit_observation(observation)["source_group"] == "kbbi"
    for key in ("source_group", "page_location_or_query", "audit_method"):
        with pytest.raises(RecordError):
            validate_audit_observation({k: v for k, v in observation.items() if k != key})
    with pytest.raises(RecordError, match="one underlying source"):
        validate_audit_observation({**observation, "source_group": "source-a + source-b"})
    with pytest.raises(RecordError, match="one source"):
        validate_audit_observation(
            {**observation, "url_or_query": "https://a.test/page | https://b.test/page"}
        )


def test_store_preserves_events_and_reloads_after_interruption(tmp_path):
    store = BatchStore(tmp_path, "transport-001")
    store.create(manifest())
    store.save_candidate("car-01", {"candidate_id": "car-01", "english": "car"})
    store.append_event("car-01", {"role": "generate", "status": "complete"})
    store.append_event("car-01", {"role": "indonesian-usage", "status": "interrupted"})
    reloaded = BatchStore(tmp_path, "transport-001")
    assert reloaded.manifest() == manifest()
    assert reloaded.candidate_ids() == ("car-01",)
    assert [event["status"] for event in reloaded.events("car-01")] == ["complete", "interrupted"]
    with pytest.raises(RecordError):
        reloaded.create(manifest())


def test_concurrent_stage_appends_keep_every_revision(tmp_path):
    store = BatchStore(tmp_path, "transport-001")
    store.create(manifest())
    store.save_candidate("car-01", {"candidate_id": "car-01"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(
            pool.map(
                lambda number: store.append_event("car-01", {"number": number}),
                range(40),
            )
        )
    assert {event["number"] for event in store.events("car-01")} == set(range(40))


def test_operation_attempts_are_append_only_and_old_manifests_remain_compatible(tmp_path):
    store = BatchStore(tmp_path, "transport-001")
    store.create(manifest())
    assert "decision_policy_version" not in store.manifest().as_dict()
    started = {
        "operation_id": "call-001",
        "kind": "model",
        "status": "started",
        "candidate_ids": ["car-01"],
        "at": "2026-10-13T00:00:00Z",
    }
    store.append_operation_event(started)
    store.append_operation_event(
        {
            **started,
            "status": "failed",
            "elapsed_ms": 9,
            "usage_unavailable_reason": "provider omitted usage",
        }
    )
    assert [event["status"] for event in store.operation_events()] == ["started", "failed"]
    with pytest.raises(RecordError, match="usage_unavailable_reason"):
        validate_operation_event({**started, "status": "complete", "elapsed_ms": 9})
