"""Solution of lab 3.3: an open load at three rates, with the claims Farz will see."""

import json
import os

from common import check, expect_fail, fresh, restore, say, server, uv, write

PORT = 18330
RATES = os.environ.get("RIFD_RATES", "40 100 220").split()  # lower them on a slow or busy laptop
lab = fresh("3.3")
expect_fail("3.3")
with server(lab, PORT):
    say("the supplied load: one claim, over and over")
    print(uv(lab, "python", "tools/loadtest.py", "--url", f"http://127.0.0.1:{PORT}", "--rates", "100", "--seconds", "15",
             "--file", "loadtest/one_claim.csv", "--out", "runs/load_one_claim.json"))
    restore(lab, "tools/loadtest.py")
    say("the replay claims of week 1, at three rates")
    print(uv(lab, "python", "tools/loadtest.py", "--url", f"http://127.0.0.1:{PORT}", "--rates", *RATES,
             "--seconds", "20", "--label", "1 worker", "--out", "runs/load.json"))
rep = json.loads((lab / "runs" / "load.json").read_text(encoding="utf-8"))
one = json.loads((lab / "runs" / "load_one_claim.json").read_text(encoding="utf-8"))["steps"][0]
rows = "\n".join(f"| {s['target_rps']:.0f} | {s['achieved_rps']} | {s['p50_ms']} | {s['p95_ms']} | {s['p99_ms']} | {s['error_ratio']:.2%} | {'holds' if s['meets_objective'] else 'broken'} |"
                 for s in rep["steps"])
note = f"""# Load test: Farz, one worker

Objective: p95 at or under 150 ms at 200 requests a second, errors at or under 1% (Munira Al-Ajmi).

| Rate | Achieved | p50 ms | p95 ms | p99 ms | Errors | Objective |
|---|---|---|---|---|---|---|
{rows}

One worker holds the objective up to {rep['highest_rate_within_objective']} requests a second of the rates tried and breaks it above.
The 95th percentile is set by the health claims outside the network, which wait about 120 ms for the policy lookup.
The supplied test, one motor claim at 100 a second, reported a p95 of {one['p95_ms']} ms: it never called the lookup.
"""
write(lab, "runs/load_note.md", note)
check("3.3")
