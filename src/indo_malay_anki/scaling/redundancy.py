"""Cheap cross-corpus exclusion followed by bounded semantic review."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from indo_malay_anki.curation.duplicates import comparison_key
from indo_malay_anki.curation.workflow import archive_candidates

from .coverage import inventory

_ALIASES = {
    "cell phone": "mobile phone",
    "cellphone": "mobile phone",
    "smartphone": "mobile phone",
    "rail station": "train station",
    "automobile": "car",
    "motorcar": "car",
    "trash can": "garbage bin",
    "rubbish bin": "garbage bin",
    "bathroom": "washroom",
}
_STOP = {"a", "an", "the", "of", "for", "to", "and", "in", "on", "concept"}


def cue_key(value: str) -> str:
    key = comparison_key(value)
    return _ALIASES.get(key, key)


def _tokens(value: str) -> frozenset[str]:
    return frozenset(
        token
        for token in re.findall(r"\w+", comparison_key(value))
        if token not in _STOP and not token.isdecimal()
    )


class ExclusionIndex:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}
        self.by_cue: dict[str, set[str]] = defaultdict(set)
        self.by_answer: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.by_token: dict[str, set[str]] = defaultdict(set)

    def add(self, ref: str, candidate: Mapping[str, Any], *, prior_same: bool = False) -> None:
        item = {**candidate, "ref": ref, "prior_same": prior_same}
        self.items[ref] = item
        self.by_cue[cue_key(str(item.get("english", "")))].add(ref)
        self.by_answer[self._answer_key(item)].add(ref)
        for token in _tokens(str(item.get("english", ""))):
            self.by_token[token].add(ref)

    @staticmethod
    def _answer_key(candidate: Mapping[str, Any]) -> tuple[str, str]:
        return (
            str(candidate.get("indonesian", "")).strip().casefold(),
            str(candidate.get("malaysian", "")).strip().casefold(),
        )

    def shortlist(self, candidate: Mapping[str, Any], limit: int = 8) -> list[dict]:
        key = cue_key(str(candidate.get("english", "")))
        candidate_tokens = _tokens(key)
        refs = set(self.by_cue.get(key, set()))
        answer_key = self._answer_key(candidate)
        if all(answer_key):
            refs.update(self.by_answer.get(answer_key, set()))
        for token in candidate_tokens:
            refs.update(self.by_token.get(token, set()))
        ranked = []
        for ref in refs:
            item = self.items[ref]
            tokens = _tokens(str(item.get("english", "")))
            similarity = len(candidate_tokens & tokens) / max(1, len(candidate_tokens | tokens))
            exact = cue_key(str(item.get("english", ""))) == key
            answer = all(answer_key) and self._answer_key(item) == answer_key
            if exact or answer or similarity >= 0.25:
                ranked.append((int(exact), int(answer), similarity, ref, item))
        ranked.sort(reverse=True)
        return [item for _, _, _, _, item in ranked[:limit]]

    def screen(
        self,
        candidate: Mapping[str, Any],
        *,
        resolver: Callable[[Mapping[str, Any], Mapping[str, Any]], str] | None = None,
    ) -> dict:
        matches = self.shortlist(candidate)
        if not matches:
            return {"outcome": "admitted", "matches": []}
        first = matches[0]
        cue_match = cue_key(str(candidate.get("english", ""))) == cue_key(
            str(first.get("english", ""))
        )
        answer_match = all(self._answer_key(candidate)) and self._answer_key(
            candidate
        ) == self._answer_key(first)
        sense_new = comparison_key(str(candidate.get("sense", "")))
        sense_old = comparison_key(str(first.get("sense", "")))
        different_sense = bool(sense_new and sense_old and sense_new != sense_old)
        needs_review = not answer_match and (
            (cue_match and bool(sense_new) and (different_sense or not sense_old)) or not cue_match
        )
        if resolver and needs_review:
            result = resolver(candidate, first)
            if result == "distinct":
                return {
                    "outcome": "distinct-sense",
                    "matches": matches,
                    "rationale": "reviewed distinct sense",
                }
            if result == "same":
                return {"outcome": "redundant", "matches": matches, "rationale": "semantic review"}
        if needs_review:
            return {"outcome": "needs-semantic-review", "matches": matches}
        if first["prior_same"]:
            return {"outcome": "prior-same", "matches": matches}
        if answer_match or (
            cue_match
            and comparison_key(str(candidate.get("english", "")))
            == comparison_key(str(first.get("english", "")))
        ):
            return {"outcome": "duplicate", "matches": matches}
        if cue_match:
            return {"outcome": "redundant", "matches": matches}
        return {"outcome": "needs-semantic-review", "matches": matches}

    @classmethod
    def from_root(cls, root: Path, run_id: str | None = None) -> ExclusionIndex:
        root = Path(root)
        result = cls()
        same = set(inventory(root)["prior_same_refs"])
        for item in archive_candidates(root, run_id or "feature-004-new"):
            ref = str(item.get("candidate_id") or item.get("id") or "")
            if ref:
                result.add(ref, item, prior_same=ref in same)
        return result
