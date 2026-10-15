"""Claim-linked evidence checks; a model assertion never counts as an external signal."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from .records import RecordError, validate_audit_observation


def _aliases(item: Mapping[str, Any]) -> tuple[str, ...]:
    """Collapse obvious mirrors even when an AI invents distinct group names."""
    aliases = ["group:" + str(item["source_group"]).casefold()]
    if item.get("source_family"):
        aliases.append("family:" + str(item["source_family"]).casefold())
    publisher = "".join(char for char in str(item["publisher"]).casefold() if char.isalnum())
    if publisher:
        aliases.append("publisher:" + publisher)
    host = urlsplit(str(item["url_or_query"])).hostname
    if host:
        aliases.append("host:" + host.casefold().removeprefix("www."))
    return tuple(aliases)


def _source_roots(observations: list[Mapping[str, Any]]) -> list[str]:
    parent: dict[str, str] = {}

    def root(alias: str) -> str:
        parent.setdefault(alias, alias)
        if parent[alias] != alias:
            parent[alias] = root(parent[alias])
        return parent[alias]

    for item in observations:
        aliases = _aliases(item)
        first = root(aliases[0])
        for alias in aliases[1:]:
            parent[root(alias)] = first
    return [root(_aliases(item)[0]) for item in observations]


def assess_evidence(
    claims: list[Mapping[str, Any]], observations: list[Mapping[str, Any]], *, relation: str
) -> tuple[bool, list[str]]:
    """Require inspected support for every key claim and independent source groups."""
    reasons: list[str] = []
    by_id = {str(claim.get("claim_id")): claim for claim in claims}
    if len(by_id) != len(claims):
        reasons.append("duplicate-claim-id")
    support: dict[str, set[str]] = defaultdict(set)
    dictionary_only_preference_claims: set[str] = set()
    all_groups: set[str] = set()
    supporting: list[dict[str, Any]] = []
    for raw in observations:
        try:
            item = validate_audit_observation(raw)
        except RecordError:
            reasons.append("uninspected-evidence")
            continue
        claim_id = item["claim_id"]
        if claim_id not in by_id or item["claim_type"] != by_id[claim_id].get("claim_type"):
            reasons.append("evidence-claim-mismatch")
            continue
        if item["stance"] == "contradicts":
            reasons.append("contradictory-evidence")
            continue
        if item["stance"] != "supports":
            continue
        if item["claim_type"] == "preferred-choice" and item.get("usage_basis") not in {
            "contextual",
            "comparative",
        }:
            dictionary_only_preference_claims.add(claim_id)
            continue
        supporting.append(item)
    for item, source_root in zip(supporting, _source_roots(supporting), strict=True):
        support[item["claim_id"]].add(source_root)
        all_groups.add(source_root)
    if any(not support[claim_id] for claim_id in dictionary_only_preference_claims):
        reasons.append("dictionary-only-preference")
    if len(all_groups) < 2:
        reasons.append("insufficient-independent-sources")

    def supported_locale_claim(locale: str, claim_type: str) -> bool:
        return any(
            claim.get("claim_type") == claim_type
            and locale in str(claim.get("locale", "")).casefold()
            and bool(support[claim_id])
            for claim_id, claim in by_id.items()
        )

    def supported_usage(locale: str) -> bool:
        if relation == "different-common-word":
            return supported_locale_claim(locale, "preferred-choice")
        return any(
            supported_locale_claim(locale, claim_type)
            for claim_type in ("preferred-choice", "locale-usage")
        )

    relation_derived = relation != "false-friend" and all(
        supported_locale_claim(locale, "meaning") and supported_usage(locale)
        for locale in ("indonesia", "malaysia")
    )
    for claim_id, claim in by_id.items():
        if not support[claim_id] and not (
            claim.get("claim_type") == "relation" and relation_derived
        ):
            reasons.append(f"unsupported-claim:{claim_id}")
        if relation == "false-friend" and claim.get("claim_type") in {
            "meaning",
            "misleading-contrast",
        }:
            if len(support[claim_id]) < 2:
                reasons.append(f"false-friend-independent-support:{claim_id}")
    if relation == "false-friend":
        if sum(claim.get("claim_type") == "meaning" for claim in claims) < 2:
            reasons.append("false-friend-missing-meanings")
        if not any(claim.get("claim_type") == "misleading-contrast" for claim in claims):
            reasons.append("false-friend-missing-contrast-claim")
    return not reasons, sorted(set(reasons))
