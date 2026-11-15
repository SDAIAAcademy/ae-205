"""Reload an artefact in a clean environment and reproduce its ten reference predictions (lab 1.1).

Run it in an environment that holds only the artefact's pins. It imports rifd.artefact from src/,
which needs nothing beyond them:

    uv run --isolated --no-project --with-requirements artefacts/farz-1.0.0/requirements.txt python tools/check_reload.py artefacts/farz-1.0.0
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rifd import artefact  # noqa: E402


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "artefacts/farz-1.0.0"
    model = artefact.load(path, check_pins=True)
    wrong = model.check_reference()
    print(f"{model.name} {model.version} loaded with pinned versions; {10 - len(wrong)} of 10 reference predictions match")
    for item, got in zip(model.meta["reference"], model.predict([r["input"] for r in model.meta["reference"]])):
        mark = "ok " if item["label"] == got["label"] else "XX "
        print(f"  {mark}{item['input']['claim_id']}  expected {item['label']:<12} got {got['label']}")
    return 1 if wrong else 0


if __name__ == "__main__":
    raise SystemExit(main())
