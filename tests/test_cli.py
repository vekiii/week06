from pathlib import Path

import pytest

from src.cli import DEFAULT_CORPUS_PATH, build_parser, main, run


def test_cli_help_exposes_corpus_and_pipeline_options() -> None:
    help_text = build_parser().format_help()

    for option in (
        "--corpus",
        "--corpus-path",
        "--question",
        "--chunk-size",
        "--overlap",
        "--top-k",
        "--show-context",
        "--show-scores",
    ):
        assert option in help_text
    assert "the-prince" in help_text


def test_cli_runs_supported_question_and_shows_reproducible_config(capsys) -> None:
    args = build_parser().parse_args(
        ["--question", "When is it safer to be feared than loved?", "--show-scores"]
    )

    exit_code = run(args)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert f"Corpus: the-prince ({DEFAULT_CORPUS_PATH})" in output
    assert "Configuration: chunk_size=140 chars, overlap=30 chars, top_k=3, min_score=0.50" in output
    assert "Answer:" in output
    assert "References:" in output
    assert "Retrieved context:" in output
    assert "score=" in output


def test_cli_accepts_relative_corpus_path(tmp_path: Path, capsys) -> None:
    # Invalid corpus content exercises path parsing and gives a stable format error
    # at the loader boundary; the default corpus is covered by the end-to-end test.
    corpus_file = tmp_path / "book.txt"
    corpus_file.write_text("not a Gutenberg book", encoding="utf-8")
    args = build_parser().parse_args(
        ["--question", "anything", "--corpus-path", str(corpus_file)]
    )

    try:
        run(args)
    except ValueError as exc:
        assert "start marker" in str(exc)
    else:
        raise AssertionError("Malformed corpus should be rejected")


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("--chunk-size", "0", "chunk_size must be > 0"),
        ("--overlap", "140", "overlap must be smaller than chunk_size"),
        ("--top-k", "0", "k must be > 0"),
        ("--min-score", "2", "min_score must be between 0 and 1"),
    ],
)
def test_cli_reports_invalid_configuration_without_traceback(
    option: str, value: str, message: str, capsys
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--question", "virtue fortune", option, value])

    output = capsys.readouterr()
    assert exc_info.value.code == 2
    assert message in output.err
    assert "Traceback" not in output.err
    assert output.out == ""


def test_cli_reports_missing_corpus_without_traceback(tmp_path: Path, capsys) -> None:
    missing_path = tmp_path / "missing-book.txt"

    with pytest.raises(SystemExit) as exc_info:
        main(["--question", "virtue fortune", "--corpus-path", str(missing_path)])

    output = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "Book corpus file not found" in output.err
    assert str(missing_path) in output.err
    assert "Traceback" not in output.err
    assert output.out == ""
