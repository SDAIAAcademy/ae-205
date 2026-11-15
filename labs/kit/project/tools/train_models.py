"""Train the supplied models of the course on a laptop processor (run by the kit's setup).

    uv run python tools/train_models.py --data ../data --out ../models --notebook ../notebook

Writes the notebook's pickle and reference predictions, then four artefacts:
  farz-1.0.0    the notebook model exported (logistic regression, investigate at 0.30)
  farz-1.1.0    gradient boosting, investigate at 0.30: the canary of lab 4.1
  farz-1.2.0    the same model with investigate at 0.05 in its metadata, a typo for 0.50: the faulty release of lab 4.2
  shabih-1.0.0  the similar-claims encoder and an index of the 50,000 past claims
"""

from __future__ import annotations

import argparse
import json
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import skops.io as sio
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

from rifd import artefact

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "notebook"))
import train_triage as nb  # noqa: E402


def score(model: artefact.Model, inputs, truth) -> dict:
    pred = [p["label"] for p in model.predict(inputs)]
    return {"macro_f1": round(f1_score(truth, pred, average="macro"), 4),
            "investigate_recall": round(recall_score(truth, pred, labels=["investigate"], average="macro"), 4),
            "investigate_share": round(sum(p == "investigate" for p in pred) / len(pred), 4),
            "test_rows": len(truth)}


def references(pipe, decision, picks) -> list[dict]:
    tmp = artefact.Model(pipe, {"name": "x", "version": "0", "decision": decision}, Path("."))
    return [{"input": p, "label": o["label"]} for p, o in zip(picks, tmp.predict(picks))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../data")
    ap.add_argument("--out", default="../models")
    ap.add_argument("--notebook", default="../notebook")
    a = ap.parse_args()
    data, out, nbdir = Path(a.data), Path(a.out), Path(a.notebook)
    subprocess.run([sys.executable, str(HERE / "notebook" / "train_triage.py"), "--data", str(data), "--out", str(nbdir)], check=True)

    rows = nb.read_claims(data / "claims.csv")
    train_rows, test_rows = rows[:nb.TRAIN_ROWS], rows[nb.TRAIN_ROWS:]
    test_inputs = [nb.model_input(r) for r in test_rows]
    truth = [r["label"] for r in test_rows]
    picks = [test_inputs[i] for i in range(0, 10000, 1000)]
    training = {"file": "claims.csv", "sha256": artefact.sha256(data / "claims.csv"), "rows": nb.TRAIN_ROWS, "split": "first 40,000 claims by day"}

    with (nbdir / "farz_notebook.pkl").open("rb") as f:
        lr = pickle.load(f)
    d10 = {"investigate_threshold": nb.INVESTIGATE_AT}
    ref10 = json.loads((nbdir / "reference_predictions.json").read_text(encoding="utf-8"))
    p = artefact.export(lr, out / "farz-1.0.0", name="farz", version="1.0.0", decision=d10, training=training, metrics={}, reference=ref10)
    artefact.write_pins(p)
    m10 = artefact.load(p)
    meta = json.loads((p / "metadata.json").read_text(encoding="utf-8"))
    meta["metrics"] = score(m10, test_inputs, truth)
    (p / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    X = [artefact.features(nb.model_input(r)) for r in train_rows]
    y = [r["label"] for r in train_rows]
    hgb = make_pipeline(DictVectorizer(sparse=False), HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, random_state=0)).fit(X, y)
    for version, thr in (("1.1.0", 0.30), ("1.2.0", 0.05)):
        dec = {"investigate_threshold": thr}
        p = artefact.export(hgb, out / f"farz-{version}", name="farz", version=version, decision=dec, training=training,
                            metrics={}, reference=references(hgb, dec, picks))
        artefact.write_pins(p)
        m = artefact.load(p)
        meta = json.loads((p / "metadata.json").read_text(encoding="utf-8"))
        meta["metrics"] = score(m, test_inputs, truth)
        (p / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"farz {version}: {meta['metrics']}")
    print(f"farz 1.0.0: {json.loads((out / 'farz-1.0.0' / 'metadata.json').read_text(encoding='utf-8'))['metrics']}")

    hist = rows
    enc = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), min_df=3, max_features=30000),
                        TruncatedSVD(96, random_state=0), Normalizer())
    vecs = enc.fit_transform([r["description"] for r in hist]).astype(np.float32)
    sp = out / "shabih-1.0.0"
    sp.mkdir(parents=True, exist_ok=True)
    sio.dump(enc, sp / "model.skops")
    np.save(sp / "index.npy", vecs)
    items = [{"claim_id": r["claim_id"], "line": r["line"], "incident": r["incident"]} for r in hist]
    (sp / "items.json").write_text(json.dumps(items) + "\n", encoding="utf-8")
    (sp / "metadata.json").write_text(json.dumps({
        "name": "shabih", "version": "1.0.0", "dimensions": 96, "vectors": len(items),
        "sha256": {"model.skops": artefact.sha256(sp / "model.skops"), "index.npy": artefact.sha256(sp / "index.npy")},
        "training": {"file": "claims.csv", "rows": len(hist), "field": "description"}}, indent=2) + "\n", encoding="utf-8")
    print(f"shabih 1.0.0: {len(items)} vectors of 96 dimensions")


if __name__ == "__main__":
    main()
