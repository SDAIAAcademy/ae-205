"""Send claims from a file to the service at a steady rate and record every answer.

    uv run python tools/replay.py --file ../data/replay/week1.csv --url http://127.0.0.1:8000 --rate 40 --out runs/week1.jsonl

Each line of the output: claim id, status, latency in ms measured by the caller, the version that
answered and the label. Requests leave on a fixed schedule (an open load): a slow answer does not
delay the next request. The input files hold personal fields, as the real claims system would send.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import claims  # noqa: E402

_local = threading.local()


def _client(url: str) -> httpx.Client:
    if not hasattr(_local, "client"):
        _local.client = httpx.Client(base_url=url, timeout=10.0)
    return _local.client


def replay(rows: list[dict], url: str, rate: float, out: Path, path: str = "/v1/triage", threads: int = 64) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    results: list[dict] = []
    sink = out.open("w", encoding="utf-8")

    def keep(rec: dict) -> None:
        with lock:
            results.append(rec)
            sink.write(json.dumps(rec) + "\n")
            sink.flush()

    def one(row: dict) -> None:
        start = time.perf_counter()
        try:
            r = _client(url).post(path, json=claims.request_body(row))
            ms = (time.perf_counter() - start) * 1000
            body = r.json() if r.headers.get("content-type", "").startswith("application/") else {}
            version = r.headers.get("x-rifd-version") or (body.get("model") or {}).get("version")
            keep({"claim_id": row["claim_id"], "status": r.status_code, "ms": round(ms, 2),
                  "version": version, "label": body.get("label"), "type": body.get("type")})
        except httpx.HTTPError as e:
            keep({"claim_id": row["claim_id"], "status": 0, "ms": None, "version": None, "label": None, "type": type(e).__name__})

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=threads) as pool:
        for i, row in enumerate(rows):
            delay = start + i / rate - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            pool.submit(one, row)
    elapsed = time.perf_counter() - start
    sink.close()
    ok = sum(r["status"] == 200 for r in results)
    return {"sent": len(rows), "ok": ok, "seconds": round(elapsed, 1), "achieved_rps": round(len(rows) / elapsed, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--rate", type=float, default=40)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = claims.read(a.file, a.limit)
    print(json.dumps(replay(rows, a.url, a.rate, Path(a.out))))


if __name__ == "__main__":
    main()
