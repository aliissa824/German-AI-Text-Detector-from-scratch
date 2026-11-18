"""Behavioral tests: how the real trained model reacts to small changes in a text.

Like the CheckList method:
- INV (invariance): changes that shouldn't matter must not change the result
- DIR (direction):  a change with a known effect must push the result the right way

These tests download mmBERT-small from the Hugging Face Hub (about 0.5 GB), so they
are skipped in a normal `pytest` run and in CI. Run them with:

    pytest -m behavioral

Another model can be tested with:  BEHAVIOR_MODEL=<hugging face repo> pytest -m behavioral
"""

import os

import pytest

from humanizer import formalize

pytestmark = pytest.mark.behavioral

MODEL = os.getenv("BEHAVIOR_MODEL", "aliissa824/german-academic-ai-text-mmbert-small")
TOLERANCE = 0.05     # how much a probability may move for a change that shouldn't matter

PLAIN = (
    "Für die Studie haben wir 2019 zwölf Lehrkräfte an Grundschulen in Leipzig befragt. Die meisten nutzen "
    "die Lernplattform vor allem, um Arbeitsblätter zu verteilen. Gemeinsames Arbeiten kommt dagegen kaum vor, "
    "auch weil Fortbildungen fehlen und die Technik oft nicht funktioniert. Frau Becker sagte z. B., dass sie "
    "die Plattform nur nutzt, wenn es sein muss. Das zeigt, wie wichtig gute Unterstützung für die Schulen ist."
)
FORMAL = (
    "Die vorliegende Untersuchung verdeutlicht, dass digitale Lernplattformen an Grundschulen bislang "
    "insbesondere zur Bereitstellung von Arbeitsmaterialien eingesetzt werden. Kooperative Funktionen spielen "
    "hingegen lediglich eine untergeordnete Rolle. Als zentrale Ursachen lassen sich fehlende Fortbildungsangebote "
    "sowie eine unzureichende technische Ausstattung identifizieren. Zugleich unterstreichen die Befunde die "
    "entscheidende Bedeutung einer systematischen Unterstützung der Schulen."
)


@pytest.fixture(scope="module")
def classify():
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL)
    model = transformers.AutoModelForSequenceClassification.from_pretrained(MODEL).eval()

    @torch.inference_mode()
    def run(text):
        encoded = tokenizer(text, truncation=True, max_length=512, return_tensors="pt")
        probs = torch.softmax(model(**encoded).logits[0], dim=-1).tolist()
        return {"human": probs[0], "ai_generated": probs[1], "ai_assisted": probs[2]}

    return run


def p_ai(probs):
    return probs["ai_generated"] + probs["ai_assisted"]


def most_likely(probs):
    return max(probs, key=probs.get)


@pytest.mark.parametrize("text", [PLAIN, FORMAL], ids=["plain", "formal"])
@pytest.mark.parametrize(
    "change",
    [
        lambda t: t.replace(". ", ".  "),                          # double spaces
        # line breaks: no human text in the dataset has one, so the model learned them as an AI signal
        pytest.param(lambda t: t.replace(". ", ".\n", 2),
                     marks=pytest.mark.xfail(reason="known weakness: line breaks push a human text towards AI")),
        lambda t: t.replace("„", '"').replace("“", '"'),           # quote style
        lambda t: t.replace("2019", "2018").replace("zwölf", "elf"),   # numbers
        lambda t: t.replace("Leipzig", "Bremen").replace("Becker", "Yilmaz"),   # names and places
    ],
    ids=["double-spaces", "line-breaks", "quotes", "numbers", "names"],
)
def test_inv_small_changes_dont_matter(classify, text, change):
    before, after = classify(text), classify(change(text))
    assert most_likely(after) == most_likely(before)
    assert abs(p_ai(after) - p_ai(before)) <= TOLERANCE


def test_dir_formal_wording_does_not_make_a_text_look_more_human(classify):
    before, after = classify(PLAIN), classify(formalize(PLAIN)[0])
    assert p_ai(after) >= p_ai(before) - TOLERANCE


def test_dir_formal_text_looks_more_like_ai_than_plain_text(classify):
    assert p_ai(classify(FORMAL)) > p_ai(classify(PLAIN))


def test_probabilities_add_up_to_one(classify):
    assert abs(sum(classify(PLAIN).values()) - 1) < 1e-4