"""Solution of lab 4.2: a canary of farz 1.2.0, the criteria fire, the share goes to 0, then the cause."""

import json
import subprocess
from contextlib import ExitStack

from common import check, expect_fail, fresh, post_json, say, server, sh, uv, write

STABLE, CANARY, ROUTER = 18421, 18422, 18420
lab = fresh("4.2")
expect_fail("4.2")
(lab / "runs").mkdir(exist_ok=True)
for f in ("router_events.jsonl", "canary.jsonl", "after_rollback.jsonl"):
    (lab / "runs" / f).unlink(missing_ok=True)
with ExitStack() as stack:
    stack.enter_context(server(lab, STABLE, env={"RIFD_MODEL_DIR": "models/farz-1.1.0"}))
    stack.enter_context(server(lab, CANARY, env={"RIFD_MODEL_DIR": "models/farz-1.2.0"}))
    stack.enter_context(server(lab, ROUTER, ready_path="/admin/state",
                               cmd=["python", "tools/router.py", "--stable", f"http://127.0.0.1:{STABLE}", "--canary", f"http://127.0.0.1:{CANARY}",
                                    "--weight", "0.10", "--port", str(ROUTER)]))
    say("release 1.2.0 to 10% and watch the written criteria")
    replay = subprocess.Popen(["uv", "run", "--quiet", "python", "tools/replay.py", "--file", "../data/replay/week2.csv",
                               "--url", f"http://127.0.0.1:{ROUTER}", "--rate", "50", "--out", "runs/canary.jsonl"], cwd=lab, stdout=subprocess.DEVNULL)
    try:
        code, out = sh(["uv", "run", "--quiet", "python", "tools/compare.py", "runs/canary.jsonl", "--criteria", "../data/rollback_criteria.json",
                        "--stable", "1.1.0", "--canary", "1.2.0", "--watch", "--json", "runs/compare.json"], lab, check=False)
        print("\n".join(out.splitlines()[-12:]))
        assert code == 3, "a criterion should fire for 1.2.0"
        fired = json.loads((lab / "runs" / "compare.json").read_text(encoding="utf-8"))["fired"]
        say("roll back first: the canary's share goes to 0")
        print(post_json(f"http://127.0.0.1:{ROUTER}/admin/weight", {"canary": 0, "reason": "criterion 3 fired: " + fired[0]}))
    finally:
        replay.terminate()
        replay.wait(timeout=30)
    print(uv(lab, "python", "tools/replay.py", "--file", "../data/replay/week2.csv", "--url", f"http://127.0.0.1:{ROUTER}",
             "--rate", "20", "--limit", "60", "--out", "runs/after_rollback.jsonl"))
events = [json.loads(x) for x in (lab / "runs" / "router_events.jsonl").read_text(encoding="utf-8").splitlines()]
start = next(e for e in events if e["event"] == "start")
back = next(e for e in events if e["event"] == "weight" and e["after"] == 0)
c = json.loads((lab / "runs" / "compare.json").read_text(encoding="utf-8"))
s, k = c["summary"]["1.1.0"], c["summary"]["1.2.0"]
meta = json.loads((lab / "models" / "farz-1.2.0" / "metadata.json").read_text(encoding="utf-8"))
meta_old = json.loads((lab / "models" / "farz-1.1.0" / "metadata.json").read_text(encoding="utf-8"))
say(f"cause: decision {meta['decision']} in 1.2.0 against {meta_old['decision']} in 1.1.0")


def shares(x):
    return ", ".join(f"{lab_} {x['shares'][lab_]:.0%}" for lab_ in ("fast_track", "standard", "investigate"))


log = (lab / "RELEASE_LOG.md").read_text(encoding="utf-8")
fill = {
    "Change": "retrained gradient boosting with a new decision rule",
    "Strategy and traffic share": "canary through the router, 10% of claims by a hash of the claim id",
    "Canary requests judged": f"{k['requests']} (minimum 200)",
    "Error ratio: current / canary": f"{s['error_ratio']:.2%} / {k['error_ratio']:.2%}",
    "p95 ms: current / canary": f"{s['p95_ms']} / {k['p95_ms']}",
    "Label shares: current / canary": f"{shares(s)} / {shares(k)}",
    "Agreement with delayed labels: current / canary": "not used: the criteria fired first",
    "Decision (promote or roll back)": "Roll back: " + "; ".join(c["fired"]),
    "Decided by": "the on-call engineer rolled back as the written criteria allow; Munira Al-Ajmi, accountable, was told at once",
    "Evidence files": "runs/canary.jsonl, runs/compare.json, runs/router_events.jsonl, runs/after_rollback.jsonl",
    "Seconds from the criterion firing to traffic share 0": f"{back['after_s'] - start['after_s']:.0f} s from the start of the release to share 0",
    "Cause": f"metadata.json of 1.2.0 sets the investigate threshold to {meta['decision'].get('investigate_threshold')} instead of {meta_old['decision'].get('investigate_threshold')}",
}
for row, value in fill.items():
    log = log.replace(f"| {row} | |", f"| {row} | {value} |")
write(lab, "RELEASE_LOG.md", log)
say(f"rolled back {back['after_s'] - start['after_s']:.0f} s after the release started; canary investigate share {k['shares']['investigate']:.0%} against {s['shares']['investigate']:.0%}")
check("4.2")
