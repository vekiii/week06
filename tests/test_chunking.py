import pytest

from src.chunking import build_chunks, split_text_with_overlap
from src.corpus import Document


def test_split_text_with_overlap_preserves_paragraph_boundaries_when_possible() -> None:
    text = f"{'A' * 55}\n\n{'B' * 55}\n\n{'C' * 20}"

    chunks = split_text_with_overlap(text, chunk_size=120, overlap=15)

    assert len(chunks) >= 2
    assert chunks[0].endswith('B' * 55)
    assert chunks[1].startswith('B' * 15)
    assert chunks[1].endswith('C' * 20)
    assert all(len(chunk) <= 120 for chunk in chunks)


def test_split_text_with_overlap_splits_long_paragraph_with_overlap() -> None:
    text = 'abcdefghijklmnopqrstuvwxyz'

    chunks = split_text_with_overlap(text, chunk_size=12, overlap=4)

    assert chunks == ['abcdefghijkl', 'ijklmnopqrst', 'qrstuvwxyz']
    assert chunks[0][-4:] == chunks[1][:4]
    assert chunks[1][-4:] == chunks[2][:4]
    assert all(len(chunk) <= 12 for chunk in chunks)


def test_split_text_with_overlap_handles_empty_and_short_text() -> None:
    assert split_text_with_overlap('  \n\n  ', chunk_size=12, overlap=2) == []
    assert split_text_with_overlap(' short text ', chunk_size=20, overlap=4) == [
        'short text'
    ]


def test_split_text_with_overlap_recognizes_windows_paragraph_breaks() -> None:
    text = f"{'A' * 50}\r\n \r\n{'B' * 50}"

    chunks = split_text_with_overlap(text, chunk_size=120, overlap=10)

    assert chunks == [f"{'A' * 50}\n\n{'B' * 50}"]


def test_split_text_with_overlap_validates_parameters() -> None:
    for size, overlap in [(0, 0), (-1, 0), (10, -1), (10, 10), (10, 12)]:
        with pytest.raises(ValueError):
            split_text_with_overlap('text', chunk_size=size, overlap=overlap)


def test_build_chunks_validates_parameters_for_empty_input() -> None:
    with pytest.raises(ValueError, match="chunk_size must be > 0"):
        build_chunks([], chunk_size=0, overlap=0)


def test_build_chunks_keeps_source_section_metadata_and_stable_ids() -> None:
    documents = [
        Document(
            doc_id='prince-section-003',
            title='CHAPTER I. EXAMPLE',
            text='The first paragraph.\n\nThe second paragraph.',
            source='https://www.gutenberg.org/ebooks/1232',
            chapter_id='prince-section-003',
        ),
        Document(
            doc_id='prince-section-004',
            title='CHAPTER II. NEXT',
            text='Another section.',
            source='https://www.gutenberg.org/ebooks/1232',
            chapter_id='prince-section-004',
        ),
    ]

    first = build_chunks(documents, chunk_size=24, overlap=5)
    second = build_chunks(documents, chunk_size=24, overlap=5)

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert first[0].chunk_id == 'prince-section-003-chunk-000'
    assert first[-1].chunk_id.startswith('prince-section-004-')
    assert first[0].chapter_id == 'prince-section-003'
    assert first[0].chapter_title == 'CHAPTER I. EXAMPLE'
    assert first[0].title == first[0].chapter_title
    assert first[0].source == documents[0].source
    assert all(chunk.doc_id == chunk.chapter_id for chunk in first)


def test_build_chunks_skips_empty_documents_and_never_mixes_sections() -> None:
    documents = [
        Document('empty', 'Empty', ' \n ', 'source', 'empty'),
        Document('one', 'Chapter One', 'A' * 25, 'source', 'one'),
        Document('two', 'Chapter Two', 'B' * 25, 'source', 'two'),
    ]

    chunks = build_chunks(documents, chunk_size=12, overlap=3)

    assert chunks
    assert all('B' not in chunk.text for chunk in chunks if chunk.chapter_id == 'one')
    assert all('A' not in chunk.text for chunk in chunks if chunk.chapter_id == 'two')
    assert not any(chunk.doc_id == 'empty' for chunk in chunks)


def test_split_text_with_overlap_handles_unicode() -> None:
    text = 'Machiavelli\u2019s prince \u2014 fortuna and virt\u00f9.'

    chunks = split_text_with_overlap(text, chunk_size=20, overlap=5)

    assert ''.join(chunks).count('\u2019') >= 1
    assert all(len(chunk) <= 20 for chunk in chunks)
