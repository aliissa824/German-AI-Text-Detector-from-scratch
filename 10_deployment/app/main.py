"""FastAPI service: a web page at /, the API at /predict.

Run locally:  uvicorn app.main:app --port 7860
"""

import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from app.detector import LABELS, MAX_TOKENS, Detector

# Locally, HF_TOKEN and MODEL_ID can come from the .env file in the repo root (like the notebooks).
# On Hugging Face Spaces there is no .env; they are set as Space secrets/variables instead.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MAX_CHARS = 50_000   # about 7,000 words; longer texts are cut at 512 tokens anyway

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)   # hide one log line per Hugging Face request
log = logging.getLogger("detector")
STATIC = Path(__file__).parent / "static"

class PredictRequest(BaseModel):
    text: str = Field(..., max_length=MAX_CHARS, examples=["Die Ergebnisse der Studie zeigen, dass ..."])

    @field_validator("text")
    @classmethod
    def not_empty(cls, value):
        if not value.strip():
            raise ValueError("text is empty")
        return value


class PredictResponse(BaseModel):
    probabilities: dict[str, float]
    most_likely: str
    word_count: int
    tokens_read: int
    truncated: bool
    warnings: list[str]
    model: str


def create_app(load_detector=Detector):
    """load_detector is swapped for a fake one in the tests, so they run without downloading the model."""

    @asynccontextmanager
    async def lifespan(app):
        app.state.detector = load_detector()
        log.info(json.dumps({"event": "model_loaded", "model": app.state.detector.model_id,
                             "temperature": app.state.detector.temperature}))
        yield

    app = FastAPI(title="German academic AI-text detector", version="1.0", lifespan=lifespan)

    def get_detector(request: Request):
        return request.app.state.detector

    @app.get("/", include_in_schema=False)
    def page():
        return FileResponse(STATIC / "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/info")
    def info(detector=Depends(get_detector)):
        return {"model": detector.model_id, "labels": LABELS, "temperature": detector.temperature,
                "max_tokens": MAX_TOKENS, "max_chars": MAX_CHARS}

    # A plain `def` runs in FastAPI's thread pool, so a slow prediction doesn't block other requests
    @app.post("/predict", response_model=PredictResponse)
    def predict(body: PredictRequest, detector=Depends(get_detector)):
        start = time.perf_counter()
        result = detector.predict(body.text)
        # Monitoring: only numbers are logged, never the text
        log.info(json.dumps({"event": "predict", "words": result.word_count, "truncated": result.truncated,
                             "most_likely": result.most_likely,
                             "ms": round((time.perf_counter() - start) * 1000)}))
        return PredictResponse(**vars(result), model=detector.model_id)

    return app


app = create_app()
