"""Step 01: cutting documents into chunks (README: "Cut-off sentences would have been a shortcut")."""

import random

import pytest

from human_data import config as cfg
from human_data.chunking import chunk_document, evenly_spaced, nearest_sentence_chunk
from human_data.text_utils import word_count


@pytest.fixture(scope="module")
def document():
    """A long made-up document of 400 sentences with 9 to 26 words each."""
    rng = random.Random(1)
    words = "Schule Lehrkraft Unterricht Studie Ergebnis Methode Analyse Gruppe Daten Frage Bildung".split()
    sentences = []
    for _ in range(400):
        body = " ".join(rng.choice(words).lower() for _ in range(rng.randint(8, 25)))
        sentences.append(f"Die {body}.")
    return " ".join(sentences)


def test_nearest_sentence_end_is_chosen():
    sentences = ["eins zwei drei", "vier fünf", "sechs sieben acht neun"]
    # 3 words is 2 away from the target of 5, 5 words hits it: stop after sentence 2
    assert nearest_sentence_chunk(sentences, 0, 5) == (2, 5)


def test_tie_goes_to_the_longer_chunk():
    # 2 and 4 words are both 1 away from 3
    assert nearest_sentence_chunk(["a b", "c d"], 0, 3) == (2, 4)


def test_shorter_chunk_wins_when_it_is_closer():
    # 3 words is 1 away from 4, 8 words is 4 away
    assert nearest_sentence_chunk(["a b c", "d e f g h"], 0, 4) == (1, 3)


def test_evenly_spaced():
    assert evenly_spaced(list(range(10)), 3) == [0, 4, 9]
    assert evenly_spaced([1, 2], 3) == [1, 2]
    assert evenly_spaced(list(range(5)), 1) == [2]


def test_at_most_three_chunks_per_document(document):
    assert len(chunk_document(document, "doc-1")) == cfg.MAX_CHUNKS_PER_DOCUMENT == 3


def test_chunks_end_on_a_full_sentence_and_start_with_a_capital(document):
    for chunk in chunk_document(document, "doc-1", max_chunks=20):
        assert chunk["text"].endswith(".")
        assert chunk["text"][0].isupper()


def test_chunks_stay_within_30_percent_of_their_target(document):
    for chunk in chunk_document(document, "doc-1", max_chunks=20):
        target = chunk["target_length"]
        assert target in cfg.TARGET_WORDS
        assert abs(word_count(chunk["text"]) - target) <= target * cfg.MAX_LENGTH_DEVIATION


def test_first_chunk_is_skipped(document):
    numbers = [chunk["chunk_number"] for chunk in chunk_document(document, "doc-1", max_chunks=100)]
    assert numbers and 1 not in numbers


def test_context_before_is_about_120_words(document):
    for chunk in chunk_document(document, "doc-1"):
        assert 0 < word_count(chunk["context_before"]) <= 120 + 26   # may end with one longer sentence


def test_same_document_gives_the_same_chunks(document):
    assert chunk_document(document, "doc-1") == chunk_document(document, "doc-1")


def test_target_lengths_rotate_per_document(document):
    starts = {chunk_document(document, f"doc-{i}", max_chunks=100)[0]["target_length"] for i in range(30)}
    assert len(starts) > 1


def test_empty_or_tiny_document_gives_no_chunks():
    assert chunk_document("", "x") == []
    assert chunk_document("Nur ein Satz hier.", "x") == []
