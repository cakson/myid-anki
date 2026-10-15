"""The frozen historical experiment replays decisions without touching archived curation."""

import hashlib
import json
from pathlib import Path

from scripts.historical_hold_experiment import run

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "specs/003-vocabulary-curation/historical-hold-sample.json"


def _archive_digests():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "curation/batches").rglob("*.json")
    }


def test_replay_is_bounded_read_only_and_keeps_old_hold_identity():
    before = _archive_digests()
    result = run(ROOT, SAMPLE)
    assert result["sample_size"] == 26
    assert result["original_distribution"] == {"accepted": 0, "hold": 26, "rejected": 0}
    assert result["new_distribution"] == {"accepted": 0, "hold": 25, "rejected": 1}
    assert len({row["candidate_ref"] for row in result["rows"]}) == 26
    assert result["new_evidence_retrievals"] == 0
    assert before == _archive_digests()


def test_model_comparison_keeps_matched_input_and_luna_route():
    comparison = json.loads(
        (ROOT / "specs/003-vocabulary-curation/historical-model-comparison.json").read_text()
    )
    completed = [row for row in comparison["results"] if row["status"] == "complete"]
    assert len(completed) == 10
    for ref in comparison["candidate_refs"]:
        paired = [row for row in completed if row["candidate_ref"] == ref]
        assert {row["model"] for row in paired} == {"gpt-5.6-luna", "gpt-5.6-sol"}
        assert len({row["prompt_digest"] for row in paired}) == 1
    config = json.loads((ROOT / "curation/config.json").read_text())
    assert {route["model"] for route in config["role_models"].values()} == {"gpt-5.6-luna"}
