"""The localized-standard signal is audit-only and requires a concrete pair of clues."""

from indo_malay_anki.curation.localized_standard_risk import classify_localized_standard_risk


def decision(*, relation="different-common-word", rationale="", risk="", alternative=None):
    return {
        "outcome": "accepted",
        "relation": relation,
        "verifier": {
            "rationale": rationale,
            "risk_rationale": risk,
            "preference_risk": alternative or {},
        },
    }


def test_standardized_term_with_named_borrowing_routes_to_audit():
    row = decision(
        rationale="The Malaysian answer is the standard localized term.",
        risk="English-based alternatives may occur in technical usage.",
        alternative={
            "form": "flash drive",
            "language": "malaysian",
            "rationale": "An English borrowing is understood.",
        },
    )
    assert classify_localized_standard_risk(row)["level"] == "possible"


def test_concrete_everyday_competition_is_strong_signal():
    row = decision(
        rationale="The Malaysian answer is the standard Malay form.",
        risk="The English borrowing is common in casual Malaysian speech.",
        alternative={"form": "printer", "language": "malaysian", "rationale": ""},
    )
    assert classify_localized_standard_risk(row)["level"] == "strong"


def test_borrowing_alone_does_not_flag_an_ordinary_loanword():
    row = decision(
        rationale="The Malaysian answer is an everyday borrowed word.",
        alternative={"form": "apron", "language": "indonesian", "rationale": "English borrowing."},
    )
    assert classify_localized_standard_risk(row)["level"] == "none"


def test_similar_spelling_pair_does_not_make_everyday_preference_claim():
    row = decision(
        relation="similar",
        rationale="Both forms are standard spelling variants.",
        alternative={"form": "shift", "language": "malaysian", "rationale": "English borrowing."},
    )
    assert classify_localized_standard_risk(row)["level"] == "none"
