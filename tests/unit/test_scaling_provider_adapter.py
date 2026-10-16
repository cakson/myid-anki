from __future__ import annotations

from indo_malay_anki.scaling.workflow import _envelope_response


def test_prompt_native_generation_result_is_wrapped_for_feature003_ingest():
    answer = {
        "model": "fixture",
        "response": {"type": "generate", "version": "2.4.0", "candidates": [{"candidate_id": "a"}]},
    }
    assert _envelope_response("generate", answer) == {
        "schema_version": 1,
        "role": "generate",
        "model": "fixture",
        "result": {"candidates": [{"candidate_id": "a"}]},
    }
