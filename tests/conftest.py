"""Makes the step 01 and step 02 packages importable for the tests.

The tests only use small made-up texts: no data, internet, API key or GPU needed.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "01_human-data"), str(REPO_ROOT / "02_ai-generated-data")]
