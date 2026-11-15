---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "1.4"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D1_4_health_readiness.html"
---

# Lab 1.4 · Health and readiness checks

Add health and readiness checks and show how they differ when the model file is missing.

Day 1 · Session 4: Health, readiness and warm-up

### Goal

Give Farz two checks that answer two questions: is the process alive, and should traffic come here now. Load and warm the model before the first request, and show what each check says when the model file is missing.

## What you need

- The lab folder `rifd-labs/1.4`: a service with one `/health` that always says OK and a model loaded on the first request
- The tests `tests/test_health.py`
- AI policy: tutor.

### See the old health check say OK with no model 4 min

```bash
# file: terminal
cd rifd-labs/1.4
RIFD_MODEL_DIR=models/missing uv run uvicorn rifd.app:app --port 8000 &
curl -s 127.0.0.1:8000/health
curl -s -X POST 127.0.0.1:8000/v1/triage -H "content-type: application/json" -d @examples/motor.json
```

A cluster that trusts `/health` sends this pod traffic, and every claim fails. Stop the server.

### Load and warm the model in the lifespan 7 min

In `src/rifd/app.py`, call `load_farz(app)` in the lifespan where the TODO is, and take the lazy loading out of the route. `load_farz` verifies the sha256, makes one warm-up prediction on the artefact's first reference claim and records how long loading and warming took.

### Write /livez and /readyz 6 min

Replace `/health` with `/livez`, which answers while the process runs and never looks at the model, and `/readyz`, which answers 200 with the model's name, version, load and warm-up times only when `app.state.ready` is true, and otherwise a `model-unavailable` problem with the reason.

### Test both with the model file missing 6 min

```bash
# file: terminal
RIFD_MODEL_DIR=models/missing uv run uvicorn rifd.app:app --port 8000 &
curl -si 127.0.0.1:8000/livez | head -1
curl -si 127.0.0.1:8000/readyz
kill %1
uv run pytest tests/test_health.py
```

### Check 2 min

```bash
# file: terminal
uv run ../lab.py check 1.4
```

### ✱ Stretch

Make `/readyz` fail when the warm-up prediction disagrees with the artefact's reference prediction, then append a byte to a copy of `model.skops` and see which check catches it first.

## Check yourself

1. The model file is missing. What should the cluster do with this pod: restart it, or stop sending it traffic?
2. Why must `/livez` never depend on the model?
3. What does the first caller pay for when the model loads lazily?
