---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "3.1"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D3_1_metrics.html"
---

# Lab 3.1 · Rate, errors and latency

Expose request rate, error rate and latency histograms and graph the 50th, 95th and 99th percentiles.

Day 3 · Session 1: Metrics that matter

### Goal

Give Farz the metrics that answer three questions about every minute of service: how many requests, how many failed, how long they took, and what the model predicted. Then compute the 50th, 95th and 99th percentiles from the histogram, the way a dashboard does.

## What you need

- The lab folder `rifd-labs/3.1`: `src/rifd/metrics.py` with TODOs, and `monitoring/dashboard.json` with two panels missing
- `tools/promlite.py`, a small stand-in for Prometheus that scrapes, records and answers the PromQL the course uses; `monitoring/compose.yaml` runs real Prometheus and Grafana if you have a container runtime
- AI policy: tutor.

### Add the counters and the latency histogram 8 min

In `src/rifd/metrics.py`, create `rifd_requests` (a counter by route and status), `rifd_request_duration_seconds` (a histogram by route with `BUCKETS`) and fill `observe()`. The middleware in `app.py` already calls it for every request.

### Add the prediction distribution 4 min

Create `rifd_predictions`, a counter by model, version and label, and fill `predicted()`. Never put a claim id or a member field in a label: each distinct value makes a new series.

```bash
# file: terminal
uv run uvicorn rifd.app:app --port 8000 &
curl -s -X POST 127.0.0.1:8000/v1/triage -H "content-type: application/json" -d @examples/motor.json
curl -s 127.0.0.1:8000/metrics | grep ^rifd_
```

### Drive traffic and compute the percentiles 7 min

```bash
# file: terminal
uv run python tools/promlite.py record --url http://127.0.0.1:8000/metrics --every 2 --for 40 --out runs/metrics.jsonl &
uv run python tools/replay.py --file ../data/replay/week1.csv --rate 60 --limit 1800 --out runs/replay.jsonl
uv run python tools/promlite.py query --series runs/metrics.jsonl --last \
  --expr 'histogram_quantile(0.95, sum by (le) (rate(rifd_request_duration_seconds_bucket{route="/v1/triage"}[30s])))'
```

Repeat the query with 0.5 and 0.99, and once with `sum by (label) (rate(rifd_predictions_total[30s]))`. Stop the server.

### Read the dashboard file; check 6 min

Open `monitoring/dashboard.json`. Add the 99th-percentile query to the latency panel and a fourth panel with predictions a second by version and label, then run the check.

```bash
# file: terminal
uv run ../lab.py check 3.1
```

### ✱ Stretch

Move the histogram buckets and see how far the estimated 95th percentile moves.

## Check yourself

1. Why can the 95th percentile of four replicas be computed from their buckets, but not by averaging their own 95th percentiles?
2. Which bucket boundary matters most for Munira's objective, and why?
3. Why is `claim_id` never a metric label?
