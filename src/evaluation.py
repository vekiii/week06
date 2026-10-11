from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Sequence

from .chunking import build_chunks
from .corpus import load_book
from .rag import GroundedAnswer, build_grounded_answer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVALUATION_PATH = PROJECT_ROOT / "data" / "evaluation.json"
DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "book.txt"


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    question: str
    supported: bool
    expected_chapter_prefix: str | None = None
    evidence_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationResult:
    case: EvaluationCase
    answer: GroundedAnswer
    passed: bool
    evidence_found: bool


def load_evaluation_cases(path: str | Path = DEFAULT_EVALUATION_PATH) -> list[EvaluationCase]:
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        EvaluationCase(
            case_id=record["id"],
            question=record["question"],
            supported=record["supported"],
            expected_chapter_prefix=record.get("expected_chapter_prefix"),
            evidence_terms=tuple(record.get("evidence_terms", ())),
        )
        for record in records
    ]


def evaluate_cases(
    cases: Sequence[EvaluationCase],
    chunks,
    top_k: int = 3,
    min_score: float = 0.5,
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    for case in cases:
        answer = build_grounded_answer(
            case.question, chunks, top_k=top_k, min_score=min_score
        )
        evidence_found = False
        if case.supported and case.expected_chapter_prefix:
            evidence_found = any(
                reference.chapter_title.startswith(case.expected_chapter_prefix)
                and all(term.casefold() in reference.excerpt.casefold() for term in case.evidence_terms)
                for reference in answer.references
            )
        passed = (
            not answer.refused and evidence_found
            if case.supported
            else answer.refused and not answer.references
        )
        results.append(
            EvaluationResult(
                case=case,
                answer=answer,
                passed=passed,
                evidence_found=evidence_found,
            )
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Week 6 RAG evaluation set.")
    parser.add_argument("--corpus-path", type=Path, default=DEFAULT_CORPUS_PATH)
    parser.add_argument("--evaluation-path", type=Path, default=DEFAULT_EVALUATION_PATH)
    parser.add_argument("--chunk-size", type=int, default=140)
    parser.add_argument("--overlap", type=int, default=30)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        cases = load_evaluation_cases(args.evaluation_path)
        chunks = build_chunks(
            load_book(args.corpus_path),
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
        results = evaluate_cases(cases, chunks, args.top_k, args.min_score)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(
        f"Configuration: chunk_size={args.chunk_size}, overlap={args.overlap}, "
        f"top_k={args.top_k}, min_score={args.min_score:.2f}"
    )
    for result in results:
        best = result.answer.retrieved[0] if result.answer.retrieved else None
        retrieved = (
            f"{best.chunk.chunk_id} ({best.chunk.chapter_title}, {best.score:.2f})"
            if best
            else "no match"
        )
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status} {result.case.case_id}: refused={result.answer.refused}; "
            f"top={retrieved}; citations={','.join(result.answer.citations) or 'none'}"
        )
    passed_count = sum(result.passed for result in results)
    print(f"Evaluation: {passed_count}/{len(results)} passed")
    return 0 if passed_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
