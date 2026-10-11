from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Sequence
import unicodedata

from .chunking import Chunk


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
STOP_WORDS = frozenset(
    """
    a an and are as at be been being by can could did do does for from had has
    have he her hers him his how i if in into is it its may me might my of on
    or our ours she should so than that the their theirs them then there these
    they this those through to up us was we were what when where which who why
    will with would you your yours s t
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Normalize Unicode/case, split into words, and discard common English stops."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return [token for token in TOKEN_RE.findall(normalized) if token not in STOP_WORDS]


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float


def lexical_score(query: str, chunk_text: str) -> float:
    """Return the fraction of distinct query terms found in a chunk.

    Each query term contributes at most once, so repetition in either the query
    or chunk cannot inflate the score. This simple coverage score does not model
    word order, phrase meaning, or term rarity.
    """
    query_terms = set(tokenize(query))
    chunk_terms = set(tokenize(chunk_text))
    if not query_terms or not chunk_terms:
        return 0.0
    return len(query_terms & chunk_terms) / len(query_terms)


def retrieve_top_k(
    query: str,
    chunks: Sequence[Chunk],
    k: int = 3,
    min_score: float = 0.0,
) -> list[RetrievalResult]:
    """Return positive-scoring chunks, ranked deterministically, up to ``k``."""
    if k <= 0:
        raise ValueError("k must be > 0")
    if not math.isfinite(min_score) or not 0.0 <= min_score <= 1.0:
        raise ValueError("min_score must be between 0 and 1")

    scored = [
        RetrievalResult(chunk=chunk, score=lexical_score(query, chunk.text))
        for chunk in chunks
    ]
    filtered = [item for item in scored if item.score > 0.0 and item.score >= min_score]
    filtered.sort(key=lambda item: (-item.score, item.chunk.chunk_id))
    return filtered[:k]
