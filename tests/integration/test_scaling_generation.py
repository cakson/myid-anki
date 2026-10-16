from __future__ import annotations

from indo_malay_anki.scaling.coverage import approve_allocation, inventory
from indo_malay_anki.scaling.store import RunStore
from indo_malay_anki.scaling.workflow import generate_run


def _provider_factory():
    calls = []

    def provider(root, role, prompt):
        import json

        assert role == "generate"
        request = json.loads(prompt.split("SCALING_REQUEST_JSON\n", 1)[1])
        priorities = request["instruction"]
        assert priorities.index("different-common-word") < priorities.index("similar")
        assert priorities.index("similar") < priorities.index("false-friend")
        calls.append(request)
        category = request["category"]
        count = request["count"]
        ordinal = len(calls)
        candidates = [
            {
                "candidate_id": f"candidate-{ordinal:02d}-{i:02d}",
                "english": f"concept {ordinal:02d} {i:02d}",
                "indonesian": f"id{ordinal:02d}{i:02d}",
                "malaysian": f"ms{ordinal:02d}{i:02d}",
                "sense": f"distinct common concept {ordinal:02d} {i:02d}",
                "tags": [category],
            }
            for i in range(count)
        ]
        return {
            "response": {
                "schema_version": 1,
                "role": "generate",
                "model": "fixture",
                "result": {"candidates": candidates},
            },
            "model": "fixture",
            "elapsed_ms": 1,
            "input_tokens": 10,
            "output_tokens": 10,
            "model_calls": 1,
            "retrievals": 0,
        }

    return calls, provider


def test_exactly_100_across_bounded_slices_and_resume(tmp_path):
    store = RunStore(tmp_path, "hundred")
    store.create(requested_count=100, proposal_cap=120, baseline_count=0)
    snapshot = inventory(tmp_path)
    counts = {key: 0 for key in snapshot["counts"]}
    counts["common-verbs"] = 100
    approve_allocation(store, counts, snapshot, reason="fixture")
    calls, provider = _provider_factory()
    result = generate_run(store, provider=provider)
    assert result["admitted_count"] == 100
    assert len(result["slices"]) == 9
    assert all(item["requested"] <= 12 for item in result["slices"])
    assert generate_run(store, provider=provider)["admitted_count"] == 100
    assert len(calls) == 9


def test_screened_out_proposal_does_not_consume_slot(repo_factory):
    root = repo_factory()
    store = RunStore(root, "small")
    store.create(requested_count=1, proposal_cap=3, baseline_count=1)
    snapshot = inventory(root)
    counts = {key: 0 for key in snapshot["counts"]}
    counts["transportation"] = 1
    approve_allocation(store, counts, snapshot, reason="fixture")
    calls, provider = _provider_factory()

    def first_duplicate(root, role, prompt):
        if not calls:
            calls.append("duplicate")
            return {
                "response": {
                    "schema_version": 1,
                    "role": "generate",
                    "model": "fixture",
                    "result": {
                        "candidates": [
                            {
                                "candidate_id": "car-copy",
                                "english": "car",
                                "indonesian": "mobil",
                                "malaysian": "kereta",
                                "sense": "road vehicle",
                                "tags": ["transportation"],
                            }
                        ]
                    },
                },
                "model": "fixture",
                "elapsed_ms": 1,
                "input_tokens": 10,
                "output_tokens": 10,
                "model_calls": 1,
                "retrievals": 0,
            }
        return provider(root, role, prompt)

    result = generate_run(store, provider=first_duplicate)
    assert result["admitted_count"] == 1
    assert result["screened_out_count"] == 1
    assert result["slices"][0]["admitted"] == 0
    assert result["slices"][0]["candidate_ids"] == []
    assert len(result["slices"]) == 2
    assert not (
        root / "curation" / "batches" / result["slices"][0]["slice_id"] / "report.json"
    ).exists()


def test_proposal_cap_pauses_without_padding(repo_factory):
    import pytest

    from indo_malay_anki.scaling.store import RunError

    root = repo_factory()
    store = RunStore(root, "cap")
    store.create(requested_count=1, proposal_cap=1, baseline_count=1)
    snapshot = inventory(root)
    counts = {key: 0 for key in snapshot["counts"]}
    counts["transportation"] = 1
    approve_allocation(store, counts, snapshot, reason="fixture")

    def duplicate(_root, _role, _prompt):
        return {
            "response": {
                "schema_version": 1,
                "role": "generate",
                "model": "fixture",
                "result": {
                    "candidates": [
                        {
                            "candidate_id": "car-copy",
                            "english": "car",
                            "indonesian": "mobil",
                            "malaysian": "kereta",
                            "sense": "road vehicle",
                            "tags": ["transportation"],
                        }
                    ]
                },
            },
            "model": "fixture",
            "elapsed_ms": 1,
        }

    with pytest.raises(RunError, match="proposal cap reached"):
        generate_run(store, provider=duplicate)
    assert store.load()["state"] == "paused"
    assert store.load()["admitted_count"] == 0


def test_resume_after_slice_ingest_before_parent_manifest(tmp_path, monkeypatch):
    store = RunStore(tmp_path, "interrupted")
    store.create(requested_count=1, proposal_cap=2, baseline_count=0)
    snapshot = inventory(tmp_path)
    counts = {key: 0 for key in snapshot["counts"]}
    counts["common-verbs"] = 1
    approve_allocation(store, counts, snapshot, reason="fixture")
    calls, provider = _provider_factory()
    original_save = store.save
    failed = False

    def interrupted_save(manifest, **kwargs):
        nonlocal failed
        if not failed and manifest.get("admitted_count") == 1:
            failed = True
            raise OSError("interrupted after Feature 003 ingest")
        return original_save(manifest, **kwargs)

    monkeypatch.setattr(store, "save", interrupted_save)
    import pytest

    with pytest.raises(OSError, match="interrupted"):
        generate_run(store, provider=provider)
    monkeypatch.setattr(store, "save", original_save)
    result = generate_run(store, provider=provider)
    assert result["admitted_count"] == 1
    assert len(calls) == 1


def test_malformed_generation_capture_is_retained_but_retryable(tmp_path):
    import pytest

    store = RunStore(tmp_path, "malformed")
    store.create(requested_count=1, proposal_cap=2, baseline_count=0)
    snapshot = inventory(tmp_path)
    counts = {key: 0 for key in snapshot["counts"]}
    counts["common-verbs"] = 1
    approve_allocation(store, counts, snapshot, reason="fixture")
    calls, valid_provider = _provider_factory()

    def malformed(*_args):
        return {
            "response": {
                "schema_version": 1,
                "role": "generate",
                "model": "fixture",
                "result": {"candidates": []},
            },
            "model": "fixture",
        }

    with pytest.raises(ValueError, match="returned 0 proposals"):
        generate_run(store, provider=malformed)
    assert len(list((store.path / "generation-responses" / "failed").glob("*.json"))) == 1
    result = generate_run(store, provider=valid_provider)
    assert result["admitted_count"] == 1
    assert len(calls) == 1


def test_cross_slice_duplicate_is_screened_then_replaced(tmp_path):
    store = RunStore(tmp_path, "cross-slice")
    store.create(requested_count=13, proposal_cap=20, baseline_count=0)
    snapshot = inventory(tmp_path)
    counts = {key: 0 for key in snapshot["counts"]}
    counts["common-verbs"] = 13
    approve_allocation(store, counts, snapshot, reason="fixture")
    calls, normal = _provider_factory()

    def provider(root, role, prompt):
        if len(calls) == 1:
            calls.append("duplicate")
            return {
                "response": {
                    "candidates": [
                        {
                            "candidate_id": "repeated-across-slices",
                            "english": "concept 01 00",
                            "indonesian": "id0100",
                            "malaysian": "ms0100",
                            "sense": "distinct common concept 01 00",
                            "tags": ["common-verbs"],
                        }
                    ]
                },
                "model": "fixture",
                "elapsed_ms": 1,
            }
        return normal(root, role, prompt)

    result = generate_run(store, provider=provider)
    assert result["admitted_count"] == 13
    assert result["proposed_count"] == 14
    assert result["slices"][1]["admitted"] == 0
    assert result["slices"][1]["screened"][0]["reason"] == "duplicate"
    assert len(result["slices"]) == 3
