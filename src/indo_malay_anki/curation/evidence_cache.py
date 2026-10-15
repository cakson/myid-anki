"""Claim-scoped, persistent evidence reuse with source-family deduplication.

Providers return inspected facts, never bare search hits. KBBI currently requires an
account, so its adapter advertises manual capture rather than scraping a login page.
PRPM captures likewise use inspected public pages; neither provider is called by builds.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

from .records import RecordError
from .store import atomic_json

CLAIM_KINDS = frozenset(
    {
        "lexical-existence",
        "semantic-meaning",
        "common-usage",
        "preferred-everyday-form",
        "cross-language-contrast",
        "false-friend",
    }
)
LEGACY_CLAIM_KIND = {
    "meaning": "semantic-meaning",
    "locale-usage": "common-usage",
    "preferred-choice": "preferred-everyday-form",
    "relation": "cross-language-contrast",
    "misleading-contrast": "false-friend",
}
KIND_TO_LEGACY = {value: key for key, value in LEGACY_CLAIM_KIND.items()}
KIND_TO_LEGACY["lexical-existence"] = "lexical-existence"
SOURCE_REGISTRY = {
    "kbbi": {
        "family": "Badan Bahasa KBBI",
        "locale": "Indonesia",
        "access": "account-required-manual-capture",
        "reference": "https://kbbi.kemendikdasmen.go.id/",
    },
    "prpm": {
        "family": "Dewan Bahasa dan Pustaka PRPM",
        "locale": "Malaysia",
        "access": "public-page-manual-capture",
        "reference": "https://prpm.dbp.gov.my/",
    },
}


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def canonical_ref(reference: str) -> str:
    parts = urlsplit(reference)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise RecordError("evidence needs an HTTP(S) canonical reference")
    return urlunsplit(("https", parts.netloc.lower(), parts.path.rstrip("/"), parts.query, ""))


def validate_fact(raw: dict[str, Any]) -> dict[str, Any]:
    required = (
        "locale",
        "form",
        "sense",
        "claim_kind",
        "source_id",
        "source_family",
        "publisher",
        "canonical_reference",
        "observation",
        "method",
        "accessed_at",
        "usage_basis",
        "stance",
        "origin_candidate",
        "origin_claim_id",
        "origin_proposition",
        "limitations",
    )
    if not isinstance(raw, dict) or any(
        not isinstance(raw.get(key), str) or not raw[key].strip() for key in required
    ):
        raise RecordError("cached evidence requires complete provenance and claim fields")
    if raw["locale"] not in {"Indonesia", "Malaysia"}:
        raise RecordError("invalid evidence locale")
    if raw["claim_kind"] not in CLAIM_KINDS:
        raise RecordError("invalid evidence claim kind")
    if raw["stance"] not in {"supports", "contradicts", "inconclusive"}:
        raise RecordError("invalid evidence stance")
    if raw["method"] not in {"retrieved-page", "corpus-query", "manual-inspection"}:
        raise RecordError("bare search hits cannot enter the evidence cache")
    if raw["usage_basis"] not in {"dictionary-only", "contextual", "comparative"}:
        raise RecordError("invalid evidence usage basis")
    if (
        raw["claim_kind"] == "preferred-everyday-form"
        and raw["usage_basis"] == "dictionary-only"
        and raw["stance"] == "supports"
    ):
        raise RecordError("dictionary existence cannot support everyday preference")
    try:
        accessed = datetime.fromisoformat(raw["accessed_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordError("invalid evidence access time") from exc
    if accessed.tzinfo is None:
        raise RecordError("evidence access time needs timezone")
    item = dict(raw)
    item["canonical_reference"] = canonical_ref(item["canonical_reference"])
    item["cache_key"] = hashlib.sha256(
        json.dumps(
            {
                "locale": normalized(item["locale"]),
                "form": normalized(item["form"]),
                "sense": normalized(item["sense"]),
                "kind": item["claim_kind"],
                "family": normalized(item["source_family"]),
                "reference": item["canonical_reference"],
                "origin_claim": item["origin_claim_id"],
                "inspection": hashlib.sha256(
                    (item["observation"] + item["accessed_at"]).encode()
                ).hexdigest(),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return item


@dataclass(frozen=True, slots=True)
class EvidenceQuery:
    locale: str
    form: str
    sense: str
    claim_kind: str
    proposition: str
    candidate_ref: str
    claim_id: str


class EvidenceProvider(Protocol):
    provider_id: str

    def lookup_many(self, queries: list[EvidenceQuery]) -> list[dict[str, Any]]:
        """Return inspected, claim-scoped facts for a batch of queries."""


class EvidenceCache:
    def __init__(self, root: Path):
        self.path = Path(root) / "curation/evidence-cache/records.json"

    def records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("records"), list):
            raise RecordError("invalid evidence cache schema")
        return [validate_fact(item) for item in data["records"]]

    def upsert_many(self, facts: list[dict[str, Any]]) -> tuple[int, int]:
        existing = {item["cache_key"]: item for item in self.records()}
        hits = misses = 0
        for raw in facts:
            item = validate_fact(raw)
            prior = existing.get(item["cache_key"])
            if prior is not None:
                if prior != item:
                    raise RecordError("cache key collision with changed inspected content")
                hits += 1
            else:
                existing[item["cache_key"]] = item
                misses += 1
        if misses:
            atomic_json(
                self.path,
                {
                    "schema_version": 1,
                    "records": sorted(existing.values(), key=lambda x: x["cache_key"]),
                },
            )
        return hits, misses

    def lookup_many(
        self, queries: list[EvidenceQuery]
    ) -> tuple[dict[tuple[str, str], list[dict]], int, int]:
        facts = self.records()
        result: dict[tuple[str, str], list[dict]] = {}
        hits = misses = 0
        for query in queries:
            if query.claim_kind not in CLAIM_KINDS:
                raise RecordError("invalid queried claim kind")
            matched = [
                item
                for item in facts
                if item["locale"] == query.locale
                and normalized(item["form"]) == normalized(query.form)
                and normalized(item["sense"]) == normalized(query.sense)
                and item["claim_kind"] == query.claim_kind
                and (
                    item["origin_candidate"] == query.candidate_ref
                    and item["origin_claim_id"] == query.claim_id
                    or normalized(item["origin_proposition"]) == normalized(query.proposition)
                )
            ]
            result[(query.candidate_ref, query.claim_id)] = matched
            hits += bool(matched)
            misses += not bool(matched)
        return result, hits, misses


def queries_for_candidate(
    candidate_ref: str, candidate: dict[str, Any], stages: dict[str, dict[str, Any]]
) -> list[EvidenceQuery]:
    queries: list[EvidenceQuery] = []
    for role in ("indonesian-usage", "malaysian-usage"):
        locale = "Indonesia" if role == "indonesian-usage" else "Malaysia"
        form = candidate["indonesian" if locale == "Indonesia" else "malaysian"]
        for claim in stages.get(role, {}).get("claims", []):
            kind = LEGACY_CLAIM_KIND.get(claim.get("claim_type"))
            if kind is None:
                continue
            queries.append(
                EvidenceQuery(
                    locale,
                    form,
                    candidate["sense"],
                    kind,
                    claim["proposition"],
                    candidate_ref,
                    claim["claim_id"],
                )
            )
    return queries


def materialize_observations(
    query: EvidenceQuery, facts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Link reused facts to a current claim, without upgrading existence to preference."""
    result = []
    for fact in facts:
        item = validate_fact(fact)
        if (
            item["locale"] != query.locale
            or normalized(item["form"]) != normalized(query.form)
            or normalized(item["sense"]) != normalized(query.sense)
            or item["claim_kind"] != query.claim_kind
        ):
            continue
        if not (
            item["origin_candidate"] == query.candidate_ref
            and item["origin_claim_id"] == query.claim_id
            or normalized(item["origin_proposition"]) == normalized(query.proposition)
        ):
            continue
        result.append(
            {
                "evidence_id": f"cache-{item['cache_key'][:16]}-{query.claim_id}",
                "claim_id": query.claim_id,
                "claim_type": KIND_TO_LEGACY[query.claim_kind],
                "source_group": item["source_family"],
                "source_family": item["source_family"],
                "source_title": item["source_id"],
                "publisher": item["publisher"],
                "url_or_query": item["canonical_reference"],
                "accessed_at": item["accessed_at"],
                "observation": item["observation"],
                "page_location_or_query": item.get("page_location") or "inspected source",
                "audit_method": item["method"],
                "usage_basis": item["usage_basis"],
                "stance": item["stance"],
                "locale": item["locale"],
                "limitations": item["limitations"],
                "origin_candidate": item["origin_candidate"],
                "cache_key": item["cache_key"],
            }
        )
    return result


class StoredCaptureProvider:
    """Batch adapter for inspected KBBI/PRPM or contextual source captures on disk."""

    provider_id = "stored-captures-v1"

    def __init__(self, root: Path):
        self.path = Path(root) / "curation/evidence-cache/inspected-captures.json"

    def lookup_many(self, queries: list[EvidenceQuery]) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise RecordError("invalid inspected capture schema")
        facts = [validate_fact(item) for item in data["records"]]
        keys = {
            (query.locale, normalized(query.form), normalized(query.sense), query.claim_kind)
            for query in queries
        }
        return [
            fact
            for fact in facts
            if (
                fact["locale"],
                normalized(fact["form"]),
                normalized(fact["sense"]),
                fact["claim_kind"],
            )
            in keys
        ]


class ArchivedObservationProvider:
    """Batch-load claim-linked inspected observations from existing candidate artifacts."""

    provider_id = "archived-observations-v1"

    def __init__(self, root: Path):
        self.root = Path(root)

    def lookup_many(self, queries: list[EvidenceQuery]) -> list[dict[str, Any]]:
        from .store import BatchStore
        from .workflow import current_results

        wanted = {query.candidate_ref for query in queries}
        facts: list[dict[str, Any]] = []
        for ref in sorted(wanted):
            batch_id, candidate_id = ref.split(":", 1)
            store = BatchStore(self.root, batch_id)
            candidate = store.candidate(candidate_id)
            stages = current_results(store, candidate_id)
            claims = {
                claim["claim_id"]: claim
                for role in ("indonesian-usage", "malaysian-usage", "relation-proposal")
                for claim in stages.get(role, {}).get("claims", [])
            }
            for observation in stages.get("evidence-audit", {}).get("observations", []):
                claim = claims.get(observation.get("claim_id"))
                if claim is None or claim.get("claim_type") not in LEGACY_CLAIM_KIND:
                    continue
                locale = claim.get("locale") or observation.get("locale")
                if locale not in {"Indonesia", "Malaysia"}:
                    continue
                form = candidate["indonesian" if locale == "Indonesia" else "malaysian"]
                locator = observation.get("url_or_query", "")
                if not isinstance(locator, str) or not locator.startswith(("https://", "http://")):
                    continue
                fact = {
                    "locale": locale,
                    "form": form,
                    "sense": candidate["sense"],
                    "claim_kind": LEGACY_CLAIM_KIND[claim["claim_type"]],
                    "source_id": observation["source_group"],
                    "source_family": observation["source_group"],
                    "publisher": observation["publisher"],
                    "canonical_reference": locator,
                    "observation": observation["observation"],
                    "method": observation["audit_method"],
                    "accessed_at": observation["accessed_at"],
                    "usage_basis": observation.get("usage_basis", "contextual"),
                    "stance": observation["stance"],
                    "origin_candidate": ref,
                    "origin_claim_id": claim["claim_id"],
                    "origin_proposition": claim["proposition"],
                    "limitations": observation.get("limitations") or "No limitations recorded.",
                }
                if (
                    fact["claim_kind"] == "preferred-everyday-form"
                    and fact["usage_basis"] == "dictionary-only"
                    and fact["stance"] == "supports"
                ):
                    fact["stance"] = "inconclusive"
                facts.append(validate_fact(fact))
        return facts


def now_utc() -> str:
    return datetime.now(UTC).isoformat()
