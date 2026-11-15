---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
deck: "day1"
day: 1
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/slides/day1.html"
---

# Deploying AI Services: Containers, Serving and Monitoring

## Day 1: Package and serve

From a notebook pickle to a versioned API that checks its inputs and says when it is ready

#### [day1#title] Package and serve

*SDAIA Academy · Deploying AI Services: Containers, Serving and Monitoring*

Day 1: From a notebook pickle to a versioned API that checks its inputs and says when it is ready

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-205

#### [day1#agenda] Package and serve

*Today*

- **Session 1 · From notebook to artefact**: The path from a trained model to a served prediction, serialisation formats, signatures, pins and the decision logic that hides in a notebook
- **Session 2 · A registry for model versions**: Immutable versions with metrics, tags and lineage, aliases for champion and challenger, and loading by version
- **Session 3 · A prediction API with a contract**: Online, batch and streaming prediction, a contract written first, input validation, typed errors and a version in the path
- **Session 4 · Health, readiness and warm-up**: Liveness and readiness as two questions, loading and warming the model at start, and what a service does when its model file is missing

#### [day1#meet-rifd] Rifd's claims team wants two notebook models in service

*The case study*

- **Farz · triage.** Every new motor, health or property claim gets fast track, standard or investigate.
- **Shabih · similar claims.** An adjuster describes a claim and gets the five most similar past claims.

- **Munira Al-Ajmi**, head of claims operations: owns the latency objective and decides rollbacks
- **Adel Al-Shaikh**, data scientist: trained both models in a notebook
- **Ghaida Al-Ruqi**, on-call platform engineer
- **Bassam Al-Jaber**, data protection officer
- **You**: the engineer who takes the models from the notebook to a monitored service

### Session 1: From notebook to artefact

#### [day1#s1] From notebook to artefact

*Session 1*

- Name the artefact, image, registry, runtime, endpoint and monitor on a deployment path
- Convert a notebook pickle into an artefact with a signature, pins and its decision rule
- Prove an artefact by reloading it in a clean environment against reference predictions

#### [day1#path-to-prediction] Six things stand between a trained model and a served prediction

*The path*

1. **Artefact** the model, its signature, its pins
2. **Registry** versions you can name
3. **Image** code, libraries, artefact
4. **Runtime** a cluster runs the image
5. **Endpoint** a versioned API
6. **Monitor** metrics, logs, traces

This course builds each box for Farz, one day at a time: artefact and endpoint today, image and runtime tomorrow, the monitor on Days 3 and 4.

#### [day1#the-handover] A notebook hand-over is a pickle, a script and a number

*What you are given*

- **Adel hands over.**
  - `farz_notebook.pkl`, the fitted pipeline
  - `train_triage.py`, the notebook as a script
  - macro F1 0.728 on 10,000 held-out claims
- **Nobody wrote down.**
  - which library versions load it
  - which inputs it expects, with which types
  - what the claims team does with the probabilities

> **What goes wrong.** The model "works on my machine" because the machine is the missing documentation.

#### [day1#serialisation-formats] A model file is either data or a program

*Serialisation formats*

| Format | What loading does | Portable across languages | Use it for |
| --- | --- | --- | --- |
| pickle, joblib | imports and calls whatever the file names | no | files you made yourself, once |
| skops | rebuilds only types on a trusted list | no (Python, scikit-learn) | scikit-learn models you share |
| ONNX | reads a graph of operators | yes | serving outside Python |
| framework formats | weights plus a known architecture | within the framework | deep learning models |

#### [day1#pickle-is-code] Read what a pickle imports before you load it

*Lab 1.1 · step 2*

```bash
# file: terminal
$ uv run python -m pickletools ../notebook/farz_notebook.pkl | grep sklearn
sklearn.feature_extraction._dict_vectorizer
sklearn.linear_model._logistic
sklearn.pipeline
sklearn.preprocessing._data
```

> **Load the pickle once,** where it was made or from someone you trust, and save it again in a safer format.

> **skops says what it does not trust.** Farz 1.1.0, a boosted model, holds one type that is not on the default list; the course's loader accepts it by name.

#### [day1#artefact-folder] Four files, each the answer to a question someone will ask

*An artefact*

- **model.skops.** What computes the probabilities? Saved so that loading runs no code.
- **signature.json.** What goes in and comes out? Ten input fields with types, three labels out.
- **metadata.json.** Which version, which data, which decision rule, which sha256, which ten reference predictions?
- **requirements.txt.** Which exact library versions load it? Six lines with `==`.

#### [day1#hidden-decision-rule] The pickle alone reproduced 8 of the notebook's 10 predictions

*Lab 1.1 · the planted problem*

**8 / 10** reference predictions matched before the rule was exported

```python
# file: notebook/train_triage.py · cell 14
INVESTIGATE_AT = 0.30

def label_from(proba):
    if proba["investigate"] >= INVESTIGATE_AT:
        return "investigate"
    return max(proba, key=proba.get)
```

CLM-041177: investigate 0.42, standard 0.57. The notebook says investigate; the pickle says standard.

#### [day1#pins-not-lock] The project's lock file and the artefact's pins answer different questions

*Recap from FN-102, one step further*

- **uv.lock (FN-102).** Every package of the project, for every platform: rebuilds the environment that develops and serves the service.
- **requirements.txt of the artefact.** The six libraries that load this model file, at the versions that wrote it: `scikit-learn==1.9.1`, `numpy==2.5.4`, `skops==0.16.0` and three more.

> **Proof, not belief.** An environment with only the pins must reproduce the ten reference predictions.

#### [day1#clean-reload] A clean environment holds the pins and nothing else

*A reproducible build*

```bash
# file: terminal
$ uv run --isolated --no-project --with-requirements artefacts/farz-1.0.0/requirements.txt \
    python tools/check_reload.py artefacts/farz-1.0.0
farz 1.0.0 loaded with pinned versions; 10 of 10 reference predictions match
  ok CLM-047849  expected investigate  got investigate
  ok CLM-049970  expected fast_track   got fast_track
  ...
```

#### [day1#check-artefact] What is missing from this artefact?

*Checkpoint*

**Question:** A colleague exports a churn model as model.skops, signature.json and requirements.txt with exact pins. A clean environment loads it and reproduces 7 of 10 reference predictions. The notebook ranked customers and called the top 5% at risk. What is missing?

- A. A safer format than skops
- B. Looser pins, so that the newest versions install
- C. The decision rule: the top-5% cut-off that turned scores into labels
- D. Twenty reference predictions instead of ten

#### [day1#lab-1-1] Export Farz as an artefact

Lab 1.1 · 25 min

Export the claims-triage model with its signature and pinned dependencies and reload it in a clean environment, reproducing ten reference predictions.

[D1_1_export_artefact.html](https://sdaiaacademy.github.io/ae-205/labs/D1_1_export_artefact.html)

- [ ] Build the workspace and open lab 1.1 (4 min)
- [ ] Load the notebook pickle and read what it needs (5 min)
- [ ] Export with a signature, pins and the decision rule (8 min)
- [ ] Reload in a clean environment; match ten predictions (6 min)
- [ ] Check (2 min)
- [ ] ✱ Stretch: Open the pickle with pickletools and list the imports it would run on load

### Session 2: A registry for model versions

#### [day1#s2] A registry for model versions

*Session 2*

- Register a model version with metrics, a data hash and a commit
- Explain why a registered version is never overwritten
- Load a model by version and by alias and say when to use each

#### [day1#why-registry] A registry answers "which model gave this answer?" in one lookup

*Why a registry*

- An adjuster disputes a triage: which version scored that claim, trained on which data?
- A canary misbehaves: what exactly changed between the two versions?
- An auditor asks for the model that ran in March: can you load it today?
- Two teams both say "the new model": are they talking about the same file?

> **What goes wrong.** A folder called `final_v2_really` on a shared drive answers none of these.

#### [day1#versions-never-change] A registered version never changes

*Lab 1.2 · step 3*

```bash
# file: terminal
$ uv run python -m rifd.registry register --name farz --version 1.0.0 --from models/farz-1.1.0
refused: farz 1.0.0 is already registered and versions never change:
register farz with a new version
```

A release log, a canary comparison and an incident note all say "farz 1.0.0". If the name could point at another file, none of them could be checked.

#### [day1#what-a-version-carries] A version carries its evidence and its lineage

*Metrics and tags*

| Field | Farz 1.0.0 in the course's run | Answers |
| --- | --- | --- |
| sha256 of the model file | `ee8e2221b179…` | is this the file that was registered? |
| metrics | macro F1 0.728, investigate recall 0.746 | how good was it when registered? |
| tag data_sha256 | hash of `claims.csv` | which data trained it? |
| tag trained_by | Adel Al-Shaikh | whom do I ask? |
| tag source | `notebook/train_triage.py` | which code made it? |

#### [day1#two-versions] 1.1.0 is better than 1.0.0, but only just

*The two supplied versions*

| Item | Value |
| --- | --- |
| 1.0.0 macro F1 | 0.728 |
| 1.1.0 macro F1 | 0.735 |
| 1.0.0 investigate recall | 0.746 |
| 1.1.0 investigate recall | 0.747 |

> **Decide on live evidence.** A gap this small on one held-out set does not justify a release by itself; Day 4's canary does.

#### [day1#aliases] An alias moves; a version does not

*Aliases*

- **farz@champion → 1.0.0.** Moving the alias changes what every reader of the alias loads, with no deployment.
- **farz 1.0.0.** Always the same file. A rollback is a change of one line in the manifest, and the manifest says what runs.

> **Rifd's rule.** Production names a version; staging and the weekly batch may follow `champion`.

#### [day1#registry-tools] Folder registry, MLflow and git tags share one model

*The same ideas, other tools*

| Idea | rifd.registry (the labs) | MLflow | Git repository of artefacts |
| --- | --- | --- | --- |
| A model | `--name farz` | registered model | a folder |
| A version | `--version 1.0.0` | model version | an annotated tag |
| Evidence | metrics, tags | run metrics, tags | files in the commit |
| A pointer that moves | alias | alias | a branch or a file of aliases |

#### [day1#lineage] From one prediction back to the data, in four hops

*Lineage*

1. **A response** `"model": {"version": "1.0.0"}`
2. **The registry** farz 1.0.0, sha256
3. **The tags** data_sha256, source
4. **The data** `claims.csv`, 40,000 rows

Session 3 puts the version in every response, so the first hop is always there.

#### [day1#check-registry] Retrained on one more month

*Checkpoint*

**Question:** Adel retrains Farz 1.0.0 with the same code on one more month of claims. Production names farz 1.0.0 in its manifest. What should be registered?

- A. A new version, 1.0.1 or 1.1.0, with the new data hash, while production keeps 1.0.0
- B. The new file as 1.0.0, so production picks it up
- C. Nothing: the code did not change
- D. Move the champion alias to the new file

#### [day1#lab-1-2] Register two versions

Lab 1.2 · 25 min

Register two supplied model versions with metrics and tags and load one by version.

[D1_2_registry.html](https://sdaiaacademy.github.io/ae-205/labs/D1_2_registry.html)

- [ ] Read the two supplied artefacts and their metrics (4 min)
- [ ] Register 1.0.0 and 1.1.0 with tags and a data hash (8 min)
- [ ] Try to overwrite 1.0.0 and read the refusal (3 min)
- [ ] Set the champion alias; load by version and by alias (7 min)
- [ ] Check (3 min)
- [ ] ✱ Stretch: Write the same two registrations as MLflow calls, or as git tags on an artefact repository

### Session 3: A prediction API with a contract

#### [day1#s3] A prediction API with a contract

*Session 3*

- Choose online, batch or streaming prediction for a use case
- Validate a request against a written contract before the model sees it
- Return typed errors that a caller can act on

#### [day1#serving-patterns] Online, batch or streaming: the caller decides

*Serving patterns*

| Pattern | The caller | At Rifd | What matters |
| --- | --- | --- | --- |
| Online | waits for the answer | Farz triages a claim as it is filed | latency, availability |
| Batch | reads the results later | every night, re-score open claims for the weekly review | throughput, cost, completeness |
| Streaming | an event arrives, a result is published | score each claim update from the claims system's event queue | ordering, back-pressure, duplicates |

#### [day1#contract-first] Write the contract before the code, and test the code against it

*Contract first*

```markdown
<!-- file: CONTRACT.md (excerpt) -->
| amount_sar        | number  | over 0, up to 5,000,000 |
| vehicle_age_years | integer | 0 to 60; motor: needed  |
| in_network        | boolean | health: needed          |
| member            | object  | never sent to the model,
                                never logged            |
```

- Agreed with the claims system's team: they build against it while you build the service
- Every rule becomes a test in `tests/test_contract.py`
- A change that breaks a caller is a new major version of the path

#### [day1#validate-before-model] Every field is checked before the model sees it

*Input validation*

```python
# file: src/rifd/schemas.py
class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line: Literal["motor", "health", "property"]
    amount_sar: float = Field(gt=0, le=5_000_000)
    vehicle_age_years: int | None = Field(default=None, ge=0, le=60)

    @model_validator(mode="after")
    def by_line(self):
        if self.line == "motor" and self.vehicle_age_years is None:
            raise ValueError("a motor claim needs vehicle_age_years")
        return self
```

#### [day1#typed-errors] A caller switches on the error's type, never on its text

*Typed errors*

| type | status | The caller |
| --- | --- | --- |
| `validation-error` | 422 | fixes the claim; never retries it as it is |
| `model-unavailable` | 503 | retries later, or sends the claim to manual triage |
| `dependency-failed` | 502 | retries later |
| `prediction-failed` | 500 | reports the request id |

> **What goes wrong.** A 200 with `"error": "bad input"` in the body: every dashboard counts it as a success.

#### [day1#problem-details] One shape for every error: RFC 9457

*Problem details*

```json
// file: 422 · application/problem+json
{
  "type": "urn:rifd:problem:validation-error",
  "title": "The claim does not match the contract",
  "status": 422,
  "detail": "1 field(s) failed validation",
  "instance": "/v1/triage",
  "errors": [{"field": "line", "message": "Input should be 'motor', 'health' or 'property'"}],
  "request_id": "3f1c9a0d7e2b4c55"
}
```

#### [day1#versioned-path] The path carries the contract's version; the body carries the model's

*Versions in two places*

- **/v1/triage.** Changes only when the contract breaks a caller. `/v2/` runs beside `/v1/` until every caller has moved.
- **"model": {"version": "1.1.0"}.** Changes with every release, contract unchanged. The first hop of lineage, and the field Day 4's canary comparison groups by.

#### [day1#personal-fields-dropped] The member's details are validated, then dropped before the model

*Personal data at the boundary*

1. **Request** claim + description + member
2. **Validated** national id: 10 digits, starts 1 or 2
3. **model_view()** the claim without member and text
4. **Farz** ten fields

> **Data minimisation in code.** What the model never receives, no model log or trace can leak.

#### [day1#contract-tests] Sixteen contract tests, from all failing to all passing

*Lab 1.3*

**0 → 16** of 16 contract tests passing, start state to finished, in the course's run

- valid motor and health claims, and the model version in the answer
- missing field, wrong type, out of range, unknown line, unknown field
- a motor claim without its vehicle age; a malformed national id
- a body that is not JSON; a request id on every response
- a model that fails to load: 503, `model-unavailable`

#### [day1#check-contract] A claim with an extra field

*Checkpoint*

**Question:** The claims system starts sending "fraud_flag": true with some claims. Farz's contract does not list the field. What should the service do?

- A. Ignore the field and triage the claim
- B. Pass it to the model as an eleventh feature
- C. Answer 500, prediction-failed
- D. Answer 422, validation-error, naming fraud_flag

#### [day1#lab-1-3] A versioned endpoint with a contract

Lab 1.3 · 25 min

Build a versioned prediction endpoint that validates inputs and returns typed errors, until the supplied contract tests pass.

[D1_3_prediction_api.html](https://sdaiaacademy.github.io/ae-205/labs/D1_3_prediction_api.html)

- [ ] Run the contract tests against the naive endpoint (3 min)
- [ ] Write the request and response schemas (8 min)
- [ ] Return problem details for each error type (8 min)
- [ ] Pass all contract tests (4 min)
- [ ] Check (2 min)
- [ ] ✱ Stretch: Add a batch endpoint that takes up to 100 claims and reports errors per item

### Session 4: Health, readiness and warm-up

#### [day1#s4] Health, readiness and warm-up

*Session 4*

- Separate a liveness check from a readiness check
- Load and warm a model before the service accepts traffic
- Show the behaviour of each check when the model file fails to load

#### [day1#two-questions] "Is it alive?" and "should it get traffic?" are two questions

*Health and readiness*

- **/livez · liveness.** Can the process answer at all? If not, restart it. Never looks at the model or at a dependency.
- **/readyz · readiness.** Is the model loaded, verified and warm? If not, send no traffic here, and do not restart.

> **What goes wrong.** One `/health` that says OK: traffic reaches a pod with no model, and every claim fails.

#### [day1#what-the-cluster-does] A wrong check turns a bad file into a restart loop

*What each failure means*

| Situation | /livez | /readyz | The cluster |
| --- | --- | --- | --- |
| Starting, model loading | 200 | 503 | waits; no traffic yet |
| Model file missing or altered | 200 | 503 | keeps it out of service; you read why |
| Process stuck | no answer | no answer | restarts it |
| Liveness that checks the model, file missing | 503 | 503 | restarts it, forever |

#### [day1#lazy-loading] Loading on the first request makes one caller pay for everyone

*Model loading and warm-up*

- **64 ms** to load and verify Farz 1.0.0
- **97 ms** for its first prediction, the warm-up

- Load at start, verify the sha256, then make one warm-up prediction
- The warm-up is checked against the artefact's reference label
- Only then does `/readyz` say ready

#### [day1#lifespan-load] Load and warm in the lifespan, before the first request

*Lab 1.4 · step 2*

```python
# file: src/rifd/app.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    logs.configure(s.log_file)
    load_farz(app)        # load, verify sha256, warm up; never raises
    yield

def load_farz(app):
    try:
        model = artefact.load(s.model_dir)
        warm = model.predict([model.meta["reference"][0]["input"]])
        ...
        app.state.ready = True
    except Exception as e:
        app.state.load_error = str(e)   # alive, not ready, and says why
```

#### [day1#missing-model] With the model file missing, the service is alive and says why it is not ready

*Lab 1.4 · step 4*

- GET /livez: `200 {"status": "alive"}`
- GET /readyz: `503 urn:rifd:problem:model-unavailable · no artefact at models/missing`
- POST /v1/triage: `503 urn:rifd:problem:model-unavailable`
- tests: `tests/test_health.py: 5 passed`

#### [day1#time-to-ready] Most of the time to ready is importing libraries, not loading the model

*Looking ahead to Day 2*

- In the course's runs, Farz took 11 to 22 seconds from process start to ready on a laptop
- Of that, loading the model took under a tenth of a second
- The rest was Python importing scikit-learn, skops and the web stack
- A cluster that gives up after five seconds restarts a healthy pod: Day 2 adds a **startup probe**

#### [day1#check-health] Which check fails?

*Checkpoint*

**Question:** A new Farz pod starts, but its model file was copied incompletely. The process is running and answers HTTP. What should /livez and /readyz answer?

- A. /livez 503, /readyz 503
- B. /livez 200, /readyz 503 with the reason
- C. /livez 200, /readyz 200, then 503 on each prediction
- D. /livez 503, /readyz 200

#### [day1#lab-1-4] Health and readiness checks

Lab 1.4 · 25 min

Add health and readiness checks and show how they differ when the model file is missing.

[D1_4_health_readiness.html](https://sdaiaacademy.github.io/ae-205/labs/D1_4_health_readiness.html)

- [ ] See the old health check say OK with no model (4 min)
- [ ] Load and warm the model in the lifespan (7 min)
- [ ] Write /livez and /readyz (6 min)
- [ ] Test both with the model file missing (6 min)
- [ ] Check (2 min)
- [ ] ✱ Stretch: Make /readyz fail when the warm-up prediction disagrees with the artefact's reference prediction

#### [day1#wrap-up] Three things to keep from today

*Day 1 · wrap-up*

- **The rule is part of the model.** An artefact holds the file, the signature, the decision rule and the pins, and proves itself on reference predictions.
- **Versions never change.** Every answer names its version; the registry turns the version into data, code and evidence.
- **The contract is tested.** Validation, typed errors, and two checks that say alive and ready separately.

#### [day1#next] Day 2: containers and a cluster

*Next*

- Start your container runtime (Docker or Podman) and check that `docker run hello-world` works
- Install kind, k3d or minikube and `kubectl`; the setup notes are in `labs/README.md`
- Lab 2.1's container file is written without AI help: read the pre-work on layers again
