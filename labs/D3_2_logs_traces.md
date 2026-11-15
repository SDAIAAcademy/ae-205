---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "3.2"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D3_2_logs_traces.html"
---

# Lab 3.2 · Logs, redaction and a trace

Add structured logs with a request id, redact personal fields and follow one slow request through a trace.

Day 3 · Session 2: Logs and traces

### Goal

Make every log line of Farz a JSON record that carries the request id and no personal data, prove it with a test, and follow the slowest request of a replay through its spans to the step that made it slow.

## What you need

- The lab folder `rifd-labs/3.2`: a service that logs the whole claim, a logger without its redaction step, and no span around the policy lookup
- structlog for the logs and the OpenTelemetry SDK for the spans; the spans go to `runs/spans.jsonl`, so no collector is needed
- AI policy: tutor.

### Find the personal fields in the current logs 4 min

```bash
# file: terminal
cd rifd-labs/3.2
export RIFD_LOG_FILE=runs/service.log
export RIFD_TRACE_FILE=runs/spans.jsonl
uv run uvicorn rifd.app:app --port 8000 &
uv run python tools/replay.py --rate 40 --limit 200 \
  --file ../data/replay/week1.csv --out runs/replay.jsonl
grep -c national_id runs/service.log
```

Stop the server and delete `runs/service.log` and `runs/spans.jsonl` before the next run.

### Log JSON with a request id; redact at the edge 9 min

In `src/rifd/app.py`, log the claim id, line, label and version instead of the whole claim. In `src/rifd/logs.py`, bind the request id in `bind_request()` and put the `redact` processor back in the chain, as a last defence if someone logs a member field again. Run `uv run pytest tests/test_redaction.py`.

### Add spans; find the slowest request and its slow span 8 min

In `app.py`, wrap the policy lookup in a span of its own named `policy_lookup` (with `tr.start_as_current_span`). Run the replay again with 400 claims, then find the slowest request (the span with no parent and the longest duration) and its children.

```bash
# file: terminal
uv run python - <<'EOF'
import json
spans = [json.loads(x) for x in open("runs/spans.jsonl")]
roots = [s for s in spans if not s["parent_id"]]
slow = max(roots, key=lambda s: s["duration_ms"])
print(slow["duration_ms"])
for s in spans:
    if s["trace_id"] == slow["trace_id"]:
        print(" ", s["name"], s["duration_ms"])
EOF
```

Write `runs/slowest.md`: the trace, its spans with their times, and which step made it slow.

### Check 4 min

```bash
# file: terminal
uv run ../lab.py check 3.2
```

### ✱ Stretch

Pass the request id to the policy lookup as a header and see it in the lookup's own log.

## Check yourself

1. Name two places personal data could still leave Farz after your change.
2. Why is the redaction processor a last defence and not the main one?
3. What share of requests called the policy lookup, and how did that share decide the 95th percentile?
