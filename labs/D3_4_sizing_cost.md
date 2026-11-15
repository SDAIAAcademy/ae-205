---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "3.4"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D3_4_sizing_cost.html"
---

# Lab 3.4 · Workers, replicas and cost

Tune workers and replicas to meet the latency objective and compute cost per 1,000 predictions.

Day 3 · Session 4: Sizing and cost

### Goal

Measure what one, two and four workers carry within the objective, choose the workers and replicas that meet 200 requests a second with headroom and a spare, and price the choice per 1,000 predictions against a graphics processor.

## What you need

- The lab folder `rifd-labs/3.4`: `tools/sizing.py` with its two formulas missing, and `tools/loadtest.py` from lab 3.3
- `../data/price_sheet.json`: Rifd's in-Kingdom quote, SAR 0.19 a vCPU-hour, 0.025 a GiB-hour and 7.40 a GPU-hour (invented prices)
- AI policy: tutor.

### Measure one, two and four workers at the target rate 10 min

```bash
# file: terminal
cd rifd-labs/3.4
uv run uvicorn rifd.app:app --host 127.0.0.1 --port 8000 --log-level warning --workers 1 &
uv run python tools/loadtest.py --rates 120 160 200 --seconds 15 --label "1 worker" --out runs/load_w1.json
kill %1
# again with --workers 2 (rates 200 280 360, --label "2 workers") and --workers 4 (rates 300 400 500)
```

Wait for `/readyz` after each start: every worker loads its own copy of the model.

### Choose workers and replicas with headroom 6 min

In `tools/sizing.py`, write `replicas_needed`: enough replicas that each runs at most at (1 − headroom) of its measured capacity, rounded up, plus the spare. Then compare the configurations.

```bash
# file: terminal
uv run python tools/sizing.py runs/load_w1.json runs/load_w2.json runs/load_w4.json --out runs/sizing.json
```

### Compute cost per 1,000 predictions 5 min

Write `cost_per_1000`: the cost of an hour divided by the thousands of predictions in that hour at the target rate. Run `sizing.py` again and write `runs/sizing_note.md`: your choice, its cost per 1,000, and the cost of one GPU replica for comparison.

### Check 4 min

```bash
# file: terminal
uv run ../lab.py check 3.4
```

### ✱ Stretch

Price the same load on the cheapest configuration that breaks the objective and say what Munira would lose.

## Check yourself

1. Did two workers carry twice what one did? If not, what took the rest?
2. Why do you plan replicas from the measured capacity minus headroom, not from the capacity itself?
3. What would make a graphics processor the right choice for a model at Rifd?
