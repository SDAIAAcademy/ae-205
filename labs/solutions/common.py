"""Shared steps of the solution scripts. Standard library only.

The workspace is $RIFD_LABS, or rifd-labs beside the course folder. Each solution starts its lab
again from the start state (setup.py --only <lab> --force), does the lab's steps, and ends with
the lab's own check, which must print PASS.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

SOLUTIONS = Path(__file__).resolve().parent
KIT = SOLUTIONS.parent / "kit"
PROJECT = KIT / "project"
FILES = SOLUTIONS / "files"
WS = Path(os.environ.get("RIFD_LABS", str(SOLUTIONS.parents[2] / "rifd-labs"))).resolve()


def say(msg: str) -> None:
    print(f"-- {msg}", flush=True)


def sh(cmd: list[str], cwd: Path, check: bool = True, env: dict | None = None, timeout: int = 900) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, **(env or {})}, timeout=timeout)
    out = (p.stdout + p.stderr).strip()
    if check and p.returncode != 0:
        raise SystemExit(f"FAILED ({p.returncode}): {' '.join(cmd)}\n{out[-2000:]}")
    return p.returncode, out


def fresh(lab: str) -> Path:
    say(f"lab {lab}: start again from the supplied state")
    sh(["uv", "run", str(KIT / "setup.py"), "--to", str(WS), "--only", lab, "--force"], cwd=WS.parent if WS.parent.exists() else Path.cwd())
    return WS / lab


def restore(lab_dir: Path, *rels: str) -> None:
    """Put the finished version of a file back (the passages the start state took out)."""
    for rel in rels:
        shutil.copyfile(PROJECT / rel, lab_dir / rel)


def put(lab_dir: Path, rel: str, src: str) -> None:
    (lab_dir / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FILES / src, lab_dir / rel)


def uv(lab_dir: Path, *args: str, check: bool = True, env: dict | None = None, timeout: int = 900) -> str:
    return sh(["uv", "run", "--quiet", *args], lab_dir, check=check, env=env, timeout=timeout)[1]


def _kill_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()


def wait_ready(port: int, proc: subprocess.Popen, path: str = "/readyz", timeout: float = 180) -> dict:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if proc.poll() is not None:
            raise SystemExit(f"the server on port {port} exited ({proc.returncode})")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3) as r:
                if r.status == 200:
                    return json.loads(r.read() or b"{}")
        except (urllib.error.URLError, ConnectionError, TimeoutError, ValueError):
            pass
        time.sleep(0.2)
    raise SystemExit(f"the server on port {port} was not ready in {timeout} s")


@contextmanager
def server(lab_dir: Path, port: int, env: dict | None = None, workers: int = 1, cmd: list[str] | None = None, ready_path: str = "/readyz"):
    """A background server in the lab folder, stopped (with its children) when the block ends."""
    cmd = cmd or ["python", "-m", "uvicorn", "rifd.app:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"] + (["--workers", str(workers)] if workers > 1 else [])
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    log = open(lab_dir / f"server_{port}.out", "w", encoding="utf-8")
    proc = subprocess.Popen(["uv", "run", "--quiet", *cmd], cwd=lab_dir, env={**os.environ, **(env or {})}, stdout=log, stderr=subprocess.STDOUT, **kw)
    try:
        info = wait_ready(port, proc, ready_path)
        if workers > 1:
            time.sleep(3)  # let every worker finish loading
        yield info
    finally:
        _kill_tree(proc)
        log.close()
        for _ in range(20):  # Windows releases the file a moment after the process tree ends
            try:
                (lab_dir / f"server_{port}.out").unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.5)


def post_json(url: str, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def check(lab: str) -> None:
    code, out = sh(["uv", "run", "--quiet", "../lab.py", "check", lab], WS / lab, check=False)
    print(out)
    if code != 0 or not out.rstrip().endswith("PASS"):
        raise SystemExit(f"lab {lab}: the check did not pass")
    say(f"lab {lab}: PASS")


def expect_fail(lab: str) -> None:
    """The start state must not pass its own check: the lab has something to do."""
    code, out = sh(["uv", "run", "--quiet", "../lab.py", "check", lab], WS / lab, check=False)
    if code == 0:
        raise SystemExit(f"lab {lab}: the start state already passes its check")
    todo = [x for x in out.splitlines() if "TODO" in x]
    say(f"lab {lab}: the start state fails its check as it should ({len(todo)} thing(s) to do)")


def write(lab_dir: Path, rel: str, content: str) -> None:
    (lab_dir / rel).parent.mkdir(parents=True, exist_ok=True)
    (lab_dir / rel).write_text(content, encoding="utf-8")
