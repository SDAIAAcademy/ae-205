"""Solution of lab 4.1: a 10% canary of farz 1.1.0 through the router, compared like with like."""

import json
from contextlib import ExitStack

from common import check, expect_fail, fresh, say, server, sh, uv, write

STABLE, CANARY, ROUTER = 18411, 18412, 18410
lab = fresh("4.1")
expect_fail("4.1")
(lab / "runs").mkdir(exist_ok=True)
(lab / "runs" / "router_events.jsonl").unlink(missing_ok=True)
with ExitStack() as stack:
    stack.enter_context(server(lab, STABLE, env={"RIFD_MODEL_DIR": "models/farz-1.0.0"}))
    stack.enter_context(server(lab, CANARY, env={"RIFD_MODEL_DIR": "models/farz-1.1.0"}))
    stack.enter_context(server(lab, ROUTER, ready_path="/admin/state",
                               cmd=["python", "tools/router.py", "--stable", f"http://127.0.0.1:{STABLE}", "--canary", f"http://127.0.0.1:{CANARY}",
                                    "--weight", "0.10", "--port", str(ROUTER)]))
    say("replay week 1 through the router: 10% of claims go to 1.1.0")
    print(uv(lab, "python", "tools/replay.py", "--file", "../data/replay/week1.csv", "--url", f"http://127.0.0.1:{ROUTER}",
             "--rate", "60", "--out", "runs/canary.jsonl"))
code, out = sh(["uv", "run", "--quiet", "python", "tools/compare.py", "runs/canary.jsonl", "--criteria", "../data/rollback_criteria.json",
                "--labels", "../data/replay/labels_week1.csv", "--stable", "1.0.0", "--canary", "1.1.0", "--json", "runs/compare.json"], lab, check=False)
print(out)
c = json.loads((lab / "runs" / "compare.json").read_text(encoding="utf-8"))
s, k = c["summary"]["1.0.0"], c["summary"]["1.1.0"]


def shares(x):
    return ", ".join(f"{lab_} {x['shares'][lab_]:.0%}" for lab_ in ("fast_track", "standard", "investigate"))


def agree(x):
    return f"{x['agreement_with_labels']:.1%} of {x['labelled']}" if x.get("agreement_with_labels") is not None else "no labels yet"


decision = "Roll back" if c["fired"] else "Promote"
log = (lab / "RELEASE_LOG.md").read_text(encoding="utf-8")
fill = {
    "Change": "gradient boosting in place of logistic regression; same threshold 0.30 for investigate",
    "Strategy and traffic share": "canary through the router, 10% of claims by a hash of the claim id",
    "Canary requests judged": f"{k['requests']} (minimum 200)",
    "Error ratio: current / canary": f"{s['error_ratio']:.2%} / {k['error_ratio']:.2%}",
    "p95 ms: current / canary": f"{s['p95_ms']} / {k['p95_ms']}",
    "Label shares: current / canary": f"{shares(s)} / {shares(k)}",
    "Agreement with delayed labels: current / canary": f"{agree(s)} / {agree(k)}",
    "Decision (promote or roll back)": decision + (": " + "; ".join(c["fired"]) if c["fired"] else ": no criterion fired after the minimum number of requests"),
    "Decided by": "Munira Al-Ajmi, on the evidence above",
    "Evidence files": "runs/canary.jsonl, runs/compare.json",
}
for row, value in fill.items():
    log = log.replace(f"| {row} | |", f"| {row} | {value} |")
write(lab, "RELEASE_LOG.md", log)
say(f"canary {k['requests']} requests; p95 {s['p95_ms']} / {k['p95_ms']} ms; decision {decision}")
check("4.1")
