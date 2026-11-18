"""Rule-based rewrites for the humanizer attack (step 10).

humanize(text, "light")   swaps typical AI words for the plain ones human writers use
humanize(text, "strong")  does the same, plus typical human abbreviations (z. B., d. h.)
formalize(text)           the reverse: makes a human text sound like AI polishing

The word lists come from step 06: the words TF-IDF relies on most for each class.
Every function returns (new_text, number_of_changes). The rules are deliberately
simple, like the cheap "humanizer" tools people use: they can produce a slightly
awkward word order (e.g. "Aber ist ..." from "Jedoch ist ..."), but never change
the content.
"""

import re

# Formal word (typical for AI-assisted / AI-generated text) -> plain word (typical for human text)
AI_TO_HUMAN = [
    (r"darüber hinaus", "außerdem"),
    (r"jedoch", "aber"),
    (r"beziehungsweise", "bzw."),
    (r"sowie", "und"),
    (r"zudem", "außerdem"),
    (r"hingegen", "dagegen"),
    (r"insbesondere", "vor allem"),
    (r"lediglich", "nur"),
    (r"beispielsweise", "zum Beispiel"),
    (r"zugleich", "gleichzeitig"),
    (r"somit", "also"),
    (r"folglich", "also"),
    (r"verdeutlicht", "zeigt"),
    (r"verdeutlichen", "zeigen"),
    (r"entscheidend(e|en|er|es|em)?", r"wichtig\1"),
]

# Extra habits of human academic writers (only in the "strong" attack)
HUMAN_HABITS = [
    (r"zum Beispiel", "z. B."),
    (r"das heißt", "d. h."),
    (r"unter anderem", "u. a."),
    (r"und so weiter", "usw."),
    (r"(?<=[.!?] )Dies(?= )", "Das"),
]

# Plain word -> formal word (the reverse, for human texts)
HUMAN_TO_AI = [
    (r"z\. ?B\.", "beispielsweise"),
    (r"zum Beispiel", "beispielsweise"),
    (r"d\. ?h\.", "das heißt"),
    (r"u\. ?a\.", "unter anderem"),
    (r"bzw\.", "beziehungsweise"),
    (r"aber", "jedoch"),
    (r"außerdem", "zudem"),
    (r"vor allem", "insbesondere"),
    (r"dagegen", "hingegen"),
    (r"gleichzeitig", "zugleich"),
    (r"(?<!nicht )nur", "lediglich"),      # not "nicht nur ... sondern auch"
    (r"also", "somit"),
]


def _keep_case(original, replacement):
    """'Jedoch' -> 'Aber', 'jedoch' -> 'aber'."""
    if original[:1].isupper() and replacement[:1].islower():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def apply_rules(text, rules):
    """Apply (pattern, replacement) rules as whole words, case-insensitive for the first letter."""
    changes = 0
    for pattern, replacement in rules:
        first, rest = pattern[0], pattern[1:]
        if first.isalpha():                        # match "Jedoch" and "jedoch"
            pattern = f"[{first.upper()}{first.lower()}]{rest}"
        regex = re.compile(rf"(?<![\wäöüÄÖÜß]){pattern}(?![\wäöüÄÖÜß])")

        def swap(match):
            nonlocal changes
            changes += 1
            return _keep_case(match.group(0), match.expand(replacement))

        text = regex.sub(swap, text)
    return text, changes


def humanize(text, level="light"):
    if level not in ("light", "strong"):
        raise ValueError(f"Unknown level: {level}")
    text, changes = apply_rules(text, AI_TO_HUMAN)
    if level == "strong":
        text, more = apply_rules(text, HUMAN_HABITS)
        changes += more
    return text, changes


def formalize(text):
    return apply_rules(text, HUMAN_TO_AI)
