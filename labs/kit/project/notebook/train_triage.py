"""Adel's training notebook for Farz, exported as a script. It is the hand-over you start from.

    uv run python notebook/train_triage.py --data ../data --out notebook

It trains the claims-triage model on the first 40,000 claims (by day), scores it on the last
10,000, and pickles the fitted pipeline. The cell near the end that turns probabilities into a
label is how the claims team has used the model in its weekly review.
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
from pathlib import Path

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from rifd.artefact import features  # moved into the package so that training and serving share it

TRAIN_ROWS = 40000


def read_claims(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def model_input(row: dict) -> dict:
    """The fields the model needs, typed, from a CSV row."""
    out = {k: row[k] for k in ("claim_id", "line", "region", "channel")}
    out["amount_sar"] = float(row["amount_sar"])
    for k in ("policy_tenure_months", "prior_claims_12m", "days_to_report"):
        out[k] = int(row[k])
    out["vehicle_age_years"] = int(row["vehicle_age_years"]) if row["vehicle_age_years"] != "" else None
    out["police_report"] = bool(int(row["police_report"])) if row["police_report"] != "" else None
    out["in_network"] = bool(int(row["in_network"])) if row["in_network"] != "" else None
    return out


def train(rows: list[dict]):
    X = [features(model_input(r)) for r in rows]
    y = [r["label"] for r in rows]
    pipe = make_pipeline(DictVectorizer(), StandardScaler(with_mean=False), LogisticRegression(max_iter=2000, C=1.0))
    return pipe.fit(X, y)


# Cell 14: the claims team reviews anything with a 30% chance of needing investigation.
INVESTIGATE_AT = 0.30


def label_from(proba: dict[str, float]) -> str:
    if proba["investigate"] >= INVESTIGATE_AT:
        return "investigate"
    return max(proba, key=proba.get)


def predict_labels(pipe, inputs: list[dict]) -> list[str]:
    rows = pipe.predict_proba([features(i) for i in inputs])
    return [label_from(dict(zip(pipe.classes_, map(float, r)))) for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data")
    ap.add_argument("--out", default="notebook")
    a = ap.parse_args()
    rows = read_claims(Path(a.data) / "claims.csv")
    train_rows, test_rows = rows[:TRAIN_ROWS], rows[TRAIN_ROWS:]
    pipe = train(train_rows)
    test_inputs = [model_input(r) for r in test_rows]
    pred = predict_labels(pipe, test_inputs)
    truth = [r["label"] for r in test_rows]
    f1 = f1_score(truth, pred, average="macro")
    rec = recall_score(truth, pred, labels=["investigate"], average="macro")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "farz_notebook.pkl").open("wb") as f:
        pickle.dump(pipe, f)
    picks = [test_inputs[i] for i in range(0, 10000, 1000)]
    labels = predict_labels(pipe, picks)
    ref = [{"input": p, "label": lab} for p, lab in zip(picks, labels)]
    (out / "reference_predictions.json").write_text(json.dumps(ref, indent=2) + "\n", encoding="utf-8")
    (out / "notebook_metrics.json").write_text(json.dumps({"macro_f1": round(f1, 4), "investigate_recall": round(rec, 4),
                                                         "test_rows": len(test_rows)}, indent=2) + "\n", encoding="utf-8")
    print(f"macro F1 {f1:.3f}, investigate recall {rec:.3f} on {len(test_rows)} held-out claims; pickled to {out / 'farz_notebook.pkl'}")


if __name__ == "__main__":
    main()
