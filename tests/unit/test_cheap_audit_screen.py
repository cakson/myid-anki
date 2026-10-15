from scripts.benchmark_cheap_audit_screen import validate
from scripts.evaluate_cheap_audit_screen import simulate


def test_screen_accepts_only_audit_priority_output():
    assert (
        validate(
            {"items": {"one": {"decision": "screen-review", "reasons": ["cue-ambiguity"]}}},
            {"one"},
        )["one"]["decision"]
        == "screen-review"
    )


def test_router_union_preserves_existing_critical_routes():
    labels = {
        "routed": {
            "batch": "batch",
            "category": "critical",
            "deterministic_reasons": ["confidence:low"],
        },
        "screened": {
            "batch": "batch",
            "category": "critical",
            "deterministic_reasons": [],
        },
        "safe": {
            "batch": "batch",
            "category": "confirmed-good",
            "deterministic_reasons": [],
        },
    }
    screen = {
        "routed": {"decision": "screen-clear"},
        "screened": {"decision": "screen-review"},
        "safe": {"decision": "screen-clear"},
    }
    result = simulate(labels, screen, "C", 0.0)
    assert result["critical_deterministic"] == 2
    assert result["total_deep_audits"] == 2
