"""Solution of lab 3.4: workers 1, 2 and 4, replicas for the target, and the cost of 1,000 predictions."""

import json

from common import check, expect_fail, fresh, restore, say, server, uv, write

lab = fresh("3.4")
expect_fail("3.4")
restore(lab, "tools/sizing.py")
plans = {1: ["40", "120", "160"], 2: ["80", "200", "280"], 4: ["120", "300", "400"]}
reports = []
for w, rates in plans.items():
    port = 18340 + w
    with server(lab, port, workers=w):
        say(f"{w} worker(s)")
        out = f"runs/load_w{w}.json"
        print(uv(lab, "python", "tools/loadtest.py", "--url", f"http://127.0.0.1:{port}", "--rates", *rates, "--seconds", "15",
                 "--label", f"{w} worker{'s' if w > 1 else ''}", "--out", out))
        reports.append(out)
print(uv(lab, "python", "tools/sizing.py", *reports, "--out", "runs/sizing.json"))
s = json.loads((lab / "runs" / "sizing.json").read_text(encoding="utf-8"))
chosen = next(o for o in s["options"] if o["config"] == s["chosen"])
rows = "\n".join(f"| {o['config']} | {o.get('capacity_rps')} | {o.get('replicas', '-')} | {o.get('vcpu', '-')} | {o.get('cost_per_hour_sar', '-')} | {o.get('cost_per_1000_sar', '-')} |"
                 for o in s["options"])
note = f"""# Sizing: Farz at 200 requests a second

Headroom {s['headroom']:.0%}, one spare replica, prices from ../data/price_sheet.json.

| Configuration | Capacity rps | Replicas | vCPU | SAR an hour | SAR per 1,000 |
|---|---|---|---|---|---|
{rows}

Choice: {chosen['config']} per replica, {chosen['replicas']} replicas, SAR {chosen['cost_per_1000_sar']} per 1,000 predictions.
One GPU replica alone would cost SAR {s['one_gpu_replica_cost_per_1000_sar']} per 1,000 at the same rate, and the model is not the slow part.
These capacities were measured with the load generator on the same laptop as the service; measure again on the cluster's nodes.
"""
write(lab, "runs/sizing_note.md", note)
check("3.4")
