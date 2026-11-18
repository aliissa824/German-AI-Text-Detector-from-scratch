"""Step 10: the rewrite rules of the humanizer attack."""

import pytest

from humanizer import formalize, humanize

AI_STYLE = ("Jedoch zeigt die Studie beziehungsweise ihre Methode entscheidende Fragen sowie Probleme. "
            "Darüber hinaus gilt dies insbesondere für Schulen. Dies ist beispielsweise in Berlin so.")


def test_light_attack_swaps_ai_words_for_plain_ones():
    text, changes = humanize(AI_STYLE, "light")
    assert text == ("Aber zeigt die Studie bzw. ihre Methode wichtige Fragen und Probleme. "
                    "Außerdem gilt dies vor allem für Schulen. Dies ist zum Beispiel in Berlin so.")
    assert changes == 7


def test_strong_attack_also_adds_human_habits():
    text, changes = humanize(AI_STYLE, "strong")
    assert text.endswith("Das ist z. B. in Berlin so.")
    assert changes == 9


@pytest.mark.parametrize(
    "word, swapped",
    [("jedoch", "aber"), ("Jedoch", "Aber"), ("zudem", "außerdem"), ("lediglich", "nur"),
     ("entscheidenden", "wichtigen"), ("verdeutlichen", "zeigen")],
)
def test_single_words_keep_their_case_and_ending(word, swapped):
    assert humanize(f"Das ist {word} so.")[0] == f"Das ist {swapped} so."


def test_only_whole_words_are_swapped():
    text = "Die Sowieso-Frage und Zudemmer bleiben."
    assert humanize(text) == (text, 0)


def test_formalize_makes_human_text_sound_like_ai():
    text, changes = formalize("Aber die Daten zeigen z. B. nur Trends, außerdem gilt das vor allem hier.")
    assert text == ("Jedoch die Daten zeigen beispielsweise lediglich Trends, zudem gilt das insbesondere hier.")
    assert changes == 5


def test_formalize_keeps_nicht_nur():
    assert formalize("Das gilt nicht nur hier, sondern auch dort.")[1] == 0


def test_text_without_marker_words_is_unchanged():
    text = "Die Kinder lesen jeden Morgen in der Schule."
    assert humanize(text, "strong") == (text, 0)
    assert formalize(text) == (text, 0)


def test_unknown_level_is_an_error():
    with pytest.raises(ValueError):
        humanize("Text", "extreme")
