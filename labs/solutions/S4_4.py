"""Solution of lab 4.4: two alert rules tested on a recorded spike, a one-page runbook, the capstone model."""

import json

from common import check, expect_fail, fresh, restore, say, uv, write

RUNBOOK = """# Runbook: Farz, the claims-triage service

On call: the platform engineer of the week. Accountable for a rollback decision: Munira Al-Ajmi, head of claims operations

## errors
Alert FarzErrorRatioHigh.
- What the caller sees: the claims system gets 5xx answers; its claims wait for manual triage
- First three checks: which version answers the errors (rifd_requests_total by version); /readyz of each pod; a release in the last hour (router events, rollout history)
- Roll back when: the errors come from a version released in the last hour, or any criterion of ../data/rollback_criteria.md holds
- How to roll back: set the canary share to 0 (POST /admin/weight {"canary": 0}) or kubectl rollout undo deployment/farz; then tell Munira

## latency
Alert FarzLatencyP95High.
- What the caller sees: triage answers slower than the 150 ms objective at the 95th percentile
- First three checks: the trace of a slow request (is it policy_lookup?); the request rate against the measured capacity; CPU throttling of the pods
- What to change: add a replica if the rate is above capacity; ask the policy team if policy_lookup is slow; roll back if a release started it

## Who to tell
Munira Al-Ajmi for a rollback or a breach of the objective; Ghaida Al-Ruqi's platform channel for the cluster; Bassam Al-Jaber if any log or trace may have carried personal data.
"""

CAPSTONE = """# My capstone model

Model: Farz (the claims-triage model), from the artefact to a monitored service
Why: it has a contract, a slow dependency and a planted faulty version, so every part of the path can be shown with evidence
Latency objective I will defend: p95 at or under 150 ms at 200 requests a second, errors at or under 1%
"""

lab = fresh("4.4")
expect_fail("4.4")
restore(lab, "monitoring/alerts.yml")
write(lab, "RUNBOOK.md", RUNBOOK)
write(lab, "CAPSTONE.md", CAPSTONE)
out = uv(lab, "python", "-c", "import sys, json; sys.path.insert(0,'tools'); import promlite\n"
         "s = promlite.Series.load('../data/recordings/spike.jsonl'); print(json.dumps(promlite.run_rules(s, 'monitoring/alerts.yml')))")
for r in json.loads(out.splitlines()[-1]):
    say(f"{r['alert']} (for {r['for']}): fired " + ", ".join(f"from minute {f['from_s'] / 60:.1f} to {f['to_s'] / 60:.1f}" if f["to_s"] else f"from minute {f['from_s'] / 60:.1f}" for f in r["fired"]))
say("the same rules without a for: duration")
nofor = (lab / "monitoring" / "alerts.yml").read_text(encoding="utf-8").replace("        for: 2m\n", "").replace("        for: 5m\n", "")
write(lab, "runs/alerts_no_for.yml", nofor)
out = uv(lab, "python", "-c", "import sys, json; sys.path.insert(0,'tools'); import promlite\n"
         "s = promlite.Series.load('../data/recordings/spike.jsonl'); print(json.dumps(promlite.run_rules(s, 'runs/alerts_no_for.yml')))")
for r in json.loads(out.splitlines()[-1]):
    say(f"{r['alert']} without for: fired {len(r['fired'])} time(s), first from minute {r['fired'][0]['from_s'] / 60:.1f}" if r["fired"] else f"{r['alert']}: never fired")
check("4.4")
