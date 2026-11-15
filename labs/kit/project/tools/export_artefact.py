"""Turn the notebook's pickle into an artefact (lab 1.1).

    uv run python tools/export_artefact.py --pickle ../notebook/farz_notebook.pkl --out artefacts/farz-1.0.0

Load the pickle once, here, because you trust where it came from (Adel's notebook). Everything
downstream loads the skops file, which runs no code on load.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "notebook"))
from train_triage import INVESTIGATE_AT  # noqa: E402  the decision rule lives in the notebook today

from rifd import artefact  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pickle", default="../notebook/farz_notebook.pkl")
    ap.add_argument("--reference", default="../notebook/reference_predictions.json")
    ap.add_argument("--metrics", default="../notebook/notebook_metrics.json")
    ap.add_argument("--data", default="../data/claims.csv")
    ap.add_argument("--out", default="artefacts/farz-1.0.0")
    ap.add_argument("--version", default="1.0.0")
    a = ap.parse_args()

    with open(a.pickle, "rb") as f:
        pipeline = pickle.load(f)  # trusted source, loaded once

    # The decision rule is part of the model: without it the artefact predicts something else.
    decision = {"investigate_threshold": INVESTIGATE_AT}
    training = {"file": "claims.csv", "sha256": artefact.sha256(a.data), "rows": 40000, "split": "first 40,000 claims by day"}
    metrics = json.loads(Path(a.metrics).read_text(encoding="utf-8"))
    reference = json.loads(Path(a.reference).read_text(encoding="utf-8"))

    out = artefact.export(pipeline, a.out, name="farz", version=a.version, decision=decision,
                          training=training, metrics=metrics, reference=reference)
    artefact.write_pins(out)  # without pins, a fresh environment may load it with other versions
    model = artefact.load(out)
    wrong = model.check_reference()
    print(f"exported {out}: {10 - len(wrong)} of 10 reference predictions match" + (f"; differ: {wrong}" if wrong else ""))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
