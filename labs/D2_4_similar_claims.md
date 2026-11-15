---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "2.4"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D2_4_similar_claims.html"
---

# Lab 2.4 · The similar-claims endpoint

Add the similar-claims endpoint and compare its memory use and start-up time with the classifier.

Day 2 · Session 4: Serving the embedding model

### Goal

Serve Shabih, which finds past claims like a new one, behind a versioned endpoint that returns no personal data, and measure how its memory and start-up compare with Farz to decide whether the two share a deployment.

## What you need

- The lab folder `rifd-labs/2.4`, with the Shabih artefact in `models/shabih-1.0.0` and the tests `tests/test_similar.py`
- `tools/measure.py`, which starts a service, times it to ready and reads its memory
- AI policy: tutor.

### Read the Shabih artefact and its index 4 min

```bash
# file: terminal
cd rifd-labs/2.4
cat models/shabih-1.0.0/metadata.json
uv run python -c "import json; print(json.load(open('models/shabih-1.0.0/items.json'))[0])"
```

The encoder turns a description into 96 numbers; the index holds one such vector for each of 50,000 past claims, and `items.json` says which claim each vector is, with no personal field.

### Add /v1/similar with a contract and no personal fields 9 min

In `src/rifd/routes_similar.py`, replace the TODO: search the index with `m.search(query.description, k=query.k, line=query.line)` inside a span named `similar`, and answer with the `Similar` schema and the model's name and version.

```bash
# file: terminal
uv run pytest tests/test_similar.py
RIFD_SERVICE=shabih uv run uvicorn rifd.app:app --port 8001 &
curl -s -X POST 127.0.0.1:8001/v1/similar -H "content-type: application/json" \
  -d '{"description": "Windscreen cracked by a stone on the highway", "k": 3}'
kill %1
```

### Measure memory and time to ready for both models 7 min

```bash
# file: terminal
uv run python tools/measure.py --service farz > runs/measure_farz.json
uv run python tools/measure.py --service shabih > runs/measure_shabih.json
cat runs/measure_*.json
```

Then write `k8s/shabih.yaml`: a deployment of its own with a memory limit sized from your measurement and a startup probe that waits long enough.

### Check 5 min

```bash
# file: terminal
uv run ../lab.py check 2.4
```

### ✱ Stretch

Halve the index with float16 vectors and measure what it saves and what it changes in the results.

## Check yourself

1. Which of the two services takes longer to load its model, and by how much?
2. Give one reason to run Shabih in its own deployment even though it uses the same image.
3. A description can mention a person by name. What does the endpoint return about the neighbours, and what does it never return?
