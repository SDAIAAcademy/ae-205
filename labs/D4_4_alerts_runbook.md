---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "4.4"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D4_4_alerts_runbook.html"
---

# Lab 4.4 · Two alerts and a runbook

Write two alert rules and a one-page runbook for the on-call engineer, then choose the capstone model.

Day 4 · Session 4: Alerts and a runbook

### Goal

Write two alert rules for Farz, one on the error ratio and one on the 95th-percentile latency, prove on a recorded series that they fire on the real problems and stay quiet on a one-minute blip, and write the one-page runbook the on-call engineer opens when they fire.

## What you need

- The lab folder `rifd-labs/4.4`: an empty rule group in `monitoring/alerts.yml`, `RUNBOOK.md` and `CAPSTONE.md` to fill
- The recording `../data/recordings/spike.jsonl`: 30 minutes of Farz's metrics, one scrape every 15 seconds, with a latency blip at minute 6, an error spike from minute 12 to 18 and a sustained latency rise from minute 22
- AI policy: off for the first attempt at the two rules. Write them yourself, test them, then compare with an assistant if you want to.

### Write the two rules without AI help 8 min

In `monitoring/alerts.yml`, write `FarzErrorRatioHigh`: the rate of triage requests with a 5xx status divided by the rate of all triage requests, above 0.01. Write `FarzLatencyP95High`: the 95th percentile from the histogram, above 0.15. Give each a `for:` duration, a `severity` label and a `runbook_url` annotation pointing at a section of `RUNBOOK.md`.

### Test them on the recorded spike 6 min

```bash
# file: terminal
cd rifd-labs/4.4
uv run python tools/promlite.py rules --series ../data/recordings/spike.jsonl --rules monitoring/alerts.yml
```

Each rule must fire on its problem and not at minute 6. If the latency rule fires on the blip, change its window or its `for:` and test again. Real Prometheus tests rules the same way with `promtool test rules`.

### Write the one-page runbook 8 min

Fill `RUNBOOK.md`: who is accountable for a rollback decision, then for each alert what the caller sees, the first three checks, when to roll back and how, and who to tell.

### Choose the capstone model; check 3 min

In `CAPSTONE.md`, name the model you will take to a monitored service in the capstone, why, and the latency objective you will defend.

```bash
# file: terminal
uv run ../lab.py check 4.4
```

### ✱ Stretch

Add a burn-rate alert on the error objective over two windows and test it on the same recording.

## Check yourself

1. Which of your two settings, the rate window or the `for:` duration, kept the latency rule quiet at minute 6?
2. The error rule fired two minutes after the spike began. Is that too slow for Rifd?
3. The on-call engineer sees FarzErrorRatioHigh ten minutes after a release. What does the runbook let them do before they reach Munira?
