"""Start a service, time how long it takes to become ready, and measure its memory (lab 2.4).

    uv run python tools/measure.py --service farz
    uv run python tools/measure.py --service shabih --requests 200

Memory is the resident set size of the server and its worker processes, in MiB, after start-up and
again after some requests. Time to ready runs from starting the process to the first 200 from /readyz.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

import psutil

LAST_READY: dict = {}


def start(service: str, port: int, workers: int = 1, env: dict | None = None, log_file: str | None = None) -> subprocess.Popen:
    e = {**os.environ, "RIFD_SERVICE": service, **(env or {})}
    cmd = [sys.executable, "-m", "uvicorn", "rifd.app:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"]
    if workers > 1:
        cmd += ["--workers", str(workers)]
    out = open(log_file, "w", encoding="utf-8") if log_file else subprocess.DEVNULL
    return subprocess.Popen(cmd, env=e, stdout=out, stderr=subprocess.STDOUT)


def wait_ready(port: int, proc: subprocess.Popen, timeout: float = 120) -> float:
    """Seconds until /readyz answers 200; the body (load_ms, warm_ms) is kept in LAST_READY."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError(f"the server exited with code {proc.returncode}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/readyz", timeout=2) as r:
                if r.status == 200:
                    LAST_READY.update(json.loads(r.read()))
                    return time.perf_counter() - t0
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(0.05)
    raise TimeoutError("not ready in time")


def rss_mib(proc: subprocess.Popen) -> float:
    p = psutil.Process(proc.pid)
    total = p.memory_info().rss
    for c in p.children(recursive=True):
        try:
            total += c.memory_info().rss
        except psutil.NoSuchProcess:
            pass
    return round(total / 2**20, 1)


def stop(proc: subprocess.Popen) -> None:
    try:
        parent = psutil.Process(proc.pid)
        for c in parent.children(recursive=True):
            c.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        pass
    proc.wait(timeout=10)


def post(port: int, path: str, body: dict) -> int:
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


FARZ_BODY = {"claim_id": "CLM-050001", "line": "motor", "region": "riyadh", "channel": "app", "amount_sar": 4200.0,
             "policy_tenure_months": 30, "prior_claims_12m": 0, "days_to_report": 1, "vehicle_age_years": 5, "police_report": True}
SHABIH_BODY = {"description": "Windscreen cracked by a stone on the highway", "k": 5}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--service", choices=["farz", "shabih"], required=True)
    ap.add_argument("--port", type=int, default=8010)
    ap.add_argument("--requests", type=int, default=200)
    a = ap.parse_args()
    proc = start(a.service, a.port)
    try:
        ready = wait_ready(a.port, proc)
        rss_ready = rss_mib(proc)
        path, body = ("/v1/similar", SHABIH_BODY) if a.service == "shabih" else ("/v1/triage", FARZ_BODY)
        t0 = time.perf_counter()
        codes = [post(a.port, path, body) for _ in range(a.requests)]
        per = (time.perf_counter() - t0) / a.requests * 1000
        print(json.dumps({"service": a.service, "ready_s": round(ready, 2), "load_ms": LAST_READY.get("load_ms"), "rss_ready_mib": rss_ready,
                          "rss_after_mib": rss_mib(proc), "requests": a.requests, "ok": codes.count(200),
                          "mean_ms_one_at_a_time": round(per, 2)}))
    finally:
        stop(proc)


if __name__ == "__main__":
    main()
