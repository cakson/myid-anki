"""Cheap audit/evidence signal for localized modern technical vocabulary.

This is deliberately lexical and independent of verifier-named alternatives.
It never changes an ACCEPT/HOLD/REJECT decision.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

MODERN_TECH_CONTEXT = re.compile(
    r"\b(?:computer|internet|online|digital|electronic|usb|application|app|"
    r"network|web|virtual|remote|programs?)\b",
    re.IGNORECASE,
)


def technical_borrowing_risk(decision: Mapping) -> dict:
    """Flag a localized multiword IT answer with plausible borrowing exposure.

    The `technology` topic alone is insufficient. A distinct national-word
    claim, a modern technical sense, and a multiword learner answer must all
    be present. This catches translated compounds while leaving ordinary
    loanwords and simple spelling contrasts alone.
    """
    candidate = decision.get("candidate") or {}
    result = {"triggered": False, "reasons": [], "source_basis": "candidate-lexical-only"}
    if decision.get("outcome") != "accepted" or decision.get("relation") != "different-common-word":
        return result
    tags = {str(tag).casefold() for tag in candidate.get("tags", [])}
    if "technology" not in tags:
        return result
    if "verbs" in tags:
        return result
    if not MODERN_TECH_CONTEXT.search(str(candidate.get("sense") or "")):
        return result
    forms = {
        language: str(candidate.get(language) or "").casefold().split()
        for language in ("indonesian", "malaysian")
    }
    localized = [language for language, words in forms.items() if len(words) >= 2]
    if not localized:
        return result
    # A single localized compound against a compact counterpart, or two
    # compounds sharing a translated component, is a specific lexical pattern.
    # Two unrelated compounds alone are too common to route automatically.
    lengths = [len(words) for words in forms.values()]
    if min(lengths) >= 2 and not set(forms["indonesian"]) & set(forms["malaysian"]):
        return result
    result["triggered"] = True
    result["reasons"] = ["modern-technical-sense", "localized-multiword-answer"]
    result["localized_languages"] = localized
    return result
