"""Deterministic quote location.

NOT part of the E1 freeze. Introduced for E1b.

The model supplies a verbatim quote; this module computes where it is. Character
counting is something code does perfectly and language models do poorly — E1
dropped 33 of ~40 correct extractions purely on miscounted offsets, with
`text_absent_from_passage` at zero across all three runs.

WHAT THIS IS NOT
----------------
It is not a rescue layer. There is no fuzzy matching, no edit distance, no
stemming, no semantic similarity, no "closest match". A quote either occurs in
the passage or it does not. The only tolerance is for WHITESPACE, and only
because whitespace is presentation rather than content — and even then the
result maps back to exact canonical offsets, so the Citation stays as trustworthy
as one the model had counted correctly.

D-020 P2 is unchanged. What changes is only WHO COMPUTES THE OFFSETS. An
unlocatable quote is still dropped, never hedged.

AMBIGUITY
---------
A quote occurring more than once is not silently assigned to the first hit.
Two occurrences of identical text can sit in different contexts — one inside an
interviewer's question, one inside the answer — and picking wrong would produce
a citation that resolves perfectly while pointing at the wrong speaker. That is
the misattribution failure D-020 P3 exists to prevent, arriving through the back
door. Disambiguation is attempted only where reading order leaves exactly one
candidate; otherwise the fact is dropped.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

#: Outcomes.
RESOLVED = "resolved"
ABSENT = "text_absent_from_passage"
AMBIGUOUS = "quote_ambiguous"
EMPTY = "quote_empty"

#: How a resolved quote was located. Recorded on every Citation so the path is
#: auditable rather than assumed.
EXACT = "exact"
EXACT_ORDERED = "exact_reading_order"
WHITESPACE = "whitespace_normalised"
WHITESPACE_ORDERED = "whitespace_normalised_reading_order"


@dataclass
class LocateResult:
    status: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    method: Optional[str] = None
    occurrences: int = 0
    #: Text actually present at the returned offsets. Always echoed back so the
    #: caller cites what the passage holds, never what the model typed.
    canonical_text: Optional[str] = None


def locate(passage_text: str, quote: str, search_from: int = 0) -> LocateResult:
    """Locate `quote` in `passage_text`.

    `search_from` is the end offset of the previously located quote in the same
    passage. It is used ONLY to break ties, and only when it leaves exactly one
    candidate.
    """
    if not quote or not quote.strip():
        return LocateResult(status=EMPTY)

    trimmed = quote.strip()

    hits = _find_all(passage_text, trimmed)
    if hits:
        return _choose(passage_text, hits, search_from, EXACT, EXACT_ORDERED)

    # Whitespace-only tolerance. Presentation, not content.
    norm_text, index_map = _normalise_whitespace(passage_text)
    norm_quote, _ = _normalise_whitespace(trimmed)
    norm_quote = norm_quote.strip()
    if not norm_quote:
        return LocateResult(status=EMPTY)

    norm_hits = _find_all(norm_text, norm_quote)
    if not norm_hits:
        return LocateResult(status=ABSENT, occurrences=0)

    mapped = [(index_map[s], index_map[e - 1] + 1) for s, e in norm_hits]
    return _choose(passage_text, mapped, search_from, WHITESPACE, WHITESPACE_ORDERED,
                   already_spans=True)


def _choose(passage_text: str, hits, search_from: int, method: str,
            ordered_method: str, already_spans: bool = False) -> LocateResult:
    spans: List[Tuple[int, int]] = (
        hits if already_spans else [(s, e) for s, e in hits])

    if len(spans) == 1:
        s, e = spans[0]
        return LocateResult(status=RESOLVED, char_start=s, char_end=e, method=method,
                            occurrences=1, canonical_text=passage_text[s:e])

    # More than one. Reading order breaks the tie only if it leaves exactly one.
    forward = [(s, e) for s, e in spans if s >= search_from]
    if len(forward) == 1:
        s, e = forward[0]
        return LocateResult(status=RESOLVED, char_start=s, char_end=e,
                            method=ordered_method, occurrences=len(spans),
                            canonical_text=passage_text[s:e])

    return LocateResult(status=AMBIGUOUS, occurrences=len(spans))


def _find_all(haystack: str, needle: str) -> List[Tuple[int, int]]:
    out, i = [], haystack.find(needle)
    while i != -1:
        out.append((i, i + len(needle)))
        i = haystack.find(needle, i + 1)
    return out


def _normalise_whitespace(text: str) -> Tuple[str, List[int]]:
    """Collapse whitespace runs to one space, keeping a map to original indices.

    `index_map[i]` is the original index of `normalised[i]`, so a match in
    normalised space converts back to exact canonical offsets.
    """
    chars: List[str] = []
    index_map: List[int] = []
    prev_ws = False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_ws:
                chars.append(" ")
                index_map.append(i)
            prev_ws = True
        else:
            chars.append(ch)
            index_map.append(i)
            prev_ws = False
    return "".join(chars), index_map
