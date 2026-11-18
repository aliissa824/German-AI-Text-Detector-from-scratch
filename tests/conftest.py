"""Loaded by pytest automatically before any test runs (it is not a test itself).

1. Makes the step 01 and step 02 packages importable, plus tests/fakes.py.
2. Turns off the waiting between retries in step 02 for every test.

The tests only use small made-up texts: no data, internet, API key or GPU needed.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(REPO_ROOT / "01_human-data"),
    str(REPO_ROOT / "02_ai-generated-data"),
    str(REPO_ROOT / "10_humanizer-attack"),
    str(REPO_ROOT / "tests"),
]


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    """Retries in step 02 normally wait 2, 4, 8 ... seconds."""
    from ai_generation import generate

    monkeypatch.setattr(generate.time, "sleep", lambda seconds: None)
