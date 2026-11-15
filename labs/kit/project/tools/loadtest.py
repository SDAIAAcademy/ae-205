"""Step a steady load through several rates and report latency against the objective (labs 3.3, 3.4).

    uv run python tools/loadtest.py --url http://127.0.0.1:8000 --rates 60 120 180 --seconds 20 --out runs/load.json

For each rate: a short warm-up that is not counted, then a fixed number of seconds at that rate
(an open load: requests leave on schedule whatever the answers do). It reports the rate actually
achieved, the 50th, 95th and 99th percentiles seen by the caller, the error ratio, and whether the
objective in ../data/objective.json holds. Locust and k6 do the same job; see loadtest/.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import claims  # noqa: E402
import replay  # noqa: E402


def percentile(values: list[float], q: float) -> float:
    v = sorted(values)
    return round(v[min(len(v) - 1, int(q * len(v)))], 1)


def step(url: str, rows: list[dict], rate: float, seconds: float, warmup: float, out_dir: Path) -> dict:
    n_warm, n = int(rate * warmup), int(rate * seconds)
    pool = (rows * (1 + (n_warm + n) // len(rows)))[: n_warm + n]
    if n_warm:
        replay.replay(pool[:n_warm], url, rate, out_dir / f"warmup_{int(rate)}.jsonl")
    summary = replay.replay(pool[n_warm:], url, rate, out_dir / f"rate_{int(rate)}.jsonl")
    res = [json.loads(x) for x in (out_dir / f"rate_{int(rate)}.jsonl").read_text(encoding="utf-8").splitlines()]
    ms = [r["ms"] if r["ms"] is not None else 10000.0 for r in res]
    errors = sum(r["status"] == 0 or r["status"] >= 500 for r in res)
    return {"target_rps": rate, "achieved_rps": summary["achieved_rps"], "requests": len(res),
            "p50_ms": percentile(ms, 0.50), "p95_ms": percentile(ms, 0.95), "p99_ms": percentile(ms, 0.99),
            "error_ratio": round(errors / len(res), 4)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--rates", type=float, nargs="+", required=True)
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--warmup", type=float, default=3)
    ap.add_argument("--file", default="../data/replay/week1.csv")
    ap.add_argument("--objective", default="../data/objective.json")
    ap.add_argument("--label", default="", help="a name for this configuration, such as '1 worker'")
    ap.add_argument("--out", default="runs/load.json")
    a = ap.parse_args()
    obj = json.loads(Path(a.objective).read_text(encoding="utf-8"))
    rows = claims.read(a.file)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    steps = []
    print(f"objective: p95 <= {obj['p95_ms']} ms, errors <= {obj['error_ratio_max']:.0%}")
    print(f"{'rate':>6}{'achieved':>10}{'p50':>8}{'p95':>8}{'p99':>8}{'errors':>8}   objective")
    for rate in a.rates:
        s = step(a.url, rows, rate, a.seconds, a.warmup, out.parent)
        s["meets_objective"] = s["p95_ms"] <= obj["p95_ms"] and s["error_ratio"] <= obj["error_ratio_max"] and s["achieved_rps"] >= 0.95 * rate
        steps.append(s)
        print(f"{rate:>6.0f}{s['achieved_rps']:>10}{s['p50_ms']:>8}{s['p95_ms']:>8}{s['p99_ms']:>8}{s['error_ratio']:>8.2%}   {'holds' if s['meets_objective'] else 'BROKEN'}")
    held = [s["target_rps"] for s in steps if s["meets_objective"]]
    report = {"label": a.label, "file": Path(a.file).as_posix(), "objective": {"p95_ms": obj["p95_ms"], "error_ratio_max": obj["error_ratio_max"]},
              "steps": steps, "highest_rate_within_objective": max(held) if held else None}
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"highest rate within the objective: {report['highest_rate_within_objective']} requests a second; report in {out}")


if __name__ == "__main__":
    main()
