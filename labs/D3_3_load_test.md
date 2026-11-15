---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "3.3"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D3_3_load_test.html"
---

# Lab 3.3 · Three rates against the objective

Run a load test at three request rates and find where latency breaks the objective.

Day 3 · Session 3: Load testing

### Goal

Load Farz the way the claims system will after a flood: an open load of real claims at fixed rates. Find the rate at which the 95th percentile breaks Munira's objective of 150 ms, and say why it breaks there.

## What you need

- The lab folder `rifd-labs/3.3`: `tools/loadtest.py`, which sends `loadtest/one_claim.csv` by default, and `loadtest/locustfile.py`
- `../data/objective.json`: p95 at or under 150 ms at 200 requests a second, errors at or under 1%
- A quiet laptop: close other heavy programs, because the load generator and the service share its processors
- AI policy: tutor.

### Read the objective and the locust file 4 min

```bash
# file: terminal
cd rifd-labs/3.3
cat ../data/objective.json
sed -n 1,12p loadtest/locustfile.py
```

Note who owns the objective and where latency is measured. In the locust file, find how a number of users becomes a rate, and when that stops being true.

### Make the requests realistic 5 min

```bash
# file: terminal
uv run uvicorn rifd.app:app --host 127.0.0.1 --port 8000 --log-level warning &
uv run python tools/loadtest.py --rates 100 --seconds 15 --out runs/load_one_claim.json
```

That is the supplied test: one motor claim, over and over. In `tools/loadtest.py`, change the default `--file` to `../data/replay/week1.csv`, the week of claims Farz will see.

### Run three rates with a warm-up 10 min

```bash
# file: terminal
uv run python tools/loadtest.py --rates 80 150 220 --seconds 20 --warmup 3 --label "1 worker" --out runs/load.json
```

If every rate holds or every rate breaks, choose others: the check asks for one on each side. Locust is an option: `uv run locust -f loadtest/locustfile.py --headless --host http://127.0.0.1:8000 --users 150 --spawn-rate 50 --run-time 40s --only-summary`.

### Report where the objective breaks; check 6 min

Write `runs/load_note.md`: the table of rates, where the objective breaks, and why, with the trace of lab 3.2 in mind. Stop the server.

```bash
# file: terminal
uv run ../lab.py check 3.3
```

### ✱ Stretch

Run the same rates with k6 and compare the two tools' numbers.

## Check yourself

1. Why did one claim a hundred times a second give a 95th percentile that was too good?
2. At the rate where the objective broke, did the achieved rate keep up with the target?
3. What would change these numbers on the cluster, compared with your laptop?
