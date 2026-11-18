"""Step 02: the rules for generating AI texts, tested with a fake model instead of a real API.

No API key is needed: `fake_model` (from tests/fakes.py) returns fixed answers,
so the tests check our own logic: retries, refusals, lengths and prompts.
"""

import pytest

from ai_generation import config as cfg
from ai_generation import generate as gen
from ai_generation import prompts as P

from fakes import HUMAN, REFUSAL, REWRITE, fake_model


def test_length_range_is_plus_minus_20_percent():
    assert gen.length_range(100, "source_based") == (80, 120)
    assert gen.length_range(100, "topics") == (80, 120)
    assert gen.length_range(1, "topics") == (1, 1)          # never 0 words


def test_refusal_is_rejected_and_retried():
    complete = fake_model(REFUSAL, REWRITE)
    text, topics = gen.make_assisted(complete, HUMAN)
    assert text == REWRITE and topics is None
    assert len(complete.calls) == 2


def test_answer_must_be_at_least_half_as_long_as_the_human_text():
    half = " ".join(["Neu"] * 50)
    assert gen.make_assisted(fake_model(half), HUMAN)[0] == half
    too_short = " ".join(["Neu"] * 49)
    with pytest.raises(RuntimeError, match="too short"):
        gen.make_assisted(fake_model(*[too_short] * cfg.MAX_RETRIES), HUMAN)


def test_empty_answers_are_retried_then_given_up():
    complete = fake_model(*[""] * cfg.MAX_RETRIES)
    with pytest.raises(RuntimeError, match="empty answer"):
        gen.make_assisted(complete, HUMAN)
    assert len(complete.calls) == cfg.MAX_RETRIES


def test_source_based_prompt_contains_the_human_text_and_length():
    complete = fake_model(REWRITE)
    gen.make_generated(complete, HUMAN, "source_based")
    instructions, prompt = complete.calls[0]
    assert instructions == P.SOURCE_BASED_INSTRUCTIONS
    assert HUMAN in prompt and "80" in prompt and "120" in prompt


def test_topics_strategy_never_shows_the_human_text():
    topics = "1. Lernplattformen\n2. Grundschule\n3. Fortbildung"
    complete = fake_model(topics, REWRITE)
    text, returned_topics = gen.make_generated(complete, HUMAN, "topics")
    assert (text, returned_topics) == (REWRITE, topics)
    (first_instructions, first_input), (second_instructions, second_prompt) = complete.calls
    assert first_instructions == P.TOPICS_EXTRACT_INSTRUCTIONS and first_input == HUMAN
    assert second_instructions == P.TOPICS_INSTRUCTIONS
    assert topics in second_prompt and HUMAN not in second_prompt


def test_unknown_strategy_is_an_error():
    with pytest.raises(ValueError):
        gen.make_generated(fake_model(), HUMAN, "something_else")


def test_prompt_templates_fill_without_errors():
    P.SOURCE_BASED_TEMPLATE.format(target_words=100, min_words=80, max_words=120, text="Text")
    P.TOPICS_TEMPLATE.format(target_words=100, min_words=80, max_words=120, notes="Themen")


def test_model_id_ranges_cover_every_human_sample_once():
    ranges = sorted(spec["seed_ids"] for spec in cfg.MODELS.values())
    assert ranges[0][0] == 1 and ranges[-1][1] == 10227
    for (_, end), (next_start, _) in zip(ranges, ranges[1:]):
        assert next_start == end + 1
