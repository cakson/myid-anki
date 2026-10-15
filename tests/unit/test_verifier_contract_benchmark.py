import json

import pytest
from scripts.benchmark_verifier_contract import model_prompt, validate_items


def test_model_prompt_exposes_only_candidate_fields():
    item = {
        "candidate_ref": "fixed-01",
        "candidate": {"english": "socks", "indonesian": "kaus kaki", "malaysian": "stoking"},
        "audit_verdict": "materially-misleading",
        "post_audit_correction": "stokin",
        "production_verifier": {"verdict": "agree"},
    }
    payload = model_prompt([item])
    visible = json.loads(payload.split("Evaluate exactly these candidates:\n", 1)[1])
    assert visible == [{"candidate_ref": "fixed-01", "candidate": item["candidate"]}]


def test_structured_result_rejects_missing_candidate_or_invalid_action():
    row = {
        "semantic_alignment": "clear",
        "answer_precision": {"indonesian": "natural", "malaysian": "questionable"},
        "everyday_contrast": "uncertain",
        "concrete_objection": "The Malaysian form may mean stockings.",
        "action": "ACCEPT_WITH_REVIEW",
        "reason": "The proposed form needs a precision check.",
    }
    assert validate_items({"items": {"fixed-01": row}}, {"fixed-01"})["fixed-01"] == row
    with pytest.raises(ValueError, match="candidate refs"):
        validate_items({"items": {"fixed-01": row}}, {"fixed-02"})
    with pytest.raises(ValueError, match="action"):
        validate_items({"items": {"fixed-01": {**row, "action": "MAYBE"}}}, {"fixed-01"})
