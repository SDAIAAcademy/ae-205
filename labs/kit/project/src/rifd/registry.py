"""A model registry in a folder: immutable versions, metrics, tags and aliases.

    uv run python -m rifd.registry register --name farz --version 1.0.0 --from models/farz-1.0.0 --tag data_sha256=<hash>
    uv run python -m rifd.registry alias --name farz --alias champion --version 1.0.0
    uv run python -m rifd.registry show --name farz
    uv run python -m rifd.registry load --name farz --ref champion      (or --ref 1.0.0)

The same ideas in MLflow: a registered model, model versions, tags and aliases (models:/farz@champion).
In a git repository of artefacts: one tag per version, never moved, and a file that maps aliases to tags.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from rifd import artefact

DEFAULT_ROOT = "registry"


class RegistryError(Exception):
    pass


class Registry:
    def __init__(self, root: str | Path = DEFAULT_ROOT):
        self.root = Path(root)
        self.index_file = self.root / "registry.json"

    def _read(self) -> dict[str, Any]:
        if not self.index_file.is_file():
            return {"models": {}}
        return json.loads(self.index_file.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def register(self, name: str, version: str, source: str | Path, tags: dict[str, str] | None = None) -> dict[str, Any]:
        source = Path(source)
        data = self._read()
        entry = data["models"].setdefault(name, {"versions": {}, "aliases": {}})
        if version in entry["versions"]:
            raise RegistryError(f"{name} {version} is already registered and versions never change: register {name} with a new version")
        model = artefact.load(source)  # refuses an altered or unreviewed artefact
        if model.name != name or model.version != version:
            raise RegistryError(f"the artefact says {model.name} {model.version}, not {name} {version}")
        target = self.root / "store" / name / version
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        record = {
            "path": target.relative_to(self.root).as_posix(),
            "sha256": model.meta["sha256"],
            "metrics": model.meta.get("metrics", {}),
            "tags": dict(tags or {}),
            "order": len(entry["versions"]) + 1,
        }
        entry["versions"][version] = record
        self._write(data)
        return record

    def set_alias(self, name: str, alias: str, version: str) -> None:
        data = self._read()
        entry = data["models"].get(name)
        if not entry or version not in entry["versions"]:
            raise RegistryError(f"{name} {version} is not registered")
        if alias[0].isdigit():
            raise RegistryError("an alias is a word such as champion, not a version number")
        entry["aliases"][alias] = version
        self._write(data)

    def resolve(self, name: str, ref: str) -> str:
        entry = self._read()["models"].get(name)
        if not entry:
            raise RegistryError(f"no model called {name}")
        if ref in entry["versions"]:
            return ref
        if ref in entry["aliases"]:
            return entry["aliases"][ref]
        raise RegistryError(f"{name} has no version or alias {ref}")

    def load(self, name: str, ref: str) -> artefact.Model:
        version = self.resolve(name, ref)
        record = self._read()["models"][name]["versions"][version]
        model = artefact.load(self.root / record["path"])
        if model.meta["sha256"] != record["sha256"]:
            raise RegistryError("the stored artefact differs from the one registered")
        return model

    def show(self, name: str) -> dict[str, Any]:
        entry = self._read()["models"].get(name)
        if not entry:
            raise RegistryError(f"no model called {name}")
        return entry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m rifd.registry")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register")
    r.add_argument("--name", required=True)
    r.add_argument("--version", required=True)
    r.add_argument("--from", dest="source", required=True)
    r.add_argument("--tag", action="append", default=[], help="key=value, repeatable")
    a = sub.add_parser("alias")
    a.add_argument("--name", required=True)
    a.add_argument("--alias", required=True)
    a.add_argument("--version", required=True)
    s = sub.add_parser("show")
    s.add_argument("--name", required=True)
    lo = sub.add_parser("load")
    lo.add_argument("--name", required=True)
    lo.add_argument("--ref", required=True)
    args = ap.parse_args(argv)
    reg = Registry(args.root)
    try:
        if args.cmd == "register":
            tags = dict(t.split("=", 1) for t in args.tag)
            rec = reg.register(args.name, args.version, args.source, tags)
            print(f"registered {args.name} {args.version}: sha256 {rec['sha256'][:12]}, metrics {rec['metrics']}, tags {rec['tags']}")
        elif args.cmd == "alias":
            reg.set_alias(args.name, args.alias, args.version)
            print(f"{args.name}@{args.alias} -> {args.version}")
        elif args.cmd == "show":
            print(json.dumps(reg.show(args.name), indent=2, ensure_ascii=False))
        elif args.cmd == "load":
            model = reg.load(args.name, args.ref)
            wrong = model.check_reference()
            print(f"loaded {model.name} {model.version} from {args.name}@{args.ref}; reference predictions: {10 - len(wrong)} of 10 match")
    except (RegistryError, artefact.ArtefactError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
