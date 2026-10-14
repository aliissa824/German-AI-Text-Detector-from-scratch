[← 03 · Pangram check](../03_pangram-test/)

# 04 · Hugging Face dataset

Combines the human, AI-assisted and AI-generated texts into **one dataset with three labels**: 30,629 texts, checked and ready for training. It's kept private on Hugging Face (`aliissa824/german-academic-ai-text`).

## Output format

`data/hf-dataset/` holds the train, validation and test splits plus the dataset card. Every human text sits next to its two AI partners, which share its number in the `id`. Twelve real rows:

| id | label | source | word_count | generator_model | strategy | license_name |
|---|---|---|---|---|---|---|
| human-697 | human | ssoar | 41 | – | – | CC BY-SA |
| assisted-697 | ai_assisted | ssoar | 43 | gpt-5.6-luna | rewrite | CC BY-SA |
| generated-697 | ai_generated | ssoar | 38 | gpt-5.6-luna | source_based | CC BY-SA |
| human-2884 | human | ssoar | 152 | – | – | CC BY |
| assisted-2884 | ai_assisted | ssoar | 156 | gemini-3.8-flash | rewrite | CC BY |
| generated-2884 | ai_generated | ssoar | 145 | gemini-3.8-flash | source_based | CC BY |
| human-7164 | human | pedocs | 285 | – | – | CC BY |
| assisted-7164 | ai_assisted | pedocs | 296 | deepseek-flash | rewrite | CC BY |
| generated-7164 | ai_generated | pedocs | 276 | deepseek-flash | topics | CC BY |
| human-9857 | human | ssoar | 601 | – | – | CC BY-SA |
| assisted-9857 | ai_assisted | ssoar | 604 | gpt-6-luna | rewrite | CC BY-SA |
| generated-9857 | ai_generated | ssoar | 567 | gpt-6-luna | source_based | CC BY-SA |

Each row also has `text`, `seed_sample_id` (the human original of an AI row), `source_name`, `document_id`, `title`, `author`, `publication_year`, `document_type`, `license_url`, `source_url`, `target_length` and `generator_company`.

## Labels

| label | name | meaning |
|---|---|---|
| 0 | `human` | Original human-written text |
| 1 | `ai_generated` | A new text on the same topic, written by an AI model |
| 2 | `ai_assisted` | The human text, rewritten and polished by an AI model |

The label names are stored inside the dataset, so they show up when it's loaded. All models in steps 05–09 use this same order.

## Size

| split | human | ai_generated | ai_assisted | total |
|---|---|---|---|---|
| train | 8,342 | 8,324 | 8,320 | 24,986 |
| validation | 971 | 967 | 968 | 2,906 |
| test | 914 | 912 | 911 | 2,737 |
| **total** | **10,227** | **10,203** | **10,199** | **30,629** |

## What gets left out

- **Refusals:** 20 AI answers under 20 words (14 AI-assisted, 6 AI-generated), one-line refusals like "I'm sorry, but I cannot assist with that request."
- **One unchanged copy:** for sample 11, the model returned the human text unchanged as its "rewrite", so it would have been a human text labelled as AI.
- **Failed requests:** 13 AI-assisted and 18 AI-generated texts were never produced.

So 28 human texts have no AI-assisted partner and 24 no AI-generated one. The classes are still almost perfectly balanced.

## Checks before saving

- No source document appears in more than one split.
- Every AI text is in the same split as its human original.
- No two texts are identical.
- Every row has a licence and a source URL.

All checks pass.

## Licence and attribution

Every row keeps the author, title, licence and link of the original work, since CC BY and CC BY-SA require attribution. Because part of the human texts are CC BY-SA, the dataset is under **CC BY-SA 4.0**.

## How to run

Open `build_hf_dataset.ipynb` and run the cells. It saves the dataset to `data/hf-dataset/` and fills `dataset_card.md` (the text for the Hugging Face page) with the real counts.

To upload, set `HF_REPO_ID` in the first cell and `HF_TOKEN` in `.env`, then set `UPLOAD = True`. The dataset is uploaded as private.

---

[← 03 · Pangram check](../03_pangram-test/) -- [05 · Zero-shot LLM →](../05_zero-shot-llm/)