"""Step 01: old German spelling is converted (README: "Old spelling would have been another shortcut")."""

import pytest

from human_data.quality import modernize_spelling, uses_old_spelling


@pytest.mark.parametrize(
    "old, new",
    [
        ("daß", "dass"), ("Daß", "Dass"), ("Prozeß", "Prozess"), ("bewußt", "bewusst"),
        ("mußte", "musste"), ("läßt", "lässt"), ("häßlich", "hässlich"), ("Einfluß", "Einfluss"),
        ("Schluß", "Schluss"), ("Mißbrauch", "Missbrauch"), ("Mißerfolg", "Misserfolg"),
        ("müßte", "müsste"), ("bißchen", "bisschen"),
    ],
)
def test_old_spelling_is_converted(old, new):
    assert modernize_spelling(old) == (new, 1)


@pytest.mark.parametrize(
    "word",
    ["Maß", "Maßnahme", "gemäß", "Fuß", "Fußball", "Spaß", "saß", "aß", "heißt", "weiß",
     "groß", "Straße", "Gruß", "grüßt"],
)
def test_sz_after_a_long_vowel_stays(word):
    assert modernize_spelling(word) == (word, 0)


def test_whole_sentence_counts_each_replacement():
    text, count = modernize_spelling("Er sagte, daß der Prozeß wichtig sei, aber das Maß stimmt.")
    assert text == "Er sagte, dass der Prozess wichtig sei, aber das Maß stimmt."
    assert count == 2


def test_uses_old_spelling():
    assert uses_old_spelling("Er sagte, daß der Prozeß wichtig sei.")
    assert not uses_old_spelling("Er sagte, dass der Prozess wichtig sei.")
    assert not uses_old_spelling("Nur ein daß unter neuen: dass, dass.")
