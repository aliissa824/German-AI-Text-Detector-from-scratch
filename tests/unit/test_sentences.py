"""Step 01: where a sentence ends (README: "Not every period ends a sentence")."""

import pytest

from human_data.text_utils import split_into_sentences


@pytest.mark.parametrize(
    "text, expected",
    [
        # Abbreviations from the list
        ("Das gilt z. B. für Schulen. Danach kommt ein neuer Satz.",
         ["Das gilt z. B. für Schulen.", "Danach kommt ein neuer Satz."]),
        ("Dr. Müller kam. Er sprach.", ["Dr. Müller kam.", "Er sprach."]),
        ("Es geht um vgl. Kapitel drei. Gut.", ["Es geht um vgl. Kapitel drei.", "Gut."]),
        # Letter chains
        ("Das gilt z.B. für Schulen. Danach kommt etwas.",
         ["Das gilt z.B. für Schulen.", "Danach kommt etwas."]),
        # Single initials
        ("Siehe A. Müller und andere. Neuer Satz.", ["Siehe A. Müller und andere.", "Neuer Satz."]),
        # Decimal numbers
        ("Der Wert beträgt 3.14 im Mittel. Weiter.", ["Der Wert beträgt 3.14 im Mittel.", "Weiter."]),
        # Ordinal numbers
        ("Im 19. Jahrhundert änderte sich viel. Später auch.",
         ["Im 19. Jahrhundert änderte sich viel.", "Später auch."]),
        ("Am 3. Mai begann es. Dann endete es.", ["Am 3. Mai begann es.", "Dann endete es."]),
        ("Die 2. Auflage erschien 2001. Sie war neu.", ["Die 2. Auflage erschien 2001.", "Sie war neu."]),
        # A page number at the end of a sentence still ends it
        ("Siehe S. 45. Danach folgt der Rest.", ["Siehe S. 45.", "Danach folgt der Rest."]),
        # Lowercase next word: the sentence goes on
        ("Er kam ca. zehn Jahre später. Ende.", ["Er kam ca. zehn Jahre später.", "Ende."]),
        # Repeated marks: only the last one counts
        ("Warte... Dann ging es weiter.", ["Warte...", "Dann ging es weiter."]),
        ("Wann? Heute!? Ja.", ["Wann?", "Heute!?", "Ja."]),
        # ? or ! inside a sentence
        ("Das ist (widerlegend?) zum Teil falsch. Gut.", ["Das ist (widerlegend?) zum Teil falsch.", "Gut."]),
        ("Ist das so? Ja. Wirklich!", ["Ist das so?", "Ja.", "Wirklich!"]),
    ],
)
def test_sentence_ends(text, expected):
    assert split_into_sentences(text) == expected


def test_closing_german_quote_stays_with_its_sentence():
    # README example: the closing quote after the period belongs to the sentence
    text = "Er sagte: „Ich legte das Abitur ab.“ Danach studierte er."
    assert split_into_sentences(text) == ["Er sagte: „Ich legte das Abitur ab.“", "Danach studierte er."]


def test_closing_bracket_stays_with_its_sentence():
    text = "Das war bekannt (siehe oben.) Danach kam mehr."
    assert split_into_sentences(text)[0] == "Das war bekannt (siehe oben.)"


def test_opening_english_quote_is_not_pulled_into_the_previous_sentence():
    text = "Das ist der Satz. “Ein neues Zitat” beginnt hier."
    assert split_into_sentences(text) == ["Das ist der Satz.", "“Ein neues Zitat” beginnt hier."]


def test_unfinished_text_at_the_end_is_dropped():
    assert split_into_sentences("Ein vollständiger Satz. Und ein unvollständiger") == ["Ein vollständiger Satz."]


def test_empty_text():
    assert split_into_sentences("") == []
    assert split_into_sentences("   \n ") == []
