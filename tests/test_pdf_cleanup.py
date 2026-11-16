"""Step 01: repairing PDF damage (README: "Repair PDF damage").

Invisible characters are written as escapes so they can be read:
\\u00ad = soft hyphen, \\ufb01 = "fi" ligature, \\u200b = zero-width space.
"""

from human_data.pdf_text import (clean_pdf_paragraph, fix_hyphenation, fix_spacing, join_lines,
                                 normalize_characters, remove_footnote_numbers)


def test_word_split_across_lines_is_joined():
    assert join_lines(["Die Wirt-", "schaft wächst."]) == "Die Wirtschaft wächst."


def test_hyphen_before_und_is_kept():
    assert join_lines(["Berufs-", "und Wirtschaftspädagogik"]) == "Berufs- und Wirtschaftspädagogik"


def test_normal_line_break_becomes_a_space():
    assert join_lines(["Ein Satz", "geht weiter"]) == "Ein Satz geht weiter"


def test_fix_hyphenation():
    assert fix_hyphenation("Die Wirt- schaft") == "Die Wirtschaft"
    assert fix_hyphenation("Berufs- und Wirtschaftspädagogik") == "Berufs- und Wirtschaftspädagogik"
    assert fix_hyphenation("Covid- 19 und Online- Plattformen") == "Covid-19 und Online-Plattformen"


def test_soft_hyphens_ligatures_and_invisible_characters_are_removed():
    assert normalize_characters("Infrastruk\u00ad turen") == "Infrastrukturen"
    assert normalize_characters("\ufb01nden \ufb02ach") == "finden flach"
    assert normalize_characters("Text\x07 mit\u200b Resten") == "Text mit Resten"
    assert normalize_characters("a\u2011b") == "a-b"


def test_bullet_glyphs_become_one_bullet():
    assert normalize_characters("▪ Punkt \uf0b7 Punkt") == "• Punkt • Punkt"


def test_footnote_numbers_are_removed():
    assert remove_footnote_numbers("Es wurde gearbeitet30.") == "Es wurde gearbeitet."
    assert remove_footnote_numbers("(Storytelling)29 dar") == "(Storytelling) dar"
    assert remove_footnote_numbers("werden.12 Die") == "werden. Die"


def test_real_numbers_are_kept():
    text = "COVID-19 und CO2 und Abb.1 und [15] und S. 45"
    assert remove_footnote_numbers(text) == text


def test_fix_spacing():
    assert fix_spacing("(s.o. II. 3.) . Das") == "(s.o. II. 3.). Das"
    assert fix_spacing("( Abb. 2) ist so , gut") == "(Abb. 2) ist so, gut"
    assert fix_spacing("… sind. “ Ein") == "… sind.“ Ein"


def test_full_paragraph_cleanup():
    text = "Die Wirt- schaft hat neue Ver- fahren30 ( siehe oben) ge\ufb01ltert ."
    assert clean_pdf_paragraph(text) == "Die Wirtschaft hat neue Verfahren (siehe oben) gefiltert."
