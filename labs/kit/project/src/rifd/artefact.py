"""A model artefact: the model file, its signature, its decision rule, its pins and its proof.

An artefact folder holds:
  model.skops        the fitted scikit-learn pipeline, saved with skops (no code runs on load)
  signature.json     the input fields with their types and the outputs
  metadata.json      name, version, decision rule, training data hash, metrics, sha256 of the model file,
                     ten reference inputs with the predictions the notebook made for them
  requirements.txt   the exact versions of the libraries that load it (write_pins)
"""

from __future__ import annotations

import hashlib
import json
import math
from importlib import metadata as md
from pathlib import Path
from typing import Any

import skops.io as sio

LABELS = ["fast_track", "standard", "investigate"]
CATEGORICAL = {
    "line": ["motor", "health", "property"],
    "region": ["riyadh", "makkah", "eastern", "madinah", "qassim", "asir"],
    "channel": ["app", "branch", "broker"],
}
NUMERIC = ["amount_sar", "policy_tenure_months", "prior_claims_12m", "days_to_report", "vehicle_age_years"]
FLAGS = ["police_report", "in_network"]
PINNED = ["scikit-learn", "numpy", "scipy", "skops", "joblib", "threadpoolctl"]
# Types skops does not trust by default that this project has reviewed and accepts.
REVIEWED_TYPES = {"sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"}

SIGNATURE = {
    "inputs": (
        [{"name": k, "type": "string", "enum": v, "required": True} for k, v in CATEGORICAL.items()]
        + [{"name": "amount_sar", "type": "number", "required": True},
           {"name": "policy_tenure_months", "type": "integer", "required": True},
           {"name": "prior_claims_12m", "type": "integer", "required": True},
           {"name": "days_to_report", "type": "integer", "required": True},
           {"name": "vehicle_age_years", "type": "integer", "required": False, "note": "motor only"},
           {"name": "police_report", "type": "boolean", "required": False, "note": "motor only"},
           {"name": "in_network", "type": "boolean", "required": False, "note": "health only"}]
    ),
    "outputs": {"label": {"type": "string", "enum": LABELS}, "probabilities": {"type": "object", "keys": LABELS}},
}


class ArtefactError(Exception):
    """The artefact is missing, altered or cannot be loaded."""


def features(claim: dict[str, Any]) -> dict[str, Any]:
    """The model's view of a claim. Shared by training and serving, so both see the same features."""
    out: dict[str, Any] = {}
    for k in CATEGORICAL:
        out[k] = str(claim[k])
    for k in NUMERIC:
        v = claim.get(k)
        if v is None or v == "":
            continue
        out[k] = float(v)
    out["amount_log"] = math.log1p(float(claim["amount_sar"]))
    for k in FLAGS:
        v = claim.get(k)
        if v is None or v == "":
            continue
        out[k] = 1.0 if v in (True, 1, "1", "true", "True") else 0.0
    return out


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pins() -> list[str]:
    return [f"{name}=={md.version(name)}" for name in PINNED]


def decide(proba: dict[str, float], decision: dict[str, Any]) -> str:
    """The decision rule: investigate when its probability reaches the threshold, else the most likely label."""
    threshold = decision.get("investigate_threshold")
    if threshold is not None and proba["investigate"] >= threshold:
        return "investigate"
    return max(proba, key=proba.get)


class Model:
    def __init__(self, pipeline: Any, meta: dict[str, Any], path: Path):
        self.pipeline = pipeline
        self.meta = meta
        self.path = path
        self.name = meta["name"]
        self.version = meta["version"]
        self.decision = meta.get("decision", {})
        self.classes = [str(c) for c in pipeline.classes_]

    def predict(self, claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = self.pipeline.predict_proba([features(c) for c in claims])
        out = []
        for row in rows:
            proba = {c: round(float(p), 6) for c, p in zip(self.classes, row)}
            out.append({"label": decide(proba, self.decision), "probabilities": proba})
        return out

    def check_reference(self) -> list[str]:
        """Predict the reference inputs and return the claim ids whose label differs."""
        ref = self.meta.get("reference", [])
        got = self.predict([r["input"] for r in ref])
        return [r["input"].get("claim_id", str(i)) for i, (r, g) in enumerate(zip(ref, got)) if r["label"] != g["label"]]


def write_pins(out: str | Path) -> Path:
    """requirements.txt: the exact version of every library that loading the model needs, from this environment."""
    path = Path(out) / "requirements.txt"
    path.write_text("\n".join(pins()) + "\n", encoding="utf-8")
    return path


def export(pipeline: Any, out: str | Path, *, name: str, version: str, decision: dict[str, Any],
           training: dict[str, Any], metrics: dict[str, float], reference: list[dict[str, Any]]) -> Path:
    """Write an artefact folder. `reference` holds {"input": claim, "label": expected label} items."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    model_file = out / "model.skops"
    sio.dump(pipeline, model_file)
    (out / "signature.json").write_text(json.dumps(SIGNATURE, indent=2) + "\n", encoding="utf-8")
    meta = {
        "name": name, "version": version, "format": "skops",
        "sha256": sha256(model_file), "decision": decision, "training": training,
        "metrics": metrics, "labels": LABELS, "reference": reference,
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def load(path: str | Path, *, check_pins: bool = False) -> Model:
    path = Path(path)
    model_file = path / "model.skops"
    meta_file = path / "metadata.json"
    if not model_file.is_file() or not meta_file.is_file():
        raise ArtefactError(f"no artefact at {path}: model.skops and metadata.json are both needed")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    if sha256(model_file) != meta.get("sha256"):
        raise ArtefactError("model.skops does not match the sha256 in metadata.json: the file was altered or replaced")
    untrusted = set(sio.get_untrusted_types(file=model_file))
    unknown = untrusted - REVIEWED_TYPES
    if unknown:
        raise ArtefactError(f"model.skops holds types nobody has reviewed: {sorted(unknown)}")
    if check_pins:
        if not (path / "requirements.txt").is_file():
            raise ArtefactError("no requirements.txt: nothing says which library versions load this model")
        wanted = (path / "requirements.txt").read_text(encoding="utf-8").split()
        have = set(pins())
        differ = [w for w in wanted if w not in have]
        if differ:
            raise ArtefactError(f"this environment differs from the artefact's pins: {differ}")
    pipeline = sio.load(model_file, trusted=sorted(untrusted))
    return Model(pipeline, meta, path)
