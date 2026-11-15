"""Solution of lab 3.1: request, latency and prediction metrics, a dashboard, and a recording to query."""

import subprocess

from common import check, expect_fail, fresh, restore, say, server, uv

PORT = 18310
P = 'histogram_quantile({q}, sum by (le) (rate(rifd_request_duration_seconds_bucket{{route="/v1/triage"}}[30s])))'

lab = fresh("3.1")
expect_fail("3.1")
restore(lab, "src/rifd/metrics.py", "monitoring/dashboard.json")
(lab / "runs").mkdir(exist_ok=True)
with server(lab, PORT):
    say("record /metrics every 2 s while week 1 is replayed at 60 claims a second")
    rec = subprocess.Popen(["uv", "run", "--quiet", "python", "tools/promlite.py", "record", "--url", f"http://127.0.0.1:{PORT}/metrics",
                            "--every", "2", "--for", "40", "--out", "runs/metrics.jsonl"], cwd=lab)
    print(uv(lab, "python", "tools/replay.py", "--file", "../data/replay/week1.csv", "--url", f"http://127.0.0.1:{PORT}",
             "--rate", "60", "--limit", "1800", "--out", "runs/replay.jsonl"))
    rec.wait(timeout=120)
for q in ("0.5", "0.95", "0.99"):
    out = uv(lab, "python", "tools/promlite.py", "query", "--series", "runs/metrics.jsonl", "--last", "--expr", P.format(q=q))
    say(f"p{round(float(q) * 100)}: {out.splitlines()[-1]}")
out = uv(lab, "python", "tools/promlite.py", "query", "--series", "runs/metrics.jsonl", "--last",
         "--expr", "sum by (label) (rate(rifd_predictions_total[30s]))")
say("predictions a second by label: " + " | ".join(out.splitlines()[-3:]))
check("3.1")
