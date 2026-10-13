from pathlib import Path

from src.chunking import build_chunks
from src.corpus import Document, load_book
from src.evaluation import EvaluationCase, evaluate_cases, load_evaluation_cases


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_set_covers_supported_evidence_and_unsupported_refusals() -> None:
    cases = load_evaluation_cases(PROJECT_ROOT / "data" / "evaluation.json")
    chunks = build_chunks(load_book(PROJECT_ROOT / "data" / "book.txt"))

    results = evaluate_cases(cases, chunks)

    assert sum(case.supported for case in cases) >= 3
    assert sum(not case.supported for case in cases) >= 2
    assert all(result.passed for result in results)
    assert all(result.evidence_found for result in results if result.case.supported)
    assert all(
        result.answer.refused and not result.answer.references
        for result in results
        if not result.case.supported
    )


def test_evaluation_rejects_wrong_citation_even_when_expected_evidence_is_retrieved() -> None:
    documents = [
        Document(
            doc_id="wrong",
            title="CHAPTER II.",
            text="Virtue and fortune guide rulers.",
            source="book.txt",
            chapter_id="wrong",
        ),
        Document(
            doc_id="expected",
            title="CHAPTER I.",
            text="Fortune influences rulers.",
            source="book.txt",
            chapter_id="expected",
        ),
    ]
    case = EvaluationCase(
        case_id="wrong-citation",
        question="virtue fortune",
        supported=True,
        expected_chapter_prefix="CHAPTER I.",
        evidence_terms=("fortune",),
    )

    result = evaluate_cases([case], build_chunks(documents), top_k=2)[0]

    # Expected evidence in the search results is not enough: it must be cited.
    assert any(
        item.chunk.chapter_title == "CHAPTER I."
        and "fortune" in item.chunk.text.casefold()
        for item in result.answer.retrieved
    )
    assert result.answer.refused is False
    assert result.answer.references[0].chapter_title == "CHAPTER II."
    assert result.evidence_found is False
    assert result.passed is False
