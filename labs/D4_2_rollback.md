---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "4.2"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D4_2_rollback.html"
---

# Lab 4.2 · Roll back a faulty version

Trigger the rollback criteria with a seeded faulty version and roll back within five minutes.

Day 4 · Session 2: Rollback on evidence

### Goal

Release farz 1.2.0 as a canary behind 1.1.0, watch it against Munira's written criteria, roll it back within five minutes of the first criterion firing, then find the cause and record the evidence.

## What you need

- The lab folder `rifd-labs/4.2` with farz 1.1.0 and 1.2.0 in `models/`. This lab does not continue from your decision in lab 4.1: in its start state 1.1.0 is the version in service, the router and `tools/compare.py`
- `../data/rollback_criteria.md` and `.json`: judge after 200 canary requests; roll back on errors above 1%, a 95th percentile above 150 ms, or a label share that differs by more than 10 points
- AI policy: tutor.

### Read the criteria; start the canary of 1.2.0 5 min

```bash
# file: terminal
cd rifd-labs/4.2
cat ../data/rollback_criteria.md
RIFD_MODEL_DIR=models/farz-1.1.0 uv run uvicorn rifd.app:app --host 127.0.0.1 --port 8001 --log-level warning &
RIFD_MODEL_DIR=models/farz-1.2.0 uv run uvicorn rifd.app:app --host 127.0.0.1 --port 8002 --log-level warning &
uv run python tools/router.py --stable http://127.0.0.1:8001 --canary http://127.0.0.1:8002 --weight 0.10 --port 8000 &
uv run python tools/replay.py --file ../data/replay/week2.csv --url http://127.0.0.1:8000 --rate 50 --out runs/canary.jsonl &
```

### Watch until a criterion fires 6 min

```bash
# file: terminal
uv run python tools/compare.py runs/canary.jsonl --criteria ../data/rollback_criteria.json \
  --stable 1.1.0 --canary 1.2.0 --watch --json runs/compare.json
```

### Roll back and time it 5 min

```bash
# file: terminal
curl -s -X POST 127.0.0.1:8000/admin/weight -H "content-type: application/json" \
  -d '{"canary": 0, "reason": "criterion 3: investigate share"}'
kill %4
uv run python tools/replay.py --file ../data/replay/week2.csv --url http://127.0.0.1:8000 --rate 20 --limit 60 --out runs/after_rollback.jsonl
```

Roll back first, diagnose second. `runs/router_events.jsonl` records when the release started and when the share went to 0.

### Find the cause; write the release log 6 min

Compare `models/farz-1.1.0/metadata.json` with `models/farz-1.2.0/metadata.json`. Fill `RELEASE_LOG.md`, including the seconds to share 0, the cause, and who decided.

### Check 3 min

```bash
# file: terminal
uv run ../lab.py check 4.2
```

Stop the three servers.

### ✱ Stretch

Do the same rollback on the cluster with `kubectl rollout undo` and compare the time.

## Check yourself

1. Which criterion fired, and after how many canary requests?
2. Errors and latency looked healthy. What would have happened without a criterion on the label shares?
3. Why did the on-call engineer not wait for Munira before setting the share to 0?
