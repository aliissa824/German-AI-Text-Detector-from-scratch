"""Step 01: small text helpers and the document-level split."""

import datetime as dt
from collections import Counter

from human_data.text_utils import clean_whitespace, is_german, parse_date, sha256_text, word_count
from human_data.writer import assign_split


def test_word_count():
    assert word_count("Ein  Satz\nmit vier") == 4
    assert word_count("") == 0


def test_clean_whitespace():
    assert clean_whitespace("a b  c\r\n\n\n\nd ") == "a b c\n\nd"
    assert clean_whitespace(None) == ""


def test_parse_date():
    assert parse_date("2019-05-03") == dt.date(2019, 5, 3)
    assert parse_date("03.05.2019") == dt.date(2019, 5, 3)
    assert parse_date("") is None


def test_year_only_counts_as_the_end_of_that_year():
    # So a text dated only "2022" can't slip past the 2022-12-31 cut-off
    assert parse_date("2019") == dt.date(2019, 12, 31)


def test_text_hash_finds_duplicates():
    assert sha256_text("Gleicher Text") == sha256_text("Gleicher Text")
    assert sha256_text("Gleicher Text") != sha256_text("Anderer Text")


def test_language_check():
    assert is_german("Die Untersuchung zeigt, dass Lehrkräfte digitale Lernplattformen vor allem für Arbeitsblätter nutzen.")
    assert not is_german("This study shows that teachers mainly use digital platforms to share worksheets.")


def test_split_is_fixed_per_document():
    assert assign_split("ssoar:12345") == assign_split("ssoar:12345")


def test_split_is_about_80_10_10():
    counts = Counter(assign_split(f"doc-{i}") for i in range(10_000))
    assert 0.77 < counts["train"] / 10_000 < 0.83
    assert 0.08 < counts["validation"] / 10_000 < 0.12
    assert 0.08 < counts["test"] / 10_000 < 0.12
