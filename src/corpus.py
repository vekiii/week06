from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


GUTENBERG_SOURCE = "https://www.gutenberg.org/ebooks/1232"
GUTENBERG_TEXT_URL = "https://www.gutenberg.org/cache/epub/1232/pg1232.txt"

_START_MARKER = re.compile(
    r"^\*{3}\s*START OF THE PROJECT GUTENBERG EBOOK\b.*\*{3}\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_END_MARKER = re.compile(
    r"^\*{3}\s*END OF THE PROJECT GUTENBERG EBOOK\b.*\*{3}\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_CHAPTER_HEADING = re.compile(
    r"^CHAPTER\s+[IVXLCDM]+\.(?:\[\d+\])?(?:\s+.*)?$",
    re.IGNORECASE,
)
_APPENDIX_HEADINGS = (
    "DESCRIPTION OF THE METHODS ADOPTED",
    "THE LIFE OF CASTRUCCIO CASTRACANI",
)


class CorpusFormatError(ValueError):
    """Raised when a Gutenberg text file is missing expected structure."""


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    source: str
    chapter_id: str


def _extract_gutenberg_body(raw_text: str) -> str:
    start = _START_MARKER.search(raw_text)
    end = _END_MARKER.search(raw_text)
    if start is None:
        raise CorpusFormatError("Project Gutenberg start marker was not found")
    if end is None:
        raise CorpusFormatError("Project Gutenberg end marker was not found")
    if end.start() <= start.end():
        raise CorpusFormatError("Project Gutenberg markers are out of order")

    body = raw_text[start.end():end.start()]
    lines = body.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    contents_index = next(
        (index for index, line in enumerate(lines) if line.strip().casefold() == "contents"),
        None,
    )
    if contents_index is None:
        raise CorpusFormatError("Book contents heading was not found")

    introduction_indexes = [
        index
        for index in range(contents_index + 1, len(lines))
        if lines[index].strip().casefold() == "introduction"
    ]
    if len(introduction_indexes) < 2:
        raise CorpusFormatError(
            "Could not distinguish the contents list from the book introduction"
        )

    # The first INTRODUCTION is in the table of contents; the second starts the text.
    return "\n".join(lines[introduction_indexes[1]:]).strip()


def _is_section_heading(line: str) -> bool:
    heading = line.strip()
    upper = heading.upper()
    return (
        upper == "INTRODUCTION"
        or _CHAPTER_HEADING.fullmatch(heading) is not None
        or any(upper.startswith(prefix) for prefix in _APPENDIX_HEADINGS)
    )


def _split_sections(book_text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in book_text.splitlines():
        if _is_section_heading(line):
            if current_title is not None:
                text = "\n".join(current_lines).strip()
                if text:
                    sections.append((current_title, text))
            current_title = line.strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        text = "\n".join(current_lines).strip()
        if text:
            sections.append((current_title, text))

    return sections


def load_book(path: str | Path) -> list[Document]:
    """Load Gutenberg eBook 1232 as one document per titled section/chapter.

    The source file is left untouched. Gutenberg's license/header and closing
    boilerplate are excluded using the eBook's explicit boundary markers.
    """
    book_path = Path(path)
    if not book_path.is_file():
        raise FileNotFoundError(f"Book corpus file not found: {book_path}")

    try:
        raw_text = book_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CorpusFormatError(f"Book corpus is not valid UTF-8: {book_path}") from exc

    body = _extract_gutenberg_body(raw_text)
    sections = _split_sections(body)
    if not sections:
        raise CorpusFormatError("No titled book sections or chapters were found")
    if not any(_CHAPTER_HEADING.fullmatch(title) for title, _ in sections):
        raise CorpusFormatError("No chapter headings were found in the book text")

    documents: list[Document] = []
    for index, (title, text) in enumerate(sections, start=1):
        section_id = f"prince-section-{index:03d}"
        documents.append(
            Document(
                doc_id=section_id,
                title=title,
                text=text,
                source=GUTENBERG_SOURCE,
                chapter_id=section_id,
            )
        )
    return documents
