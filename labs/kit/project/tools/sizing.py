"""From measured capacity to replicas and the cost of 1,000 predictions (lab 3.4).

    uv run python tools/sizing.py runs/load_w1.json runs/load_w2.json --out runs/sizing.json

Each load report comes from tools/loadtest.py run against one configuration (--label "1 worker").
A replica is one container; it is billed on what it requests: one vCPU and 0.25 GiB per worker.
Replicas are chosen so that each runs at most at (1 - headroom) of its measured capacity, plus one
spare so that a rolling update or a lost node does not break the objective.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

GIB_PER_WORKER = 0.25


def workers_of(label: str) -> int:
    m = re.search(r"(\d+)\s*worker", label)
    if not m:
        raise ValueError(f"name the configuration with its workers, such as --label '2 workers' (got {label!r})")
    return int(m.group(1))


def replicas_needed(target_rps: float, capacity_rps: float, headroom: float, spare: int = 1) -> int:
    """Enough replicas that each stays below (1 - headroom) of the capacity it showed, plus spares."""
    return math.ceil(target_rps / (capacity_rps * (1 - headroom))) + spare


def cost_per_hour(replicas: int, workers: int, price: dict) -> float:
    per_replica = workers * price["vcpu_hour"] + workers * GIB_PER_WORKER * price["gib_hour"]
    return round(replicas * per_replica, 4)


def cost_per_1000(hourly: float, rate_rps: float) -> float:
    """The cost of 1,000 predictions when the service carries rate_rps for an hour."""
    return round(hourly / (rate_rps * 3600 / 1000), 6)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("reports", nargs="+")
    ap.add_argument("--objective", default="../data/objective.json")
    ap.add_argument("--prices", default="../data/price_sheet.json")
    ap.add_argument("--headroom", type=float, default=0.3)
    ap.add_argument("--out", default="runs/sizing.json")
    a = ap.parse_args()
    obj = json.loads(Path(a.objective).read_text(encoding="utf-8"))
    price = json.loads(Path(a.prices).read_text(encoding="utf-8"))
    target = obj["target_rps"]
    options = []
    for path in a.reports:
        rep = json.loads(Path(path).read_text(encoding="utf-8"))
        cap = rep["highest_rate_within_objective"]
        w = workers_of(rep["label"])
        if not cap:
            options.append({"config": rep["label"], "workers": w, "capacity_rps": None, "note": "no measured rate met the objective"})
            continue
        n = replicas_needed(target, cap, a.headroom)
        hourly = cost_per_hour(n, w, price)
        options.append({"config": rep["label"], "workers": w, "capacity_rps": cap, "replicas": n,
                        "vcpu": n * w, "cost_per_hour_sar": hourly, "cost_per_1000_sar": cost_per_1000(hourly, target)})
    ok = [o for o in options if o.get("replicas")]
    best = min(ok, key=lambda o: o["cost_per_hour_sar"]) if ok else None
    gpu_note = round(price["gpu_hour"] / (target * 3.6), 6)
    result = {"target_rps": target, "p95_ms": obj["p95_ms"], "headroom": a.headroom, "options": options,
              "chosen": best["config"] if best else None, "one_gpu_replica_cost_per_1000_sar": gpu_note}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"target {target} requests a second, p95 <= {obj['p95_ms']} ms, headroom {a.headroom:.0%}, one spare replica")
    for o in options:
        if o.get("replicas"):
            print(f"  {o['config']:<12} capacity {o['capacity_rps']:>5} rps -> {o['replicas']} replicas, {o['vcpu']} vCPU, SAR {o['cost_per_hour_sar']}/h, SAR {o['cost_per_1000_sar']} per 1,000")
        else:
            print(f"  {o['config']:<12} {o['note']}")
    print(f"chosen: {result['chosen']}; for comparison one GPU replica alone costs SAR {gpu_note} per 1,000 at the same rate")


if __name__ == "__main__":
    main()
