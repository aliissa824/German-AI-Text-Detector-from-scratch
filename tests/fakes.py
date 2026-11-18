"""Shared test helpers: a fake AI model and small example texts (used by unit and integration tests)."""

HUMAN = " ".join(["Wort"] * 100)            # a 100-word human text
REWRITE = " ".join(["Neu"] * 95)
REFUSAL = "I'm sorry, but I cannot assist with that request."


def fake_model(*replies):
    """A fake model that gives these replies one after another and remembers what it was asked."""
    replies = list(replies)
    calls = []

    def complete(instructions, text):
        calls.append((instructions, text))
        return replies.pop(0)

    complete.calls = calls
    return complete
