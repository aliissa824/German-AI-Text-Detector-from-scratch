"""Step 02: generating the AI texts, tested with a fake model instead of a real API.

No API key is needed: `complete` is replaced by a small function that returns
fixed answers, so the tests check our own logic (retries, refusals, lengths, files).
"""

import json

import pytest

from ai_generation import config as cfg
from ai_generation import generate as gen
from ai_generation import prompts as P


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    # Retries normally wait 2, 4, 8 ... seconds
    monkeypatch.setattr(gen.time, "sleep", lambda seconds: None)


def answers(*replies):
    """A fake model that gives these replies one after another."""
    replies = list(replies)
    calls = []

    def complete(instructions, text):
        calls.append((instructions, text))
        return replies.pop(0)

    complete.calls = calls
    return complete


HUMAN = " ".join(["Wort"] * 100)            # a 100-word human text
REWRITE = " ".join(["Neu"] * 95)
REFUSAL = "I'm sorry, but I cannot assist with that request."


def test_length_range_is_plus_minus_20_percent():
    assert gen.length_range(100, "source_based") == (80, 120)
    assert gen.length_range(100, "topics") == (80, 120)
    assert gen.length_range(1, "topics") == (1, 1)          # never 0 words


def test_refusal_is_rejected_and_retried():
    complete = answers(REFUSAL, REWRITE)
    text, topics = gen.make_assisted(complete, HUMAN)
    assert text == REWRITE and topics is None
    assert len(complete.calls) == 2


def test_answer_must_be_at_least_half_as_long_as_the_human_text():
    half = " ".join(["Neu"] * 50)
    assert gen.make_assisted(answers(half), HUMAN)[0] == half
    too_short = " ".join(["Neu"] * 49)
    with pytest.raises(RuntimeError, match="too short"):
        gen.make_assisted(answers(*[too_short] * cfg.MAX_RETRIES), HUMAN)


def test_empty_answers_are_retried_then_given_up():
    complete = answers(*[""] * cfg.MAX_RETRIES)
    with pytest.raises(RuntimeError, match="empty answer"):
        gen.make_assisted(complete, HUMAN)
    assert len(complete.calls) == cfg.MAX_RETRIES


def test_source_based_prompt_contains_the_human_text_and_length():
    complete = answers(REWRITE)
    gen.make_generated(complete, HUMAN, "source_based")
    instructions, prompt = complete.calls[0]
    assert instructions == P.SOURCE_BASED_INSTRUCTIONS
    assert HUMAN in prompt and "80" in prompt and "120" in prompt


def test_topics_strategy_never_shows_the_human_text():
    topics = "1. Lernplattformen\n2. Grundschule\n3. Fortbildung"
    complete = answers(topics, REWRITE)
    text, returned_topics = gen.make_generated(complete, HUMAN, "topics")
    assert (text, returned_topics) == (REWRITE, topics)
    (first_instructions, first_input), (second_instructions, second_prompt) = complete.calls
    assert first_instructions == P.TOPICS_EXTRACT_INSTRUCTIONS and first_input == HUMAN
    assert second_instructions == P.TOPICS_INSTRUCTIONS
    assert topics in second_prompt and HUMAN not in second_prompt


def test_unknown_strategy_is_an_error():
    with pytest.raises(ValueError):
        gen.make_generated(answers(), HUMAN, "something_else")


def test_prompt_templates_fill_without_errors():
    P.SOURCE_BASED_TEMPLATE.format(target_words=100, min_words=80, max_words=120, text="Text")
    P.TOPICS_TEMPLATE.format(target_words=100, min_words=80, max_words=120, notes="Themen")


def test_model_id_ranges_cover_every_human_sample_once():
    ranges = sorted(spec["seed_ids"] for spec in cfg.MODELS.values())
    assert ranges[0][0] == 1 and ranges[-1][1] == 10227
    for (_, end), (next_start, _) in zip(ranges, ranges[1:]):
        assert next_start == end + 1


@pytest.fixture
def folders(tmp_path, monkeypatch):
    """Point step 02 at an empty temporary data folder."""
    for name, sub in [("HUMAN_DIR", "human"), ("ASSISTED_DIR", "ai-assisted"),
                      ("GENERATED_DIR", "ai-generated")]:
        monkeypatch.setattr(cfg, name, tmp_path / sub)
    monkeypatch.setattr(cfg, "LOG_FILE", tmp_path / "generation_log.jsonl")
    cfg.HUMAN_DIR.mkdir()
    (cfg.HUMAN_DIR / "7").write_text("", encoding="utf-8")   # not a .txt: ignored
    (cfg.HUMAN_DIR / "7.txt").write_text(HUMAN, encoding="utf-8")
    return tmp_path


def test_process_sample_writes_both_files_and_logs_them(folders):
    message = gen.process_sample(7, "gpt-5.6-luna", answers(REWRITE, REWRITE), "fake-deployment")
    assert (cfg.ASSISTED_DIR / "7.txt").read_text(encoding="utf-8") == REWRITE
    assert (cfg.GENERATED_DIR / "7.txt").read_text(encoding="utf-8") == REWRITE
    log = [json.loads(line) for line in cfg.LOG_FILE.read_text(encoding="utf-8").splitlines()]
    assert [(r["kind"], r["strategy"]) for r in log] == [("ai_assisted", "rewrite"), ("ai_generated", "source_based")]
    assert "ai_assisted=95" in message


def test_existing_files_are_skipped_so_runs_can_resume(folders):
    cfg.ASSISTED_DIR.mkdir()
    (cfg.ASSISTED_DIR / "7.txt").write_text("schon da", encoding="utf-8")
    complete = answers(REWRITE)
    message = gen.process_sample(7, "gpt-5.6-luna", complete, "fake-deployment")
    assert "ai_assisted skipped" in message
    assert len(complete.calls) == 1                     # only the AI-generated text was requested
    assert (cfg.ASSISTED_DIR / "7.txt").read_text(encoding="utf-8") == "schon da"


def test_missing_human_text(folders):
    assert gen.process_sample(99, "gpt-5.6-luna", answers(), "x") == "99: missing human text"
