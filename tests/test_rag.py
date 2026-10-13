from pathlib import Path

import pytest

from src.chunking import Chunk, build_chunks
from src.corpus import load_book
from src.rag import DEFAULT_MIN_SCORE, build_grounded_answer


def make_chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="doc-1",
        chapter_id="chapter-1",
        chapter_title="CHAPTER I. TEST",
        chunk_index=0,
        text=text,
        source="book.txt",
    )


def test_supported_answer_quotes_retrieved_text_and_has_matching_reference() -> None:
    chunk = make_chunk(
        "chapter-17-chunk-001",
        "It is much safer to be feared than loved, when either must be dispensed with.",
    )

    result = build_grounded_answer("When is it safer to be feared than loved?", [chunk])

    assert result.refused is False
    assert result.answer.startswith("Evidence excerpt from the book:")
    assert result.citations == (chunk.chunk_id,)
    assert result.references[0].chunk_id in {
        item.chunk.chunk_id for item in result.retrieved
    }
    assert result.references[0].excerpt == chunk.text
    assert "CHAPTER I. TEST" in result.render()
    assert "Answer:" in result.render()
    assert "References:" in result.render()


def test_no_matching_content_returns_refusal_without_citations() -> None:
    result = build_grounded_answer(
        "Who won the World Cup in 1958?", [make_chunk("c1", "The prince values counsel.")]
    )

    assert result.refused is True
    assert result.references == ()
    assert result.citations == ()
    assert result.retrieved == ()
    assert "enough evidence" in result.answer
    assert "None (no citation is made)." in result.render()


def test_low_score_returns_refusal_without_citations_but_keeps_retrieval() -> None:
    chunk = make_chunk("c1", "The whole world is ruled by princes.")

    result = build_grounded_answer("world cup 1958", [chunk], min_score=0.5)

    assert result.refused is True
    assert result.retrieved[0].score == pytest.approx(1 / 3)
    assert result.references == ()
    assert result.citations == ()
    assert "below the configured minimum" in result.refusal_reason


def test_min_score_is_validated() -> None:
    chunk = make_chunk("c1", "The prince values counsel.")
    for score in (-0.1, 1.1, float("inf"), float("nan")):
        with pytest.raises(ValueError, match="min_score must be between 0 and 1"):
            build_grounded_answer("prince counsel", [chunk], min_score=score)


@pytest.mark.parametrize(
    ("min_score", "expected_refusal"),
    [(0.5, False), (0.5001, True)],
)
def test_answer_threshold_includes_exact_minimum(
    min_score: float, expected_refusal: bool
) -> None:
    chunk = make_chunk("c1", "Virtue guides a prince.")

    result = build_grounded_answer("virtue fortune", [chunk], min_score=min_score)

    assert result.retrieved[0].score == pytest.approx(0.5)
    assert result.refused is expected_refusal
    if expected_refusal:
        assert result.references == ()
        assert result.citations == ()
        assert result.refusal_reason is not None
    else:
        assert result.citations == (chunk.chunk_id,)
        assert result.references[0].excerpt == chunk.text
        assert result.refusal_reason is None


@pytest.mark.parametrize("question", ["", " \t\n ", "the and of"])
def test_empty_content_questions_refuse_even_with_zero_minimum(question: str) -> None:
    chunk = make_chunk("c1", "Virtue and fortune guide a prince.")

    result = build_grounded_answer(question, [chunk], min_score=0.0)

    assert result.refused is True
    assert result.retrieved == ()
    assert result.references == ()
    assert result.citations == ()


def test_real_book_supported_and_unsupported_examples_calibrate_default_threshold() -> None:
    project_root = Path(__file__).resolve().parents[1]
    book = load_book(project_root / "data" / "book.txt")
    chunks = build_chunks(book)

    supported = build_grounded_answer(
        "When is it safer to be feared than loved?", chunks
    )
    unsupported = build_grounded_answer("Who won the World Cup in 1958?", chunks)

    assert DEFAULT_MIN_SCORE == 0.5
    assert supported.refused is False
    assert supported.references[0].chapter_title == "CHAPTER XVII."
    assert supported.references[0].chunk_id == supported.retrieved[0].chunk.chunk_id
    assert unsupported.refused is True
    assert unsupported.retrieved[0].score == pytest.approx(0.25)
    assert unsupported.citations == ()
