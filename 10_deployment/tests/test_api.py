"""API tests with a fake detector: fast, and no model download needed."""

import pytest
from fastapi.testclient import TestClient

from app.detector import LABELS, Prediction
from app.main import MAX_CHARS, create_app


class FakeDetector:
    model_id = "fake/model"
    temperature = 2.0

    def predict(self, text):
        words = len(text.split())
        return Prediction(probabilities={"human": 0.7, "ai_generated": 0.1, "ai_assisted": 0.2},
                          most_likely="human", word_count=words, tokens_read=words + 2, truncated=False,
                          warnings=["Short text"] if words < 70 else [])


@pytest.fixture
def client():
    with TestClient(create_app(load_detector=FakeDetector)) as c:   # `with` runs the startup (model loading)
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "German AI-Text Detector" in response.text


def test_info(client):
    info = client.get("/info").json()
    assert info["model"] == "fake/model"
    assert info["labels"] == LABELS
    assert info["temperature"] == 2.0


def test_predict(client):
    response = client.post("/predict", json={"text": "Das ist ein kurzer Test."})
    assert response.status_code == 200
    data = response.json()
    assert set(data["probabilities"]) == set(LABELS)
    assert data["most_likely"] == "human"
    assert data["word_count"] == 5
    assert data["warnings"] == ["Short text"]
    assert data["model"] == "fake/model"


@pytest.mark.parametrize("body", [{}, {"text": ""}, {"text": "   \n "}, {"text": 123}, {"text": "x" * (MAX_CHARS + 1)}])
def test_bad_input_is_rejected(client, body):
    assert client.post("/predict", json=body).status_code == 422


def test_text_is_not_logged(client, caplog):
    secret = "Geheimer Satz, der nicht im Log landen darf."
    with caplog.at_level("INFO", logger="detector"):
        client.post("/predict", json={"text": secret})
    assert "predict" in caplog.text
    assert "Geheimer" not in caplog.text
