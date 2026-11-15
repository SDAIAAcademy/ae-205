"""Solution of lab 3.2: logs with a request id and no personal data, and a span for the slow step."""

import json
import re
from collections import defaultdict

from common import check, expect_fail, fresh, restore, say, server, sh, uv, write

PERSONAL = re.compile(r"(?<!\d)[12]\d{9}(?!\d)|(?<!\d)05\d{8}(?!\d)")
ENV = {"RIFD_LOG_FILE": "runs/service.log", "RIFD_TRACE_FILE": "runs/spans.jsonl"}


def traffic(lab, port, limit):
    (lab / "runs").mkdir(exist_ok=True)
    for f in ("service.log", "spans.jsonl"):
        (lab / "runs" / f).unlink(missing_ok=True)
    with server(lab, port, env=ENV):
        uv(lab, "python", "tools/replay.py", "--file", "../data/replay/week1.csv", "--url", f"http://127.0.0.1:{port}",
           "--rate", "40", "--limit", str(limit), "--out", "runs/replay.jsonl")


lab = fresh("3.2")
say("the start state: what the logs hold")
traffic(lab, 18320, 200)
log = (lab / "runs" / "service.log").read_text(encoding="utf-8")
lines = [x for x in log.splitlines() if x.startswith("{")]
leaks = [x for x in lines if PERSONAL.search(x)]
say(f"{len(leaks)} of {len(lines)} log lines carry a national id or a mobile number")
expect_fail("3.2")
restore(lab, "src/rifd/logs.py", "src/rifd/app.py")
traffic(lab, 18321, 400)
print(sh(["uv", "run", "--quiet", "pytest", "tests/test_redaction.py"], lab)[1].splitlines()[-1])
spans = [json.loads(x) for x in (lab / "runs" / "spans.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
by_trace = defaultdict(list)
for s in spans:
    by_trace[s["trace_id"]].append(s)
roots = [s for s in spans if s["parent_id"] is None]
slow = max(roots, key=lambda s: s["duration_ms"])
kids = sorted((s for s in by_trace[slow["trace_id"]] if s is not slow), key=lambda s: -s["duration_ms"])
share = sum(1 for r in roots if any(k["name"] == "policy_lookup" for k in by_trace[r["trace_id"]])) / len(roots)
rows = "\n".join(f"| {k['name']} | {k['duration_ms']:.1f} |" for k in kids)
note = f"""# The slowest request

Trace {slow['trace_id']}, request id {slow['attributes'].get('request_id', '?')}: {slow['duration_ms']:.1f} ms in total ({slow['name']}).

| Span | ms |
|---|---|
{rows}

The slow span is policy_lookup: the call to the policy system for health claims outside the network.
{share:.0%} of the {len(roots)} requests made that call. The prediction itself takes about a millisecond.
"""
write(lab, "runs/slowest.md", note)
say(f"slowest request {slow['duration_ms']:.1f} ms: " + ", ".join(f"{k['name']} {k['duration_ms']:.1f} ms" for k in kids))
say(f"{share:.1%} of {len(roots)} requests called the policy lookup")
check("3.2")
