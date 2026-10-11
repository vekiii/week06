from pathlib import Path
import pytest

from src.corpus import (
    CorpusFormatError,
    GUTENBERG_SOURCE,
    load_book,
)


START = "*** START OF THE PROJECT GUTENBERG EBOOK THE PRINCE ***"
END = "*** END OF THE PROJECT GUTENBERG EBOOK THE PRINCE ***"


def write_sample(path: Path, main_text: str = "An example chapter paragraph.") -> Path:
    path.write_text(
        f"""Gutenberg license and header.
{START}
The Prince

Contents
INTRODUCTION
CHAPTER I. CONTENTS ENTRY

INTRODUCTION
A short introduction.

CHAPTER I. CONTENTS AND CHAPTERS
{main_text}

{END}
Closing Gutenberg license.
""",
        encoding="utf-8",
    )
    return path


def test_load_book_removes_gutenberg_boilerplate_and_splits_sections(tmp_path: Path) -> None:
    path = write_sample(tmp_path / "book.txt")

    documents = load_book(path)

    assert [document.title for document in documents] == [
        "INTRODUCTION",
        "CHAPTER I. CONTENTS AND CHAPTERS",
    ]
    assert "Gutenberg license" not in " ".join(document.text for document in documents)
    assert "Closing Gutenberg license" not in " ".join(
        document.text for document in documents
    )
    assert documents[0].text == "A short introduction."
    assert documents[1].text == "An example chapter paragraph."
    assert all(document.source == GUTENBERG_SOURCE for document in documents)


def test_load_book_uses_stable_section_ids_and_reads_utf8(tmp_path: Path) -> None:
    path = write_sample(tmp_path / "book.txt", "Machiavelli\u2019s text has UTF-8 punctuation.")

    first = load_book(path)
    second = load_book(path)

    assert [document.doc_id for document in first] == [
        "prince-section-001",
        "prince-section-002",
    ]
    assert [document.doc_id for document in first] == [
        document.doc_id for document in second
    ]
    assert "Machiavelli\u2019s" in first[1].text


def test_load_book_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Book corpus file not found"):
        load_book(tmp_path / "missing.txt")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("plain text only", "start marker was not found"),
        (f"{START}\nbody only", "end marker was not found"),
        (
            f"{START}\nContents\nINTRODUCTION\nCHAPTER I. ENTRY\n{END}",
            "distinguish the contents list",
        ),
    ],
)
def test_load_book_fails_clearly_for_invalid_structure(
    tmp_path: Path, content: str, message: str
) -> None:
    path = tmp_path / "invalid.txt"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(CorpusFormatError, match=message):
        load_book(path)


def test_load_book_parses_existing_project_corpus() -> None:
    path = Path("data/book.txt")
    if not path.is_file():
        pytest.skip("local Gutenberg corpus is not present")

    documents = load_book(path)

    assert len(documents) >= 29
    assert documents[0].title == "INTRODUCTION"
    assert sum(document.title.startswith("CHAPTER ") for document in documents) == 26
    assert any(document.title.startswith("DESCRIPTION OF THE METHODS ADOPTED") for document in documents)
    assert any(document.title.startswith("THE LIFE OF CASTRUCCIO CASTRACANI") for document in documents)
    assert not any("Gutenberg" in document.text for document in documents)
