"""A traffic splitter for canary and shadow releases on a laptop (labs 4.1 and 4.2).

    uv run python tools/router.py --stable http://127.0.0.1:8001 --canary http://127.0.0.1:8002 --weight 0.10 --port 8000
    curl -X POST http://127.0.0.1:8000/admin/weight -H "content-type: application/json" -d '{"canary": 0}'

A claim always goes to the same version (the split hashes the claim id), so a caller who retries
sees one answer. --shadow sends every request to the stable version and a copy to the canary,
whose answer is recorded and thrown away. On a cluster the same split is two Deployments behind
one Service with replicas in the ratio you want, or a weighted route of a gateway.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response
from starlette.concurrency import run_in_threadpool

STATE = {"stable": "", "canary": "", "weight": 0.0, "shadow": False, "events": "runs/router_events.jsonl", "t0": time.monotonic()}


def event(kind: str, **data) -> None:
    Path(STATE["events"]).parent.mkdir(parents=True, exist_ok=True)
    with open(STATE["events"], "a", encoding="utf-8") as f:
        f.write(json.dumps({"after_s": round(time.monotonic() - STATE["t0"], 1), "event": kind, **data}) + "\n")


def to_canary(claim_id: str) -> bool:
    bucket = int(hashlib.sha256(claim_id.encode()).hexdigest()[:8], 16) % 10000
    return bucket < STATE["weight"] * 10000


# One synchronous client per thread: on some Windows laptops httpx's asynchronous client adds
# hundreds of milliseconds under load, which would make the router, not the model, the slow part.
_local = threading.local()
_shadow_pool = ThreadPoolExecutor(max_workers=16)
_write = threading.Lock()


def _client() -> httpx.Client:
    if not hasattr(_local, "client"):
        _local.client = httpx.Client(timeout=10.0)
    return _local.client


def _forward(target: str, raw: bytes) -> httpx.Response:
    return _client().post(target + "/v1/triage", content=raw, headers={"content-type": "application/json"})


@asynccontextmanager
async def lifespan(_app):
    event("start", stable=STATE["stable"], canary=STATE["canary"], weight=STATE["weight"], shadow=STATE["shadow"])
    yield
    _shadow_pool.shutdown(wait=False)


app = FastAPI(title="Rifd release router", lifespan=lifespan)


@app.post("/admin/weight")
async def set_weight(request: Request):
    body = await request.json()
    old = STATE["weight"]
    STATE["weight"] = max(0.0, min(1.0, float(body["canary"])))
    event("weight", before=old, after=STATE["weight"], reason=body.get("reason", ""))
    return {"canary": STATE["weight"]}


@app.get("/admin/state")
async def state():
    return {k: STATE[k] for k in ("stable", "canary", "weight", "shadow")}


@app.post("/v1/triage")
async def triage(request: Request):
    raw = await request.body()
    try:
        claim_id = json.loads(raw).get("claim_id", "")
    except (ValueError, AttributeError):
        claim_id = ""
    if STATE["shadow"] and STATE["canary"]:
        _shadow_pool.submit(_shadow, raw)
        target, name = STATE["stable"], "stable"
    elif STATE["canary"] and to_canary(claim_id):
        target, name = STATE["canary"], "canary"
    else:
        target, name = STATE["stable"], "stable"
    r = await run_in_threadpool(_forward, target, raw)
    out = Response(r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))
    out.headers["X-Rifd-Route"] = name
    try:
        out.headers["X-Rifd-Version"] = r.json().get("model", {}).get("version", name)
    except ValueError:
        out.headers["X-Rifd-Version"] = name
    return out


def _shadow(raw: bytes) -> None:
    start = time.perf_counter()
    try:
        r = _forward(STATE["canary"], raw)
        body = r.json()
        rec = {"status": r.status_code, "ms": round((time.perf_counter() - start) * 1000, 2),
               "version": body.get("model", {}).get("version"), "label": body.get("label"), "claim_id": json.loads(raw).get("claim_id")}
    except (httpx.HTTPError, ValueError) as e:
        rec = {"status": 0, "error": type(e).__name__}
    with _write, open(Path(STATE["events"]).with_name("shadow.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stable", required=True)
    ap.add_argument("--canary", default="")
    ap.add_argument("--weight", type=float, default=0.0)
    ap.add_argument("--shadow", action="store_true")
    ap.add_argument("--events", default="runs/router_events.jsonl")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    STATE.update(stable=a.stable.rstrip("/"), canary=a.canary.rstrip("/"), weight=a.weight, shadow=a.shadow, events=a.events)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
