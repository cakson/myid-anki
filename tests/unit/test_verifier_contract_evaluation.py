from scripts.evaluate_verifier_contract import score


def test_review_and_random_audit_have_separate_safety_effects():
    labels = {
        "unsafe-review": {"critical": True, "audit_verdict": "should-hold"},
        "unsafe-ordinary": {"critical": True, "audit_verdict": "materially-misleading"},
        "safe-review": {"critical": False, "audit_verdict": "confirmed-good"},
        "minor": {"critical": False, "audit_verdict": "minor-correction"},
    }
    decisions = {
        "unsafe-review": {"action": "ACCEPT_WITH_REVIEW"},
        "unsafe-ordinary": {"action": "ACCEPT"},
        "safe-review": {"action": "ACCEPT_WITH_REVIEW"},
        "minor": {"action": "ACCEPT"},
    }
    result = score(labels, decisions, "test")
    assert result["critical_review"] == ["unsafe-review"]
    assert result["critical_ordinary_accept"] == ["unsafe-ordinary"]
    assert result["good_false_escalation"] == ["safe-review"]
    assert result["routing_0.00"]["critical_caught"] == 1
    assert result["routing_0.00"]["audited"] == 2
