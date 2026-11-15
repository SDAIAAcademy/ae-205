---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "1.3"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D1_3_prediction_api.html"
---

# Lab 1.3 · A versioned endpoint with a contract

Build a versioned prediction endpoint that validates inputs and returns typed errors, until the supplied contract tests pass.

Day 1 · Session 3: A prediction API with a contract

### Goal

Make Farz's endpoint keep the contract the claims system agreed to: a versioned path, every field checked before the model sees it, and an error of a known type for every way a request can fail. The contract tests are supplied; you make them pass.

## What you need

- The lab folder `rifd-labs/1.3`, with `CONTRACT.md` and `tests/test_contract.py`
- A serving framework: FastAPI with Pydantic here; Ray Serve and KServe put the same contract in front of a model
- AI policy: tutor.

### Run the contract tests against the naive endpoint 3 min

```bash
# file: terminal
cd rifd-labs/1.3
uv run pytest tests/test_contract.py
```

Read `CONTRACT.md` while they run. Every test is one sentence of the contract.

### Write the request and response schemas 8 min

In `src/rifd/schemas.py`, give each field of `Claim` its type and its rule from the contract, refuse unknown fields, and add the check that a motor claim carries its vehicle age and police report and a health claim says whether the provider is in the network.

### Return problem details for each error type 8 min

In `src/rifd/errors.py`, write the two handlers marked TODO with the `problem()` helper: a validation error lists each failed field; a `ServiceError` keeps its own type. In `src/rifd/app.py`, move the route to `/v1/triage`, declare `response_model=Triage` and return the model's name and version with every answer.

```bash
# file: terminal
uv run uvicorn rifd.app:app --port 8000 &
curl -s -X POST 127.0.0.1:8000/v1/triage -H "content-type: application/json" \
  -d '{"claim_id":"CLM-050123","line":"marine"}'
```

### Pass all contract tests 4 min

```bash
# file: terminal
uv run pytest tests/test_contract.py
```

### Check 2 min

```bash
# file: terminal
uv run ../lab.py check 1.3
```

Stop the server you started (`kill %1`, or close its terminal).

### ✱ Stretch

Add `POST /v1/triage/batch` that takes up to 100 claims and answers each one, with a problem detail per claim that fails, so that one bad claim does not fail the other 99.

## Check yourself

1. Why does the API refuse a field it does not know, instead of ignoring it?
2. A caller gets 422 and a caller gets 503. Which one should retry?
3. Where does the member's national id go once the claim is valid?
