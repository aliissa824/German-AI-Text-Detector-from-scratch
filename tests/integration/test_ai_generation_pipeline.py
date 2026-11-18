"""Step 02 as a whole: one human sample goes in, two AI files and a log entry come out.

Uses a fake model and a temporary folder, so nothing real is written or sent.
"""

import json

import pytest

from ai_generation import config as cfg
from ai_generation import generate as gen

from fakes import HUMAN, REWRITE, fake_model


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
    message = gen.process_sample(7, "gpt-5.6-luna", fake_model(REWRITE, REWRITE), "fake-deployment")
    assert (cfg.ASSISTED_DIR / "7.txt").read_text(encoding="utf-8") == REWRITE
    assert (cfg.GENERATED_DIR / "7.txt").read_text(encoding="utf-8") == REWRITE
    log = [json.loads(line) for line in cfg.LOG_FILE.read_text(encoding="utf-8").splitlines()]
    assert [(r["kind"], r["strategy"]) for r in log] == [("ai_assisted", "rewrite"), ("ai_generated", "source_based")]
    assert "ai_assisted=95" in message


def test_existing_files_are_skipped_so_runs_can_resume(folders):
    cfg.ASSISTED_DIR.mkdir()
    (cfg.ASSISTED_DIR / "7.txt").write_text("schon da", encoding="utf-8")
    complete = fake_model(REWRITE)
    message = gen.process_sample(7, "gpt-5.6-luna", complete, "fake-deployment")
    assert "ai_assisted skipped" in message
    assert len(complete.calls) == 1                     # only the AI-generated text was requested
    assert (cfg.ASSISTED_DIR / "7.txt").read_text(encoding="utf-8") == "schon da"


def test_missing_human_text(folders):
    assert gen.process_sample(99, "gpt-5.6-luna", fake_model(), "x") == "99: missing human text"
