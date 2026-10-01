from dataclasses import FrozenInstanceError

import pytest

from indo_malay_anki.model import (
    DECK_ID,
    GUID_NAMESPACE,
    MODEL_ID,
    ValidatedVocabulary,
    VocabularyConcept,
    stable_guid,
)


def test_ids_are_strings_and_leading_zeroes_are_preserved():
    concept = VocabularyConcept("000001", "car", "mobil", "kereta")
    assert concept.id == "000001"
    assert isinstance(concept.id, str)


def test_compatibility_ids_namespace_and_golden_guid_are_fixed():
    assert DECK_ID == 1242123295
    assert MODEL_ID == 1942161817
    assert GUID_NAMESPACE == "myid-anki:v1"
    assert stable_guid("000001") == "D6BBAuKXK"


def test_concept_is_immutable():
    concept = VocabularyConcept("000001", "car", "mobil", "kereta")
    with pytest.raises(FrozenInstanceError):
        concept.english = "automobile"
    exposed_tags = concept.tags
    exposed_tags.append("unvalidated")
    assert concept.tags == []


def test_validated_vocabulary_cannot_be_constructed_by_callers():
    with pytest.raises(TypeError):
        ValidatedVocabulary((VocabularyConcept("000001", "car", "mobil", "kereta"),), ())


def test_distinct_concept_ids_have_distinct_guids():
    assert stable_guid("000001") != stable_guid("000002")
