[← 09 · Model comparison](../09_model-comparison/)

# 10 · Deployment

The detector as a web app and an API: paste a German text, get three probabilities. It runs the fine-tuned **mmBERT-small** from step 07 (96.35% test accuracy). It's nearly as accurate as the biggest models, but small enough to run on a normal CPU.

**Live demo:** Hugging Face Space (link added once it's public)

## Output format

`POST /predict` with `{"text": "..."}` returns, for example:

```json
{
  "probabilities": {"human": 0.9512, "ai_generated": 0.0121, "ai_assisted": 0.0367},
  "most_likely": "human",
  "word_count": 312,
  "tokens_read": 498,
  "truncated": false,
  "warnings": [],
  "model": "aliissa824/german-academic-ai-text-mmbert-small"
}
```

Ten real texts from the test set, sent to the live demo:

| id | true label | words | human | ai_generated | ai_assisted | most likely | warning |
|---|---|---|---|---|---|---|---|
| *filled in by the last cell of `deploy_space.ipynb`* | | | | | | | |

## What it does

| Endpoint | |
|---|---|
| `GET /` | The web page |
| `POST /predict` | Three calibrated probabilities, plus warnings |
| `GET /info` | Model name, labels, temperature, limits |
| `GET /health` | For Docker and uptime checks |
| `GET /docs` | Interactive API docs (made by FastAPI) |

- **Probabilities, not verdicts.** The page shows three bars instead of a "this is AI" stamp. A detector that sounds sure of itself does more harm when it's wrong.
- **Calibrated.** The probabilities use the temperature from step 07, so the model's confidence matches how often it's actually right more closely (fitted on the validation set).
- **Honest warnings.** Under 70 words, accuracy drops clearly (TF-IDF in step 06: 78% vs. 93–95% for longer texts), so the API says so. Texts longer than 512 tokens are cut, as in training, and the API says how many words were read.
- **No texts are stored.** Each request logs only word count, predicted class and response time. A test checks that the text never reaches the log.

## Files

```
10_deployment/
├── app/
│   ├── detector.py        ← loads the model and calibration, makes predictions
│   ├── main.py            ← FastAPI app
│   └── static/index.html  ← the web page
├── tests/                 ← API tests (fake model) and detector tests (tiny random model)
├── Dockerfile
├── deploy_space.ipynb     ← uploads everything to Hugging Face Spaces
└── space_README.md        ← the Space's settings and description
```

The tests don't download the real model. The detector tests build a tiny random model with the same labels and a `calibration.json`, so they check the real loading code in a few seconds. They run on every push with GitHub Actions (`.github/workflows/tests.yml`), followed by a Docker build.

## How to run

**Locally** (from this folder):

```bash
pip install -r requirements-dev.txt
pytest                                          # 16 tests, about 15 seconds
uvicorn app.main:app --port 7860                # then open http://localhost:7860
```

While the model repo is private, put `HF_TOKEN` in your environment first. To try another model from step 07, set `MODEL_ID`, e.g. `MODEL_ID=aliissa824/german-academic-ai-text-xlm-roberta-base`.

**With Docker:**

```bash
docker build -t german-ai-text-detector .
docker run -p 7860:7860 -e HF_TOKEN=hf_... german-ai-text-detector
```

**On Hugging Face Spaces:** open `deploy_space.ipynb` and run the cells. It creates a Docker Space, uploads the app, and stores the token as a Space secret. Docker Spaces need a Hugging Face PRO account. The first build takes about 5–10 minutes.

**Quick public link for testing:** while the app is running, `cloudflared tunnel --url http://localhost:7860` prints a temporary public link. It works as long as the app and the tunnel are running.

---

[← 09 · Model comparison](../09_model-comparison/) -- [Back to overview →](../)
