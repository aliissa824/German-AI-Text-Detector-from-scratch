"""Detector tests with a tiny, randomly initialised model built on the fly.

This checks the real loading and prediction code (labels, calibration, truncation, warnings)
without downloading the real model, so it also runs in CI.
"""

import json

import pytest
from transformers import BertTokenizerFast, ModernBertConfig, ModernBertForSequenceClassification

from app.detector import LABELS, MAX_TOKENS, SHORT_TEXT_WORDS, Detector

WORDS = ["die", "der", "und", "studie", "zeigt", "dass", "ergebnisse", "text", "eine", "wird"]


def make_tiny_model(folder, labels=LABELS, temperature=2.5):
    vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", *WORDS]
    (folder / "vocab.txt").write_text("\n".join(vocab))
    tokenizer = BertTokenizerFast(vocab_file=str(folder / "vocab.txt"), do_lower_case=True)
    config = ModernBertConfig(
        vocab_size=len(vocab), hidden_size=32, intermediate_size=64, num_hidden_layers=2,
        num_attention_heads=2, max_position_embeddings=MAX_TOKENS, pad_token_id=0, cls_token_id=2,
        sep_token_id=3, bos_token_id=2, eos_token_id=3,
        num_labels=3, id2label=dict(enumerate(labels)), label2id={l: i for i, l in enumerate(labels)})
    ModernBertForSequenceClassification(config).save_pretrained(folder)
    tokenizer.save_pretrained(folder)
    if temperature is not None:
        (folder / "calibration.json").write_text(json.dumps({"temperature": temperature}))
    return str(folder)


@pytest.fixture(scope="module")
def detector(tmp_path_factory):
    return Detector(model_id=make_tiny_model(tmp_path_factory.mktemp("model")), device="cpu")


def test_loads_calibration(detector):
    assert detector.temperature == 2.5


def test_probabilities(detector):
    result = detector.predict(" ".join(WORDS * 10))
    assert set(result.probabilities) == set(LABELS)
    assert abs(sum(result.probabilities.values()) - 1) < 1e-3
    assert result.most_likely == max(result.probabilities, key=result.probabilities.get)
    assert result.word_count == 100
    assert not result.truncated
    assert result.warnings == []


def test_short_text_warning(detector):
    result = detector.predict("die studie zeigt")
    assert result.word_count == 3
    assert any(str(SHORT_TEXT_WORDS) in w for w in result.warnings)


def test_long_text_is_truncated(detector):
    result = detector.predict(" ".join(WORDS * 100))   # 1,000 words, 1,002 tokens
    assert result.truncated
    assert result.tokens_read == MAX_TOKENS
    assert any("only the first" in w for w in result.warnings)


def test_missing_calibration_means_no_scaling(tmp_path):
    assert Detector(model_id=make_tiny_model(tmp_path, temperature=None), device="cpu").temperature == 1.0


def test_wrong_label_order_is_refused(tmp_path):
    with pytest.raises(ValueError, match="Unexpected labels"):
        Detector(model_id=make_tiny_model(tmp_path, labels=["human", "ai_assisted", "ai_generated"]), device="cpu")



def test_clear_error_when_model_cannot_be_loaded():
    with pytest.raises(RuntimeError, match="Could not load the model"):
        Detector(model_id="someone/repo-that-does-not-exist", device="cpu")