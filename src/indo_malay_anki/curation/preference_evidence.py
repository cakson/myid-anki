"""Targeted, audit-oriented preference evidence for prospective curation.

This module does not alter the v3.1 ordinary acceptance gate. It identifies
concrete preference questions and validates research gathered only for them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from urllib.parse import urlsplit

from .localized_standard_risk import classify_localized_standard_risk
from .technical_borrowing_risk import technical_borrowing_risk

SOURCE_TYPES = frozenset(
    {
        "official-dictionary-terminology",
        "government-educational",
        "mainstream-publication",
        "commercial-product-facing",
        "conversational-community",
        "corpus-frequency",
        "other",
    }
)
CLAIM_ROLES = frozenset(
    {"lexical-existence", "semantic-meaning", "ordinary-usage", "relative-preference"}
)
SENSITIVE_SIGNALS = frozenset(
    {
        "credible-everyday-alternative",
        "shared-common-form",
        "preference-strength-uncertain",
        "regional-or-register-competition",
        "same-sense-competition",
        "verifier-explicitly-questions-preference",
    }
)


def preference_trigger(decision: Mapping, *, include_technical: bool = True) -> list[str]:
    """Return concrete reasons for *targeted* research, never a generic synonym trigger."""
    # Already-held candidates cannot enter an unaudited release; this branch
    # exists to route provisional ACCEPTs, not to clear a historical backlog.
    if decision.get("outcome") != "accepted":
        return []
    relation = decision.get("relation")
    verifier = decision.get("verifier") or {}
    preference = verifier.get("preference_risk") or {}
    reasons = []
    signal = preference.get("signal")
    if relation == "different-common-word" and signal in SENSITIVE_SIGNALS:
        risk_text = " ".join(
            str(value or "")
            for value in (preference.get("rationale"), verifier.get("risk_rationale"))
        ).casefold()
        weak_alternative = (
            signal == "credible-everyday-alternative"
            and "broader" in risk_text
            and "everyday" not in risk_text
        )
        unsupported_region_label = signal == "regional-or-register-competition" and not any(
            term in risk_text for term in ("compete", "casual", "ordinary", "everyday", "common")
        )
        if not weak_alternative and not unsupported_region_label:
            reasons.append(f"specific-preference-signal:{signal}")
    localized = classify_localized_standard_risk(dict(decision))
    if localized["level"] != "none":
        reasons.append(f"localized-standard-vs-borrowed:{localized['level']}")
    if include_technical and technical_borrowing_risk(decision)["triggered"]:
        reasons.append("technical-borrowing-risk")
    if relation == "different-common-word" and any(
        "preference" in str(concern).casefold() or "everyday" in str(concern).casefold()
        for concern in verifier.get("concerns", [])
    ):
        reasons.append("verifier-explicit-preference-concern")
    return sorted(set(reasons))


def validate_source_record(value: Mapping) -> dict:
    """Validate one inspected, claim-linked observation; dictionary presence is not usage."""
    required = (
        "source_type",
        "language_market",
        "form",
        "sense",
        "claim_roles",
        "observation",
        "url",
        "source_family",
        "retrieved_at_utc",
    )
    if any(not value.get(key) for key in required):
        raise ValueError("source observation is missing a required field")
    if value["source_type"] not in SOURCE_TYPES:
        raise ValueError("unknown source type")
    if value["language_market"] not in {"indonesia", "malaysia"}:
        raise ValueError("unknown language market")
    roles = value["claim_roles"]
    if not isinstance(roles, list) or not roles or any(role not in CLAIM_ROLES for role in roles):
        raise ValueError("invalid source claim roles")
    if value["source_type"] == "official-dictionary-terminology" and any(
        role in {"ordinary-usage", "relative-preference"} for role in roles
    ):
        raise ValueError("dictionary existence cannot establish everyday preference")
    if urlsplit(str(value["url"])).scheme not in {"https", "http"}:
        raise ValueError("source URL must be HTTP(S)")
    for key in ("form", "sense", "observation", "source_family", "retrieved_at_utc"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"invalid source field: {key}")
    result = dict(value)
    result["cache_key"] = hashlib.sha256(
        json.dumps(
            {
                "market": result["language_market"],
                "form": result["form"].casefold().strip(),
                "sense": result["sense"].casefold().strip(),
                "source_family": result["source_family"].casefold().strip(),
                "url": result["url"],
                "claim_roles": sorted(result["claim_roles"]),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return result
