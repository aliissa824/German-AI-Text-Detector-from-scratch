"""Loads the fine-tuned model from Hugging Face and turns a text into three calibrated probabilities."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEFAULT_MODEL_ID = "aliissa824/german-academic-ai-text-mmbert-small"
LABELS = ["human", "ai_generated", "ai_assisted"]   # same order as the dataset (step 04)
MAX_TOKENS = 512                                    # same as in training (step 07)
SHORT_TEXT_WORDS = 70                               # below this, all models in steps 06–07 get clearly worse


@dataclass
class Prediction:
    probabilities: dict
    most_likely: str
    word_count: int
    tokens_read: int
    truncated: bool
    warnings: list = field(default_factory=list)


class Detector:
    def __init__(self, model_id=None, token=None, device=None):
        self.model_id = model_id or os.getenv("MODEL_ID", DEFAULT_MODEL_ID)
        token = token or os.getenv("HF_TOKEN") or None   # only needed while the model repo is private
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, token=token)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_id, token=token)
        except Exception as error:   # e.g. 401 for a private repo without a token
            hint = "" if token else " No HF_TOKEN found: a private model repo needs one (in .env or as a Space secret)."
            raise RuntimeError(f"Could not load the model {self.model_id}.{hint}") from error
        self.model.to(self.device).eval()

        labels = [self.model.config.id2label[i] for i in range(self.model.config.num_labels)]
        if labels != LABELS:
            raise ValueError(f"Unexpected labels in {self.model_id}: {labels}, expected {LABELS}")

        self.temperature = self._load_temperature(token)

    def _load_temperature(self, token):
        """calibration.json is written by step 07. Without it, the raw probabilities are used (T = 1)."""
        local = Path(self.model_id) / "calibration.json"
        try:
            path = local if local.exists() else hf_hub_download(self.model_id, "calibration.json", token=token)
            return float(json.loads(Path(path).read_text())["temperature"])
        except Exception:
            return 1.0

    @torch.inference_mode()
    def predict(self, text):
        encoded = self.tokenizer(text, truncation=True, max_length=MAX_TOKENS, return_tensors="pt")
        full_length = len(self.tokenizer(text, truncation=False)["input_ids"])
        logits = self.model(**encoded.to(self.device)).logits[0].float().cpu()
        probs = torch.softmax(logits / self.temperature, dim=-1).tolist()

        word_count = len(text.split())
        tokens_read = int(encoded["input_ids"].shape[1])
        truncated = full_length > MAX_TOKENS

        warnings = []
        if word_count < SHORT_TEXT_WORDS:
            warnings.append(f"Short text ({word_count} words). Results under {SHORT_TEXT_WORDS} words "
                            "are much less reliable.")
        if truncated:
            words_read = len(self.tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True).split())
            warnings.append(f"Long text: only the first {MAX_TOKENS} tokens (about {words_read} words) were read.")

        return Prediction(
            probabilities={label: round(p, 4) for label, p in zip(LABELS, probs)},
            most_likely=LABELS[max(range(3), key=probs.__getitem__)],
            word_count=word_count,
            tokens_read=tokens_read,
            truncated=truncated,
            warnings=warnings,
        )
