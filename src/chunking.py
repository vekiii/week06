from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from .corpus import Document


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    chapter_id: str
    chapter_title: str
    chunk_index: int
    text: str
    source: str

    @property
    def title(self) -> str:
        """Compatibility alias for consumers that display a source title."""
        return self.chapter_title


def _validate_chunking_parameters(chunk_size: int, overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")


def _normalized_paragraphs(text: str) -> list[str]:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    return [
        " ".join(paragraph.split())
        for paragraph in re.split(r"\n[ \t]*\n+", normalized_newlines)
        if paragraph.strip()
    ]


def split_text_with_overlap(
    text: str,
    chunk_size: int = 140,
    overlap: int = 30,
) -> list[str]:
    """Split text into character-sized chunks, preferring paragraph endings.

    Paragraphs are preserved as units when they fit. A paragraph longer than
    ``chunk_size`` is split at character boundaries. The next chunk starts
    ``overlap`` characters before the previous chunk ended.
    """
    _validate_chunking_parameters(chunk_size, overlap)
    paragraphs = _normalized_paragraphs(text)
    if not paragraphs:
        return []

    normalized = "\n\n".join(paragraphs)
    paragraph_ends: list[int] = []
    cursor = 0
    for paragraph in paragraphs:
        cursor += len(paragraph)
        paragraph_ends.append(cursor)
        cursor += 2

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        target_end = min(start + chunk_size, len(normalized))
        end = target_end

        if target_end < len(normalized):
            paragraph_candidates = [
                boundary
                for boundary in paragraph_ends
                if start < boundary <= target_end
            ]
            if paragraph_candidates:
                preferred_end = paragraph_candidates[-1]
                if preferred_end - start > overlap:
                    end = preferred_end

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized):
            break
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


def build_chunks(
    documents: Sequence[Document],
    chunk_size: int = 140,
    overlap: int = 30,
) -> list[Chunk]:
    """Build stable, metadata-bearing chunks without crossing sections."""
    _validate_chunking_parameters(chunk_size, overlap)
    chunks: list[Chunk] = []
    for document in documents:
        parts = split_text_with_overlap(
            document.text,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        for chunk_index, part in enumerate(parts):
            chunk_id = f"{document.chapter_id}-chunk-{chunk_index:03d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=document.doc_id,
                    chapter_id=document.chapter_id,
                    chapter_title=document.title,
                    chunk_index=chunk_index,
                    text=part,
                    source=document.source,
                )
            )
    return chunks
