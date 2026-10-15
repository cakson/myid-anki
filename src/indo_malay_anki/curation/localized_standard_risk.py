"""Retrospective audit signal for standardized terms versus borrowed usage.

This module does not participate in production ACCEPT/HOLD/REJECT decisions.
It reads only candidate and verifier material available at decision time.
"""

from __future__ import annotations

import re

STANDARD_WORDING = re.compile(
    r"\b(?:standard|standardized|standardised|localized|localised|official|formal|prescriptive)\b",
    re.IGNORECASE,
)
BORROWING_WORDING = re.compile(
    r"\b(?:english|international|borrow(?:ed|ing)?|loan(?:word)?|anglicism)\b",
    re.IGNORECASE,
)
STRONG_COMPETITION = re.compile(
    r"\b(?:commonly|common|frequent|often|everyday|casual|colloquial|competes?|dominates?)\b",
    re.IGNORECASE,
)


def classify_localized_standard_risk(decision: dict) -> dict:
    """Return a conservative, explainable *audit* signal from frozen inputs.

    Mentioning an English borrowing alone is insufficient. The verifier must
    also explicitly characterize a proposed answer as standard/localized/formal
    and connect the alternate form to borrowing or English usage. This avoids
    treating the loanword on the card as inherently risky.
    """
    verifier = decision.get("verifier") or {}
    preference = verifier.get("preference_risk") or {}
    rationale = " ".join(
        str(verifier.get(key) or "")
        for key in ("rationale", "risk_rationale", "shared_synonym_rationale")
    )
    alternative_text = " ".join(
        str(value or "") for value in (preference.get("form"), preference.get("rationale"))
    )
    evidence_text = f"{rationale} {alternative_text}"
    result = {
        "level": "none",
        "reasons": [],
        "alternate_form": preference.get("form") or None,
        "source_basis": "production-verifier-only",
    }
    if decision.get("outcome") != "accepted" or decision.get("relation") != "different-common-word":
        return result
    if not preference.get("form") or preference.get("language") not in {
        "indonesian",
        "malaysian",
        "both",
    }:
        return result
    if not STANDARD_WORDING.search(rationale):
        return result
    if not BORROWING_WORDING.search(evidence_text):
        return result
    result["reasons"] = ["proposed-standard-or-localized-form", "named-borrowed-alternative"]
    if STRONG_COMPETITION.search(
        str(verifier.get("risk_rationale") or "") + " " + str(preference.get("rationale") or "")
    ):
        result["level"] = "strong"
        result["reasons"].append("ordinary-usage-competition-mentioned")
    else:
        result["level"] = "possible"
    return result
