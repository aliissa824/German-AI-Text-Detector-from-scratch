"""Step 01: the quality check every chunk has to pass (README: "Quality check every chunk")."""

import pytest

from human_data.quality import is_good_academic_chunk

GOOD = (
    "Die vorliegende Untersuchung geht der Frage nach, wie Lehrkräfte an Grundschulen mit digitalen "
    "Lernplattformen umgehen. Grundlage sind leitfadengestützte Interviews mit zwölf Lehrkräften aus drei "
    "Bundesländern, die im Frühjahr geführt wurden. Es zeigt sich, dass die Plattformen vor allem zur "
    "Verteilung von Arbeitsblättern genutzt werden, während kooperative Funktionen kaum eine Rolle spielen. "
    "Als Gründe nennen die Befragten fehlende Fortbildungen und eine unzuverlässige technische Ausstattung."
)


def test_normal_academic_prose_is_kept():
    assert is_good_academic_chunk(GOOD) == (True, None)


@pytest.mark.parametrize(
    "text, reason",
    [
        (GOOD.replace("Die vorliegende", "die vorliegende"), "chunk_starts_mid_sentence"),
        (GOOD[:-1], "chunk_not_prose"),                                   # doesn't end on a full sentence
        (GOOD + " Mehr unter www.example.org im Netz.", "chunk_url_or_email"),
        (GOOD + " Siehe ISBN 978-3-16-148410-0 für Details.", "chunk_bibliographic_info"),
        (GOOD.replace("Als Gründe", "• Als Gründe"), "chunk_bullet_list"),
        (GOOD.replace("Lernplattformen", "Lern- plattformen").replace("Arbeitsblättern", "Arbeits- blättern"),
         "chunk_broken_hyphenation"),
        (GOOD.replace("Frage", "Fr�ge"), "chunk_broken_characters"),
        (" ".join(GOOD.split()[:30]) + ".", "chunk_not_prose"),             # too short
    ],
)
def test_bad_chunks_are_rejected_with_a_reason(text, reason):
    assert is_good_academic_chunk(text) == (False, reason)
