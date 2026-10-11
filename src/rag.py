from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .chunking import Chunk
from .retrieval import RetrievalResult, retrieve_top_k


DEFAULT_MIN_SCORE = 0.5
REFUSAL_MESSAGE = (
    "I do not have enough evidence in the retrieved book passages to answer this question."
)


@dataclass(frozen=True)
class Reference:
    chunk_id: str
    chapter_title: str
    source: str
    excerpt: str


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    references: tuple[Reference, ...]
    retrieved: tuple[RetrievalResult, ...]
    refused: bool
    refusal_reason: str | None = None

    @property
    def citations(self) -> tuple[str, ...]:
        return tuple(reference.chunk_id for reference in self.references)

    def render(self) -> str:
        lines = ["Answer:", self.answer]
        if self.refusal_reason:
            lines.append(f"Reason: {self.refusal_reason}")
        lines.append("References:")
        if not self.references:
            lines.append("None (no citation is made).")
        else:
            for reference in self.references:
                lines.append(
                    f"- [{reference.chunk_id}] {reference.chapter_title} - {reference.source}"
                )
                lines.append(f'  Evidence excerpt: "{reference.excerpt}"')
        return "\n".join(lines)


def build_grounded_answer(
    question: str,
    chunks: Sequence[Chunk],
    top_k: int = 3,
    min_score: float = DEFAULT_MIN_SCORE,
) -> GroundedAnswer:
    """Return an extractive, citation-backed answer or refuse for weak evidence.

    The answer is an exact passage from the highest-ranked chunk, not a generated
    paraphrase. The lexical score is only a coarse filter and cannot establish
    semantic relevance on its own.
    """
    if not math.isfinite(min_score) or not 0.0 <= min_score <= 1.0:
        raise ValueError("min_score must be between 0 and 1")

    retrieved = tuple(retrieve_top_k(question, chunks, k=top_k))
    if not retrieved:
        return GroundedAnswer(
            answer=REFUSAL_MESSAGE,
            references=(),
            retrieved=(),
            refused=True,
            refusal_reason="No content words from the question matched the corpus.",
        )

    best = retrieved[0]
    if best.score < min_score:
        return GroundedAnswer(
            answer=REFUSAL_MESSAGE,
            references=(),
            retrieved=retrieved,
            refused=True,
            refusal_reason=(
                f"Best lexical score {best.score:.2f} is below the configured "
                f"minimum {min_score:.2f}."
            ),
        )

    reference = Reference(
        chunk_id=best.chunk.chunk_id,
        chapter_title=best.chunk.chapter_title,
        source=best.chunk.source,
        excerpt=best.chunk.text,
    )
    return GroundedAnswer(
        answer=f'Evidence excerpt from the book: "{reference.excerpt}" [{reference.chunk_id}]',
        references=(reference,),
        retrieved=retrieved,
        refused=False,
    )
