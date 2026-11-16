---
title: German AI-Text Detector
emoji: 🔎
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: cc-by-sa-4.0
short_description: Human, AI-generated or AI-assisted? For German academic text
models:
- aliissa824/german-academic-ai-text-mmbert-small
datasets:
- aliissa824/german-academic-ai-text
---

# German AI-Text Detector

Paste a German academic text and get three probabilities: **human**, **AI-generated**, or **AI-assisted**
(written by a human, then polished by AI).

The model is [mmBERT-small](https://huggingface.co/aliissa824/german-academic-ai-text-mmbert-small),
fine-tuned on about 25,000 German academic texts. On the test set it gets 96.35% right.

These are probabilities, not proof. Short texts (under 70 words) and texts outside academic German are
much less reliable. Texts are not stored.

API: `POST /predict` with `{"text": "..."}`. Docs at `/docs`.
