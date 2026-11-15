---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "4.3"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D4_3_drift.html"
---

# Lab 4.3 · Drift in four weeks

Replay four weeks of claims, compute a drift statistic per feature and name the shifted ones.

Day 4 · Session 3: Drift in replayed traffic

### Goal

Replay four weeks of new claims through Farz, measure for each feature how far its distribution moved from the training data, name the features that really shifted (and in which line of business), rule out one that only looks significant, and say what the delayed labels allow Rifd to conclude.

## What you need

- The lab folder `rifd-labs/4.3`, with `tools/drift.py` missing its PSI function and an empty `DRIFT_REPORT.md`
- The four replay weeks `../data/replay/week1.csv` to `week4.csv` and the labels that have arrived: `labels_week1.csv` and `labels_week2.csv`
- AI policy: tutor.

### Replay the four weeks through the service 5 min

```bash
# file: terminal
cd rifd-labs/4.3
uv run uvicorn rifd.app:app --port 8000 &
for w in 1 2 3 4; do uv run python tools/replay.py --file ../data/replay/week$w.csv --rate 150 --out runs/week$w.jsonl; done
```

Each line of `runs/weekN.jsonl` holds the claim id and the label Farz gave. Count the labels per week while the next step runs.

### Compute population stability and a KS test per feature 9 min

In `tools/drift.py`, write `psi_from_shares`: the sum over bins of (actual share minus expected share) times the log of their ratio, with both shares clipped at `EPS` so that an empty bin does not divide by zero. Then run it, also by line of business.

```bash
# file: terminal
uv run python tools/drift.py --weeks ../data/replay/week1.csv ../data/replay/week2.csv \
  ../data/replay/week3.csv ../data/replay/week4.csv --by line --out runs/drift.json
```

### Name the shifted features; check the labels you have 7 min

Read the table: which features pass 0.25, from which week, and in which line? Which feature has a small p-value but a tiny PSI? Then compare Farz's labels for weeks 1 and 2 with `labels_week1.csv` and `labels_week2.csv`.

### Write the drift report; check 4 min

Fill every row of `DRIFT_REPORT.md`, including what the labels cannot show yet and your recommendation.

```bash
# file: terminal
uv run ../lab.py check 4.3
```

### ✱ Stretch

Recompute the statistics with Evidently and compare its verdicts with yours.

## Check yourself

1. Why does the amount look stable over all claims and shifted for motor claims?
2. Policy tenure has a KS p-value of 0.04 in week 3. Why is it not in your list of shifted features?
3. What would have to arrive before Rifd can say whether Farz is still right in week 4?
