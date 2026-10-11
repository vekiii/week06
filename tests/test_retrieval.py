import pytest

from src.chunking import Chunk
from src.retrieval import lexical_score, retrieve_top_k, tokenize


def make_chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id='prince-section-001',
        chapter_id='prince-section-001',
        chapter_title='CHAPTER I. EXAMPLE',
        chunk_index=0,
        text=text,
        source='https://www.gutenberg.org/ebooks/1232',
    )


def test_tokenize_normalizes_case_unicode_and_stop_words() -> None:
    assert tokenize('The Machiavelli\u2019s VIRT\u00d9!') == ['machiavelli', 'virt\u00f9']


def test_lexical_score_uses_unique_query_term_coverage() -> None:
    assert lexical_score('prince prince kingdom', 'A prince prince speaks') == pytest.approx(
        1 / 2
    )
    assert lexical_score('prince kingdom', 'prince prince kingdom kingdom') == 1.0
    assert lexical_score('the and of', 'the book and the prince') == 0.0


def test_retrieve_top_k_sorts_by_score_and_obeys_k() -> None:
    chunks = [
        make_chunk('c', 'prince kingdom'),
        make_chunk('a', 'prince kingdom virtue fortune'),
        make_chunk('b', 'prince virtue'),
        make_chunk('zero', 'weather rain'),
    ]

    top_two = retrieve_top_k('prince kingdom virtue', chunks, k=2)
    top_three = retrieve_top_k('prince kingdom virtue', chunks, k=3)

    assert [(item.chunk.chunk_id, item.score) for item in top_two] == [
        ('a', pytest.approx(1.0)),
        ('b', pytest.approx(2 / 3)),
    ]
    assert [item.chunk.chunk_id for item in top_three] == ['a', 'b', 'c']
    assert len(top_three) == 3
    assert all(item.score > 0 for item in top_three)


def test_retrieve_top_k_breaks_ties_by_chunk_id_not_input_order() -> None:
    chunks = [
        make_chunk('z', 'virtue and fortune'),
        make_chunk('a', 'fortune and virtue'),
    ]

    forward = retrieve_top_k('virtue fortune', chunks, k=2)
    reverse = retrieve_top_k('virtue fortune', list(reversed(chunks)), k=2)

    assert [item.chunk.chunk_id for item in forward] == ['a', 'z']
    assert [item.chunk.chunk_id for item in reverse] == ['a', 'z']
    assert forward[0].score == forward[1].score == 1.0


def test_retrieve_top_k_returns_empty_when_no_terms_match() -> None:
    chunks = [make_chunk('a', 'virtue and fortune')]

    assert retrieve_top_k('the and or', chunks, k=2) == []
    assert retrieve_top_k('basketball playoffs', chunks, k=2) == []


def test_retrieve_top_k_applies_configurable_score_threshold() -> None:
    chunks = [
        make_chunk('full', 'prince kingdom virtue'),
        make_chunk('partial', 'prince only'),
    ]

    results = retrieve_top_k('prince kingdom virtue', chunks, k=3, min_score=0.5)

    assert [item.chunk.chunk_id for item in results] == ['full']
    assert retrieve_top_k('prince kingdom virtue', chunks, k=3, min_score=1.0) == [
        results[0]
    ]


def test_retrieve_top_k_validates_k_and_min_score() -> None:
    chunks = [make_chunk('a', 'prince kingdom')]

    for k in (0, -1):
        with pytest.raises(ValueError, match='k must be > 0'):
            retrieve_top_k('prince', chunks, k=k)
    for score in (-0.1, 1.1, float('inf'), float('nan')):
        with pytest.raises(ValueError, match='min_score must be between 0 and 1'):
            retrieve_top_k('prince', chunks, k=1, min_score=score)

@pytest.mark.parametrize("k", [2, 3, 5, 7, 10])
def test_retrieve_top_k_supports_larger_k_values_with_stable_prefix(k: int) -> None:
    chunks = [make_chunk(f"candidate-{index:02d}", "prince counsel") for index in range(12)]

    results = retrieve_top_k("prince", chunks, k=k)

    assert len(results) == k
    assert [item.chunk.chunk_id for item in results] == [
        f"candidate-{index:02d}" for index in range(k)
    ]

