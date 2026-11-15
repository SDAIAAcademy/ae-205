---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "4.1"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D4_1_canary.html"
---

# Lab 4.1 · A 10% canary

Send 10% of traffic to a new version and compare its metrics with the current one.

Day 4 · Session 1: Rolling, canary and shadow releases

### Goal

Release farz 1.1.0 to one claim in ten through a router, compare it with 1.0.0 on the same traffic (errors, latency, label shares and agreement with the labels that have arrived), and record a decision Munira can sign.

## What you need

- The lab folder `rifd-labs/4.1` with both versions in `models/`, `tools/router.py`, `tools/compare.py` and an empty `RELEASE_LOG.md`
- `../data/rollback_criteria.md`, written by Munira before the release, and the delayed labels `../data/replay/labels_week1.csv`
- Four terminals, or one with background jobs
- AI policy: tutor.

### Start both versions and the router 5 min

```bash
# file: terminal
cd rifd-labs/4.1
RIFD_MODEL_DIR=models/farz-1.0.0 uv run uvicorn rifd.app:app --host 127.0.0.1 --port 8001 --log-level warning &
RIFD_MODEL_DIR=models/farz-1.1.0 uv run uvicorn rifd.app:app --host 127.0.0.1 --port 8002 --log-level warning &
uv run python tools/router.py --stable http://127.0.0.1:8001 --canary http://127.0.0.1:8002 --weight 0.10 --port 8000 &
```

The router hashes the claim id, so a claim that is retried always reaches the same version.

### Replay claims with 10% to the canary 7 min

```bash
# file: terminal
uv run python tools/replay.py --file ../data/replay/week1.csv --url http://127.0.0.1:8000 --rate 60 --out runs/canary.jsonl
```

### Compare errors, latency and predictions 8 min

```bash
# file: terminal
uv run python tools/compare.py runs/canary.jsonl --criteria ../data/rollback_criteria.json \
  --labels ../data/replay/labels_week1.csv --stable 1.0.0 --canary 1.1.0 --json runs/compare.json
```

Both versions answered claims from the same week at the same time: that is what makes the comparison fair. Note how many canary requests you judged.

### Write the release log entry; check 5 min

Fill every row of `RELEASE_LOG.md` and stop the three servers.

```bash
# file: terminal
uv run ../lab.py check 4.1
```

### ✱ Stretch

Run 1.1.0 in shadow instead: copy every request to it, return only 1.0.0's answer, and compare.

## Check yourself

1. Why compare the canary with the current version on the same hour of traffic, and not with last week's dashboard?
2. The canary agrees with the labels a little more often. Is that enough to promote it?
3. Who signs the decision, and what would have let the on-call engineer act without her?
