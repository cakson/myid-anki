"""Evidence reuse keeps claim scope, source identity, and preference separate."""

from copy import deepcopy

import pytest

from indo_malay_anki.curation.evidence_cache import (
    EvidenceCache,
    EvidenceQuery,
    materialize_observations,
    validate_fact,
)
from indo_malay_anki.curation.records import RecordError


def fact():
    return {
        "locale": "Malaysia",
        "form": "biskut",
        "sense": "dry baked snack",
        "claim_kind": "semantic-meaning",
        "source_id": "PRPM biskut",
        "source_family": "Dewan Bahasa dan Pustaka PRPM",
        "publisher": "Dewan Bahasa dan Pustaka",
        "canonical_reference": "https://prpm.dbp.gov.my/Cari1?keyword=biskut",
        "observation": "Dictionary defines biskut as a dry baked snack.",
        "method": "retrieved-page",
        "accessed_at": "2026-10-13T00:00:00+00:00",
        "usage_basis": "dictionary-only",
        "stance": "supports",
        "origin_candidate": "food-001:foods-06",
        "origin_claim_id": "my-meaning",
        "origin_proposition": "Biskut means a dry baked snack.",
        "limitations": "Definition does not establish preference.",
    }


def test_claim_scoped_persistent_cache_and_batch_reuse(tmp_path):
    cache = EvidenceCache(tmp_path)
    item = fact()
    assert cache.upsert_many([item]) == (0, 1)
    assert EvidenceCache(tmp_path).upsert_many([item]) == (1, 0)
    matched = EvidenceQuery(
        "Malaysia",
        "BISKUT",
        "dry baked snack",
        "semantic-meaning",
        item["origin_proposition"],
        "later-batch:one",
        "new-meaning",
    )
    wrong_sense = EvidenceQuery(
        "Malaysia",
        "biskut",
        "restaurant bill",
        "semantic-meaning",
        item["origin_proposition"],
        "later-batch:two",
        "new-meaning",
    )
    wrong_claim = EvidenceQuery(
        "Malaysia",
        "biskut",
        "dry baked snack",
        "preferred-everyday-form",
        item["origin_proposition"],
        "later-batch:three",
        "new-preference",
    )
    matches, hits, misses = cache.lookup_many([matched, wrong_sense, wrong_claim])
    assert (hits, misses) == (1, 2)
    linked = materialize_observations(matched, matches[(matched.candidate_ref, matched.claim_id)])
    assert linked[0]["claim_id"] == "new-meaning"
    assert linked[0]["origin_candidate"] == "food-001:foods-06"
    assert linked[0]["source_family"] == "Dewan Bahasa dan Pustaka PRPM"


def test_dictionary_definition_cannot_be_upgraded_to_preference():
    item = fact()
    item["claim_kind"] = "preferred-everyday-form"
    with pytest.raises(RecordError, match="dictionary existence"):
        validate_fact(item)


def test_bare_search_hit_is_not_inspected_evidence():
    item = deepcopy(fact())
    item["method"] = "search-result"
    with pytest.raises(RecordError, match="bare search hits"):
        validate_fact(item)
