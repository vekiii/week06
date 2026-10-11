from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .chunking import build_chunks
from .corpus import load_book
from .rag import DEFAULT_MIN_SCORE, build_grounded_answer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_PATH = PROJECT_ROOT / "data" / "book.txt"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask a question against a local book corpus using grounded RAG."
    )
    parser.add_argument(
        "--corpus",
        choices=("the-prince",),
        default="the-prince",
        help="Corpus profile to use (default: the-prince).",
    )
    parser.add_argument(
        "--corpus-path",
        type=Path,
        default=DEFAULT_CORPUS_PATH,
        help="UTF-8 Project Gutenberg text file (default: data/book.txt).",
    )
    parser.add_argument("--question", required=True, help="Question to ask the corpus.")
    parser.add_argument(
        "--chunk-size", type=int, default=140, help="Chunk size in characters (default: 140)."
    )
    parser.add_argument(
        "--overlap", type=int, default=30, help="Chunk overlap in characters (default: 30)."
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieval results (default: 3).")
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_SCORE,
        help=f"Minimum lexical coverage to answer (default: {DEFAULT_MIN_SCORE}).",
    )
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Print all retrieved chunks and scores after the answer.",
    )
    parser.add_argument(
        "--show-scores",
        action="store_true",
        help="Print retrieval scores (implies --show-context).",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    documents = load_book(args.corpus_path)
    chunks = build_chunks(documents, chunk_size=args.chunk_size, overlap=args.overlap)
    result = build_grounded_answer(
        args.question,
        chunks,
        top_k=args.top_k,
        min_score=args.min_score,
    )

    print(f"Corpus: {args.corpus} ({args.corpus_path})")
    print(f"Question: {args.question}")
    print(
        "Configuration: "
        f"chunk_size={args.chunk_size} chars, overlap={args.overlap} chars, "
        f"top_k={args.top_k}, min_score={args.min_score:.2f}"
    )
    print()
    print(result.render())

    if args.show_context or args.show_scores:
        print("\nRetrieved context:")
        if not result.retrieved:
            print("None.")
        for item in result.retrieved:
            print(f"- [{item.chunk.chunk_id}] {item.chunk.chapter_title}")
            if args.show_scores:
                print(f"  score={item.score:.3f}")
            print(f"  {item.chunk.text}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (FileNotFoundError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
