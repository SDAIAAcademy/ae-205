"""Solution of lab 4.3: PSI and KS per feature and per week, by line as well, and a drift report."""

import csv
import json

from common import check, expect_fail, fresh, restore, say, server, uv, write

lab = fresh("4.3")
expect_fail("4.3")
restore(lab, "tools/drift.py")
weeks = [f"../data/replay/week{w}.csv" for w in (1, 2, 3, 4)]
(lab / "runs").mkdir(exist_ok=True)
with server(lab, 18430):
    for w in (1, 2, 3, 4):
        say(f"replay week {w} through farz 1.0.0")
        print(uv(lab, "python", "tools/replay.py", "--file", weeks[w - 1], "--url", "http://127.0.0.1:18430", "--rate", "150", "--out", f"runs/week{w}.jsonl"))
print(uv(lab, "python", "tools/drift.py", "--weeks", *weeks, "--by", "line", "--out", "runs/drift.json"))
d = json.loads((lab / "runs" / "drift.json").read_text(encoding="utf-8"))
p = {}
for w in (1, 2, 3, 4):
    rows = [json.loads(x) for x in (lab / "runs" / f"week{w}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    ok = [r for r in rows if r["status"] == 200]
    shares = {k: round(sum(r["label"] == k for r in ok) / len(ok), 3) for k in ("fast_track", "standard", "investigate")}
    agree = None
    labels = lab.parent / "data" / "replay" / f"labels_week{w}.csv"
    if labels.is_file():
        with open(labels, encoding="utf-8") as f:
            truth = {r["claim_id"]: r["label"] for r in csv.DictReader(f)}
        known = [r for r in ok if r["claim_id"] in truth]
        agree = round(sum(truth[r["claim_id"]] == r["label"] for r in known) / len(known), 3)
    p[f"week{w}"] = {"answered": len(ok), "shares": shares, "agreement": agree}
(lab / "runs" / "predictions_by_week.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
w4, w1 = d["week4"], d["week1"]
say("week 4: " + ", ".join(f"{f} {c['psi']}" for f, c in w4.items() if c["verdict"] != "stable"))
t = d["week3"]["policy_tenure_months"]
shares = "; ".join(f"week {w[-1]}: investigate {v['shares']['investigate']:.0%}, fast track {v['shares']['fast_track']:.0%}" for w, v in p.items())
agree = "; ".join(f"week {w[-1]}: {v['agreement']:.1%}" for w, v in p.items() if v["agreement"] is not None)
report = (lab / "DRIFT_REPORT.md").read_text(encoding="utf-8")
fill = {
    "Statistic and thresholds": "PSI over the training deciles or categories (Rifd's policy: under 0.1 stable, 0.1 to 0.25 watch, 0.25 or more shifted), with the KS test for numeric features",
    "Shifted features (and in which segment)": f"channel from week 3 (PSI {d['week3']['channel']['psi']} in week 3, {w4['channel']['psi']} in week 4: the app's share rose); amount_sar of motor claims (PSI {w4['amount_sar|line=motor']['psi']} in week 4 by line, while all lines pooled give {w4['amount_sar']['psi']})",
    "Features that moved but do not matter": f"policy_tenure_months: in week 3 the KS p-value is {t['p_value']}, a move that is not chance at the 5% level, but the PSI is {t['psi']}: tenure rose by about a month, which does not matter; by week 4 the test no longer tells it from chance ({d['week4']['policy_tenure_months']['p_value']})",
    "Prediction shares by week": shares,
    "What the delayed labels show": f"agreement of farz 1.0.0 with the labels that have arrived: {agree}, before the shift",
    "What the labels cannot show yet": "whether the model is still right on weeks 3 and 4: their labels arrive about two weeks after the claims",
    "Recommendation": "keep 1.0.0 in service and watch; ask the claims system why the app share and motor amounts rose; review the investigate share weekly; retrain on weeks 3 and 4 when their labels arrive if agreement falls",
}
for row, value in fill.items():
    report = report.replace(f"| {row} | |", f"| {row} | {value} |")
write(lab, "DRIFT_REPORT.md", report)
check("4.3")
