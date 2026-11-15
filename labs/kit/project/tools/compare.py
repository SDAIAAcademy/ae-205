"""Compare the versions that answered a replay, and apply the written rollback criteria (labs 4.1, 4.2).

    uv run python tools/compare.py runs/canary.jsonl --criteria ../data/rollback_criteria.json
    uv run python tools/compare.py runs/canary.jsonl --criteria ../data/rollback_criteria.json --watch
    uv run python tools/compare.py runs/canary.jsonl --labels ../data/replay/labels_week1.csv

--watch rereads the file every few seconds while the replay runs and stops at the first criterion
that fires. --labels adds agreement with the delayed labels that have arrived.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

LABELS = ["fast_track", "standard", "investigate"]


def pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    v = sorted(values)
    k = min(len(v) - 1, max(0, int(round(q * len(v) + 0.5)) - 1))
    return round(v[k], 1)


def summarise(rows: list[dict], truth: dict[str, str] | None = None) -> dict[str, dict]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(str(r.get("version")), []).append(r)
    out = {}
    for version, rs in sorted(groups.items()):
        ok = [r for r in rs if r["status"] == 200]
        errors = [r for r in rs if r["status"] == 0 or r["status"] >= 500]
        ms = [r["ms"] for r in rs if r["ms"] is not None]
        shares = {lab: round(sum(r["label"] == lab for r in ok) / len(ok), 3) if ok else 0.0 for lab in LABELS}
        s = {"requests": len(rs), "error_ratio": round(len(errors) / len(rs), 4), "p50_ms": pct(ms, 0.5),
             "p95_ms": pct(ms, 0.95), "shares": shares}
        if truth:
            known = [r for r in ok if r["claim_id"] in truth]
            if known:
                s["agreement_with_labels"] = round(sum(truth[r["claim_id"]] == r["label"] for r in known) / len(known), 3)
                s["labelled"] = len(known)
        out[version] = s
    return out


def verdict(summary: dict[str, dict], stable: str, canary: str, c: dict) -> list[str]:
    """The criteria that fire for the canary. An empty list means: no reason to roll back yet."""
    if canary not in summary or stable not in summary:
        return []
    k, s = summary[canary], summary[stable]
    if k["requests"] < c["min_canary_requests"]:
        return []
    fired = []
    if k["error_ratio"] > c["error_ratio_max"]:
        fired.append(f"error ratio {k['error_ratio']:.2%} > {c['error_ratio_max']:.0%}")
    if k["p95_ms"] is not None and k["p95_ms"] > c["p95_ms_max"]:
        fired.append(f"p95 {k['p95_ms']} ms > {c['p95_ms_max']} ms")
    for lab in LABELS:
        diff = abs(k["shares"][lab] - s["shares"][lab])
        if diff > c["label_share_max_diff"]:
            fired.append(f"{lab} share {k['shares'][lab]:.0%} against {s['shares'][lab]:.0%} (difference {diff:.0%} > {c['label_share_max_diff']:.0%})")
    return fired


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            pass  # a line still being written
    return out


def table(summary: dict[str, dict]) -> str:
    lines = [f"{'version':<9}{'requests':>9}{'errors':>9}{'p50 ms':>8}{'p95 ms':>8}   fast/std/inv" + ("   agree" if any("agreement_with_labels" in v for v in summary.values()) else "")]
    for v, s in summary.items():
        sh = "/".join(f"{s['shares'][lab]:.0%}" for lab in LABELS)
        agree = f"   {s['agreement_with_labels']:.1%}" if "agreement_with_labels" in s else ""
        lines.append(f"{v:<9}{s['requests']:>9}{s['error_ratio']:>9.2%}{s['p50_ms'] or 0:>8}{s['p95_ms'] or 0:>8}   {sh}{agree}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--criteria")
    ap.add_argument("--labels")
    ap.add_argument("--stable", default="1.0.0")
    ap.add_argument("--canary")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--json", help="write the summary and verdict here")
    a = ap.parse_args()
    criteria = json.loads(Path(a.criteria).read_text(encoding="utf-8")) if a.criteria else None
    truth = None
    if a.labels:
        with open(a.labels, encoding="utf-8") as f:
            truth = {r["claim_id"]: r["label"] for r in csv.DictReader(f)}
    path = Path(a.file)
    start, last_n, still = time.monotonic(), -1, 0
    while True:
        rows = load(path)
        summary = summarise(rows, truth)
        canary = a.canary or next((v for v in summary if v != a.stable), None)
        fired = verdict(summary, a.stable, canary, criteria) if criteria and canary else []
        if a.watch:
            n = summary.get(canary, {}).get("requests", 0) if canary else 0
            print(f"[{time.monotonic() - start:6.1f} s] canary {canary}: {n} requests; " + ("ROLL BACK: " + "; ".join(fired) if fired else "no criterion fired"), flush=True)
            if fired:
                break
            still = still + 1 if len(rows) == last_n else 0
            last_n = len(rows)
            if still >= 3:
                break
            time.sleep(3)
            continue
        break
    print(table(summary))
    if criteria and canary:
        print("verdict: " + ("ROLL BACK (" + "; ".join(fired) + ")" if fired else "no rollback criterion fired"))
    if a.json:
        Path(a.json).write_text(json.dumps({"summary": summary, "canary": canary, "fired": fired}, indent=2) + "\n", encoding="utf-8")
    return 3 if fired else 0


if __name__ == "__main__":
    sys.exit(main())
