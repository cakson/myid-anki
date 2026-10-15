from scripts.audit_prospective_preference_batch import select

from indo_malay_anki.curation.preference_evidence import preference_trigger
from indo_malay_anki.curation.technical_borrowing_risk import technical_borrowing_risk


def row(*, sense, tags, indonesian, malaysian, relation="different-common-word"):
    return {
        "outcome": "accepted",
        "relation": relation,
        "candidate": {
            "sense": sense,
            "tags": tags,
            "indonesian": indonesian,
            "malaysian": malaysian,
        },
    }


def test_translated_online_concept_triggers_without_named_alternative():
    candidate = row(
        sense="online files accessible over the internet",
        tags=["technology"],
        indonesian="simpanan maya",
        malaysian="ruang maya",
    )
    assert technical_borrowing_risk(candidate)["triggered"]
    assert "technical-borrowing-risk" in preference_trigger(candidate)
    assert "technical-borrowing-risk" not in preference_trigger(candidate, include_technical=False)


def test_technology_tag_or_loanword_alone_is_insufficient():
    assert not technical_borrowing_risk(
        row(
            sense="paper record for a customer",
            tags=["technology"],
            indonesian="catatan pelanggan",
            malaysian="rekod pelanggan",
        )
    )["triggered"]
    assert not technical_borrowing_risk(
        row(
            sense="online message from an app",
            tags=["technology"],
            indonesian="notifikasi",
            malaysian="pemberitahuan",
            relation="similar",
        )
    )["triggered"]


def test_nonaccepted_and_spelling_contrasts_do_not_trigger():
    candidate = row(
        sense="computer application",
        tags=["technology"],
        indonesian="aplikasi",
        malaysian="aplikasi",
    )
    candidate["outcome"] = "hold"
    assert not technical_borrowing_risk(candidate)["triggered"]


def test_technical_flag_routes_an_otherwise_clean_accept_to_audit():
    candidate = row(
        sense="online files accessible over the internet",
        tags=["technology"],
        indonesian="simpanan maya",
        malaysian="ruang maya",
    )
    candidate.update(confidence_tier="high", review_flags=["technical-borrowing-risk"])
    assert "flag:technical-borrowing-risk" in select({"candidate": candidate})["candidate"]
