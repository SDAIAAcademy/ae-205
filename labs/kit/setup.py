"""Build the lab workspace of AE-205: the data, the supplied models and one folder per lab.

    uv run labs/kit/setup.py                      # builds rifd-labs/ beside the course folder
    uv run labs/kit/setup.py --to D:/rifd-labs    # somewhere else (keep the path short on Windows)
    uv run labs/kit/setup.py --only 2.1 --force   # rebuild one lab's folder from its start state

Standard library only. It runs the data generator and trains the models with uv inside the
workspace, so the models are made by the same library versions that serve them. Fixed seeds:
every participant gets the same claims and the same models. About two minutes on a laptop.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
PROJECT = KIT / "project"
sys.path.insert(0, str(KIT))
from states import STATES  # noqa: E402

SKIP = {".venv", "__pycache__", ".pytest-tmp", "runs", "artefacts", "registry", "secrets"}
LAB_KEY = "rifd-lookup-key-for-the-labs-only"


def copy_project(dest: Path) -> None:
    def ignore(_dir, names):
        return [n for n in names if n in SKIP]
    shutil.copytree(PROJECT, dest, ignore=ignore, dirs_exist_ok=True)


def run(cmd: list[str], cwd: Path) -> None:
    print("  $ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def apply(lab: str, dest: Path, ws: Path) -> None:
    state = STATES[lab]
    for rel, old, new in state.get("patch", []):
        f = dest / rel
        text = f.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit(f"state {lab}: the passage to change in {rel} occurs {text.count(old)} times; the kit is inconsistent")
        f.write_text(text.replace(old, new), encoding="utf-8")
    for rel, content in state.get("write", {}).items():
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        (dest / rel).write_text(content, encoding="utf-8")
    for rel, src in state.get("copy", {}).items():
        shutil.copyfile(KIT / src, dest / rel)
    (dest / "secrets").mkdir(exist_ok=True)
    (dest / "secrets" / "lookup.key").write_text(LAB_KEY + "\n", encoding="utf-8")
    for rel in state.get("remove", []):
        p = dest / rel
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    (dest / "models").mkdir(exist_ok=True)
    for m in state["models"]:
        shutil.copytree(ws / "models" / m, dest / "models" / m, dirs_exist_ok=True)
    (dest / "LAB").write_text(lab + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", default=str(KIT.parents[2] / "rifd-labs"))
    ap.add_argument("--only", action="append", help="a lab id such as 2.1; repeatable")
    ap.add_argument("--force", action="store_true", help="replace lab folders that exist")
    ap.add_argument("--rebuild-data", action="store_true", help="make the data and models again")
    a = ap.parse_args()
    ws = Path(a.to).resolve()
    ws.mkdir(parents=True, exist_ok=True)
    print(f"workspace: {ws}")
    base = ws / "_build"
    copy_project(base)
    if a.rebuild_data or not (ws / "models" / "shabih-1.0.0" / "metadata.json").is_file():
        print("making the data and training the models (about two minutes)")
        run(["uv", "run", "python", "tools/prepare_data.py", "--out", str(ws / "data")], base)
        run(["uv", "run", "python", "tools/train_models.py", "--data", str(ws / "data"), "--out", str(ws / "models"), "--notebook", str(ws / "notebook")], base)
    shutil.copyfile(KIT / "lab.py", ws / "lab.py")
    labs = a.only or list(STATES)
    for lab in labs:
        if lab not in STATES:
            raise SystemExit(f"no lab {lab}; the labs are {', '.join(STATES)}")
        dest = ws / lab
        if dest.exists():
            if not a.force:
                print(f"  {lab}: exists, kept (pass --force to start it again)")
                continue
            shutil.rmtree(dest, ignore_errors=os.name == "nt")
        copy_project(dest)
        apply(lab, dest, ws)
        print(f"  {lab}: ready in {dest}")
    print("done. Next: cd into a lab folder, read its page, and when you finish:  uv run ../lab.py check <lab>")


if __name__ == "__main__":
    main()
