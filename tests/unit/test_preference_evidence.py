from datetime import UTC, datetime

import pytest

from indo_malay_anki.curation.preference_evidence import (
    preference_trigger,
    validate_source_record,
)


def test_specific_everyday_competitor_triggers_research():
    decision = {
        "outcome": "accepted",
        "relation": "different-common-word",
        "verifier": {
            "preference_risk": {
                "signal": "credible-everyday-alternative",
                "form": "printer",
            }
        },
    }
    assert preference_trigger(decision) == [
        "specific-preference-signal:credible-everyday-alternative"
    ]


def test_generic_synonym_does_not_trigger_research():
    decision = {
        "outcome": "accepted",
        "relation": "different-common-word",
        "verifier": {
            "preference_risk": {"signal": "named-alternative-exists", "form": "other word"}
        },
    }
    assert preference_trigger(decision) == []


def test_simple_spelling_contrast_stays_fast():
    decision = {
        "outcome": "accepted",
        "relation": "similar",
        "verifier": {"preference_risk": {"signal": "shared-common-form", "form": "other word"}},
    }
    assert preference_trigger(decision) == []


def test_dictionary_cannot_claim_relative_preference():
    record = {
        "source_type": "official-dictionary-terminology",
        "language_market": "malaysia",
        "form": "perisian",
        "sense": "software",
        "claim_roles": ["lexical-existence", "relative-preference"],
        "observation": "The dictionary defines the form.",
        "url": "https://example.org/perisian",
        "source_family": "example-dictionary",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
    }
    with pytest.raises(ValueError, match="dictionary existence"):
        validate_source_record(record)
