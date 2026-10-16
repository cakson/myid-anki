import hashlib

import pytest
from scripts import benchmark_scaling_efficiency as replay

from indo_malay_anki.curation.store import atomic_json


def test_saved_replay_capture_resumes_without_model_call(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "OUT", tmp_path)
    prompt = "fixed historical candidate packet"
    capture = {
        "candidate_ids": ["candidate-1"],
        "prompt_bytes": len(prompt.encode()),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "response": {"result": {"overlaps": []}},
    }
    atomic_json(tmp_path / "captures" / "trial.json", capture)
    monkeypatch.setattr(
        replay,
        "call_model",
        lambda *_args, **_kwargs: pytest.fail("resume repeated a model call"),
    )
    assert replay._run("trial", "normalize-and-dedupe", prompt, ["candidate-1"]) == capture
    with pytest.raises(ValueError, match="stale replay prompt"):
        replay._run("trial", "normalize-and-dedupe", prompt + " changed", ["candidate-1"])
    with pytest.raises(ValueError, match="stale replay capture"):
        replay._run("trial", "normalize-and-dedupe", prompt, ["candidate-2"])
