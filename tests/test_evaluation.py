from pathlib import Path

from src.chunking import build_chunks
from src.corpus import load_book
from src.evaluation import evaluate_cases, load_evaluation_cases


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
