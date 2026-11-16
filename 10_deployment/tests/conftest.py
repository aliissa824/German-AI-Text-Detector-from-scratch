import os

# The tests never need the internet: they use a fake model or a tiny one built on the fly.
# Offline mode makes sure nothing waits for a Hugging Face request (set before transformers is imported).
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
