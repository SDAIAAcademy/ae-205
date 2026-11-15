"""Shabih, the similar-claims model: a text encoder and an index of past claims held in memory.

An artefact folder holds:
  model.skops     the encoder (character n-gram TF-IDF, then SVD to 96 dimensions, then unit length)
  index.npy       one unit vector per past claim, float32
  items.json      claim id, line and incident type of each vector: no personal field, no free text
  metadata.json   name, version, sha256 of the two files
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import skops.io as sio

from rifd.artefact import ArtefactError, sha256


class SimilarModel:
    def __init__(self, path: str | Path):
        path = Path(path)
        meta_file = path / "metadata.json"
        if not meta_file.is_file():
            raise ArtefactError(f"no similar-claims artefact at {path}")
        self.meta = json.loads(meta_file.read_text(encoding="utf-8"))
        for name in ("model.skops", "index.npy"):
            if sha256(path / name) != self.meta["sha256"][name]:
                raise ArtefactError(f"{name} does not match metadata.json")
        untrusted = sio.get_untrusted_types(file=path / "model.skops")
        if untrusted:
            raise ArtefactError(f"unreviewed types in the encoder: {untrusted}")
        self.encoder = sio.load(path / "model.skops")
        self.index = np.load(path / "index.npy")
        self.items = json.loads((path / "items.json").read_text(encoding="utf-8"))
        self.lines = np.array([it["line"] for it in self.items])
        self.name, self.version = self.meta["name"], self.meta["version"]

    def search(self, text: str, k: int = 5, line: str | None = None) -> list[dict]:
        q = self.encoder.transform([text]).astype(np.float32)[0]
        scores = self.index @ q
        if line:
            scores = np.where(self.lines == line, scores, -1.0)
        top = np.argpartition(-scores, k)[:k]
        top = top[np.argsort(-scores[top])]
        return [{**self.items[i], "score": round(float(scores[i]), 4)} for i in top]
