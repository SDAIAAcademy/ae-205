---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
scope: "course"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/"
---

# Deploying AI Services: Containers, Serving and Monitoring

Take a trained model from a notebook to a versioned, containerised, monitored service, size it against a latency objective, and release and roll it back on evidence

Participants take two trained models from a notebook to a monitored service. For a fictional mutual insurer they package a claims-triage classifier and a similar-claims embedding model with pinned dependencies, register model versions, serve them behind a versioned API with input validation, build and scan a container image, run it on a single-node local cluster with health checks, add metrics, structured logs and traces, load-test and size the service, release a new version by canary and roll it back, and detect drift in a replayed stream of claims.

- **Audience:** Practitioners. Graduates and early-career developers who have completed the FN courses or passed the placement test, and software engineers moving into AI work.
- **Prerequisites:** FN-102 Command Line, Git and Reproducible Projects; AE-201 Machine Learning Foundations and Model Evaluation; Runs commands in a Linux shell; Has trained a model and saved it to a file
- **Case study:** Rifd Mutual Insurance: Rifd Mutual Insurance is a fictional cooperative insurer whose claims team wants two notebook models in service: Farz, which triages each new motor, health or property claim, and Shabih, which finds similar past claims for an adjuster. Every lab works on 50,000 synthetic claims made by a seeded generator, the models the kit trains on a laptop processor, and four weeks of replayed claims with drift injected from the third week; the personal fields in the data are invented.

## Outcomes

- LO1 (Awareness): Explain the path from a trained model to a served prediction, naming the artefact, image, registry, runtime, endpoint and monitor at each step, given a deployment diagram with the components unlabelled
- LO2 (Applied): Prepare a model artefact with pinned dependencies, a version, an input and output signature and a reproducible build, given a trained model and its training script
- LO3 (Applied): Implement a versioned prediction API with input validation, typed errors and separate health and readiness checks, given the registered model and an API contract
- LO4 (Applied): Configure a container image for the service, scan it for vulnerabilities and run it with resource limits on a single-node cluster, given the service code and a base image
- LO5 (Applied): Implement metrics, structured logs and traces for the service and a dashboard for latency percentiles, error rate and prediction distribution, given the running service and a load generator
- LO6 (Applied): Measure latency and throughput under load and size workers and replicas to meet a latency objective at the lowest cost, given a target request rate and a 95th-percentile latency objective set by the insurer, on laptop CPUs
- LO7 (Performance): Deliver a new model version by canary release, decide on promotion or rollback from monitored metrics and detect drift in replayed traffic, given two model versions, four weeks of replayed claims with injected drift and written rollback criteria

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

## Day 2: Containers and a cluster

An image that is small, scanned and configured from outside, running on a local cluster

#### [day2#title] Containers and a cluster

*SDAIA Academy · Deploying AI Services: Containers, Serving and Monitoring*

Day 2: An image that is small, scanned and configured from outside, running on a local cluster

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-205

#### [day2#agenda] Containers and a cluster

*Today*

- **Session 1 · Images that are small and reproducible**: Layers and the build cache, multi-stage builds from the lock file, slim bases, a non-root user and what to leave out
- **Session 2 · Scanning and configuration**: What a scanner reads and reports, severities and fixed versions, secrets in image layers, and configuration from the environment
- **Session 3 · Running on a local cluster**: Deployments, services and probes, requests and limits, rolling updates, and where a service may run under data rules
- **Session 4 · Serving the embedding model**: An embedding model as a service: vectors and an index in memory, start-up time, a startup probe and a deployment of its own

### Session 1: Images that are small and reproducible

#### [day2#s1] Images that are small and reproducible

*Session 1*

- Read a container file and predict which layers a change rebuilds
- Write a multi-stage container file that installs from the lock file
- Measure image size and build time and explain the difference

#### [day2#what-an-image-is] An image is a stack of read-only layers and a few settings

*An image*

- Each `RUN`, `COPY` and `ADD` line adds a **layer**: the files it changed
- `ENV`, `USER`, `CMD` and `EXPOSE` only change the **configuration**, which anyone who pulls the image can read
- A container is the image plus one thin writable layer that disappears with it

- **In the case study.** One image, `rifd/claims:1.0.0`, serves both Farz and Shabih; `RIFD_SERVICE` picks which one starts.

#### [day2#build-cache] Change a file, and every layer after the line that copied it is rebuilt

*The build cache*

```docker
// file: Dockerfile.naive
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
```

```docker
// file: Dockerfile · build stage
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev
```

> **Order by how often things change.** The lock changes rarely, the code often: copy the lock first and the dependency layer stays cached.

#### [day2#multi-stage] Build in one stage, ship only the result from a second

*Multi-stage builds*

1. **Stage 1 · build** slim base, uv, the lock, `uv sync --frozen --no-dev`
2. **COPY --from=build** `.venv`, `src`; then `models/`
3. **Stage 2 · runtime** a fresh slim base, user 10001, no uv, no caches

> **Takeaway.** Whatever the build needed and the service does not stays in stage 1 and never ships.

#### [day2#base-and-user] A slim base and a non-root user cost nothing and remove a lot

*Two small lines*

- **python:3.12-slim.** Debian with the minimum Python needs. The full `python:3.12` image adds compilers and headers, which a service that installs wheels does not use and a scanner still reports.
- **USER 10001.** A process that escapes the service holds no root rights in the container. The cluster can enforce it with `runAsNonRoot` in the manifest.

> **What goes wrong.** A tag like `python:3` or `latest` moves under you: pin the tag, or the digest when two builds must be identical.

#### [day2#dockerignore] What the build never sees cannot leak into the image

*The build context*

```text
# file: .dockerignore
.venv
.git
tests
notebook
runs
secrets
.env
```

- The build sends the folder to the builder; `.dockerignore` leaves paths out
- `.venv` is built for your laptop, not the image
- `secrets` and `.env`: a later `COPY .` by a colleague would ship them
- Tests and the notebook are evidence for the repository, not the runtime

#### [day2#measure-image] Three numbers compare two container files

*Lab 2.1 · what to record*

|  | Dockerfile.naive | Dockerfile (multi-stage) |
| --- | --- | --- |
| Image size (`docker image ls`) | your number | your number; the check asks under 500 MB |
| First build time | your number | your number |
| Rebuild after a one-line code change | reinstalls everything | only the code layers |
| Runs as | root | user 10001 |

#### [day2#check-layers] What does this change rebuild?

*Checkpoint*

**Question:** A container file copies `pyproject.toml` and `uv.lock`, runs `uv sync --no-install-project`, copies `src`, and runs `uv sync` again. A colleague edits one function in `src/rifd/app.py` and rebuilds. What runs again?

- A. Every line, from the base image down
- B. The copy of src and the second uv sync, which installs only the project
- C. The first uv sync, because the dependencies must be checked
- D. Nothing, because the dependencies did not change

#### [day2#lab-2-1] A multi-stage container file

Lab 2.1 · 25 min

Write a multi-stage container file and compare its size and build time with a naive one.

[D2_1_multi_stage_image.html](https://sdaiaacademy.github.io/ae-205/labs/D2_1_multi_stage_image.html)

- [ ] Build the naive image; record size and time (5 min)
- [ ] Write the multi-stage file without AI help (10 min)
- [ ] Build it; record size, time and a rebuild after a code change (6 min)
- [ ] Check (4 min)
- [ ] ✱ Stretch: Pin the base image by digest and rebuild twice: do the two images have the same id?

### Session 2: Scanning and configuration

#### [day2#s2] Scanning and configuration

*Session 2*

- Read a vulnerability report and pick the finding to fix first
- Fix a finding by moving to a fixed version and scan again
- Move a secret out of an image into configuration the runtime supplies

#### [day2#what-a-scanner-reads] A scanner matches what is installed against lists of known flaws

*Vulnerability scanning*

- **It reads.**
  - the system packages of the base image
  - the language packages: a lock file, or the installed environment
- **It compares with.**
  - advisory databases such as OSV and the GitHub advisories
  - each advisory names affected versions and the version that fixes it

> **A scan is a date.** The same image scanned next month can report more: new advisories are published every day.

#### [day2#read-a-report] The supplied lock carries an h11 with a critical advisory

*Lab 2.2 · step 1*

```bash
# file: terminal
$ uv run pip-audit -r runs/requirements-audit.txt --no-deps --disable-pip --aliases
Found 2 known vulnerabilities in 1 package
Name Version ID             Fix Versions Aliases
---- ------- -------------- ------------ -----------------------------------
h11  0.14.0  PYSEC-2026-348 0.16.0       GHSA-vqfr-h8mv-ghfj, CVE-2025-43859
h11  0.14.0  PYSEC-2026-348 0.16.0       GHSA-vqfr-h8mv-ghfj, CVE-2025-43859
```

- **h11** parses HTTP/1.1 for uvicorn: it reads every request Farz receives
- One advisory, listed twice, rated **critical** by GitHub: lenient parsing of the line endings in chunked bodies allows **request smuggling** behind a proxy that parses differently

#### [day2#fix-first] Fix the most severe finding that has a fix, then scan again

*Which finding first*

1. **1 · Sort** by severity and by whether the code path is reachable
2. **2 · Fix** move to the fixed version: bound in pyproject, exact in the lock
3. **3 · Prove** rescan, run the tests, rebuild
4. **4 · Record** findings with no fix: advisory, reason, date to look again

> **What goes wrong.** Suppressing a finding in the scanner's configuration makes the report clean and leaves the flaw running.

#### [day2#secret-in-layers] A key in an ENV line is readable by anyone who can pull the image

*Secrets*

```docker
// file: supplied/Dockerfile
ENV RIFD_LOOKUP_KEY=rifd-lookup-key-for-the-labs-only \
    RIFD_MODEL_DIR=/app/models/farz-1.0.0
```

- `docker history --no-trunc` and `docker inspect` print it
- Deleting it in a later layer hides it, does not remove it
- Every pushed copy keeps it: **rotate** the key, then fix the file

> **Supply it at run time.** An environment variable from the runtime, a mounted file, or a cluster Secret; a key the build needs goes through BuildKit's `--mount=type=secret`.

#### [day2#config-from-env] The service reads its settings; the runtime decides them

*Configuration*

```python
# file: src/rifd/settings.py
def _secret(name: str) -> str:
    """A secret comes from the environment, or from a file the runtime mounts."""
    if os.environ.get(name):
        return os.environ[name]
    path = Path(os.environ.get(name + "_FILE", "secrets/lookup.key"))
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""

lookup_key: str = field(default_factory=lambda: _secret("RIFD_LOOKUP_KEY"))
```

- Same image in every environment; only the configuration differs
- `secrets/` is in `.gitignore` and `.dockerignore`

#### [day2#check-scan] Which finding do you fix first?

*Checkpoint*

**Question:** A scan of the fraud-review image reports: high, in the HTTP parser, fixed in the next version; critical, in an image library the service never imports, no fix; medium, in the base image, fixed by a newer base. Where do you start?

- A. The critical one, because it is critical
- B. The medium one, because a new base is the easiest change
- C. Suppress all three and scan again next quarter
- D. The high one in the HTTP parser: it is reachable by every request and has a fix

#### [day2#lab-2-2] Scan, fix, configure

Lab 2.2 · 25 min

Scan a supplied image, fix one critical finding and move secrets out of the image into configuration.

[D2_2_scan_and_config.html](https://sdaiaacademy.github.io/ae-205/labs/D2_2_scan_and_config.html)

- [ ] Scan the supplied image and read the report (6 min)
- [ ] Fix the critical finding and scan again (7 min)
- [ ] Find the key in the image history (4 min)
- [ ] Read the key from configuration instead (5 min)
- [ ] Check (3 min)
- [ ] ✱ Stretch: Scan the multi-stage image of lab 2.1 and compare the counts by severity

### Session 3: Running on a local cluster

#### [day2#s3] Running on a local cluster

*Session 3*

- Deploy a service with probes and resource limits to a single-node cluster
- Diagnose a pod that does not become ready from its events
- Decide where each service may run from its data classification

#### [day2#cluster-objects] You describe what should run; the cluster keeps it running

*A cluster in four objects*

- **Deployment.** How many copies of which image, with which settings; it replaces pods that die.
- **Pod.** One running copy: a container with its probes and limits.
- **Service.** One stable address in front of the ready pods that match its selector.
- **ConfigMap and Secret.** Settings, and keys, given to the pods as variables or files.

#### [day2#probes] Three probes, three different actions

*Probes*

| Probe | Farz asks | When it fails, the cluster |
| --- | --- | --- |
| startupProbe | `/readyz` every 2 s, up to 30 times | restarts the container after a minute; holds the other probes until it passes |
| readinessProbe | `/readyz` every 5 s | takes the pod out of the Service; does not restart it |
| livenessProbe | `/livez` every 10 s | restarts the container |

> **A slow start is not a dead process.** The startup probe gives the model time to load without loosening the liveness probe.

#### [day2#requests-limits] Requests place the pod; limits stop it from taking the node

*Requests and limits*

```yaml
# file: k8s/farz.yaml
resources:
  requests: {cpu: 250m, memory: 256Mi}
  limits:   {cpu: "1", memory: 512Mi}
```

- The scheduler places a pod on a node with room for its **requests**
- Over its **CPU limit**, a container is slowed down
- Over its **memory limit**, it is killed (`OOMKilled`) and restarted

> **What goes wrong.** No limits: one pod with a leak takes the node and its neighbours with it. Limits far below use: a restart loop under load.

#### [day2#pod-events] A pod that does not start says why in its events

*Lab 2.3 · step 2*

| Status or event | Usual cause | Look at |
| --- | --- | --- |
| ErrImagePull, ImagePullBackOff | the node cannot fetch the image: wrong tag, or `latest` with `Always` | the image name and the pull policy |
| CrashLoopBackOff | the process exits at start | `kubectl logs --previous` |
| Readiness probe failed | running, not ready: the model did not load | the body of `/readyz` |
| OOMKilled | memory above the limit | the limit against a measurement |

#### [day2#rolling-update] A rolling update replaces pods one at a time, behind readiness

*Changing what runs*

1. **1 · New pod** maxSurge 1: one extra pod with the new image
2. **2 · Ready?** it joins the Service only when `/readyz` passes
3. **3 · Old pod out** maxUnavailable 0: capacity never drops

> **Takeaway.** A version that never becomes ready never takes traffic: the rollout stops and the old pods keep serving.

#### [day2#replicas-autoscaling] A fixed number of replicas is a decision; an autoscaler makes it from a metric

*Replicas and autoscaling*

```yaml
# file: k8s/farz-hpa.yaml (not in the lab)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef: {kind: Deployment, name: farz}
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: {type: Utilization, averageUtilization: 60}
```

- `replicas: 2` in the Deployment: two pods, always
- The autoscaler compares a measured value with a target and sets the count: wanted = ceil(current × measured ÷ target)
- CPU utilisation is a share of the pod's **request**: no request, no autoscaling
- New pods take traffic only when ready: Farz's start-up time is the delay

#### [day2#placement] The data each service holds decides where it may run

*Where may it run?*

- The national **Data Classification Policy** has four levels: Top Secret, Secret, Restricted, Public
- Claims with names, national ids and health details: Rifd classifies them **Restricted** and keeps them on its in-Kingdom cluster
- A copy abroad is a **transfer** under the Personal Data Protection Law and its transfer regulation

- **The lab's table.** Farz, Shabih and the dashboards: what each holds, its level, where it may run, and who signs. Bassam Al-Jaber signs with Munira Al-Ajmi.

#### [day2#check-cluster] Why is this pod not ready?

*Checkpoint*

**Question:** A Farz pod shows Running with 0/1 ready. Its events repeat "Readiness probe failed: HTTP probe failed with statuscode: 503". The pod has never restarted. What is the most likely cause?

- A. The model did not load, so /readyz answers model-unavailable
- B. The image tag cannot be pulled
- C. The memory limit is too low
- D. The liveness probe path is wrong

#### [day2#lab-2-3] Deploy to a local cluster

Lab 2.3 · 25 min

Deploy the supplied service image to a single-node cluster with probes and resource limits, and decide where each service may run.

[D2_3_local_cluster.html](https://sdaiaacademy.github.io/ae-205/labs/D2_3_local_cluster.html)

- [ ] Create the cluster and load the image (5 min)
- [ ] Apply the supplied manifest; read why it fails (5 min)
- [ ] Add probes, limits and a pinned image (7 min)
- [ ] Fill the placement table for three services (5 min)
- [ ] Check (3 min)
- [ ] ✱ Stretch: Change the image tag and watch a rolling update replace the pods one at a time

### Session 4: Serving the embedding model

#### [day2#s4] Serving the embedding model

*Session 4*

- Serve a nearest-neighbour search behind a versioned endpoint
- Measure memory and time to ready for two models
- Decide whether two models share a deployment

#### [day2#meet-shabih] Shabih turns a description into 96 numbers and finds the nearest past claims

*The second model*

1. **Description** "Windscreen cracked by a stone on the highway"
2. **Encoder** character n-grams, then 96 dimensions, unit length
3. **Index** 50,000 vectors in memory; dot product with each
4. **Answer** the k nearest: claim id, line, incident, score

#### [day2#index-in-memory] The index lives in memory, and loading it is the slow part

*What it costs*

- **19 MB** 50,000 × 96 float32 numbers
- **586 ms** Shabih's model load, against 60 ms for Farz
- **+40 MiB** memory at ready, 223 against 184 MiB

Searching every vector is fine at this size. Beyond a few million, an approximate index (HNSW, IVF) trades a little recall for much less time.

#### [day2#similar-contract] /v1/similar returns claims, not people

*The contract*

```json
// file: POST /v1/similar
{"description": "Windscreen cracked by a stone",
 "line": "motor", "k": 3}
```

```json
// file: 200
{"results": [
  {"claim_id": "CLM-…", "line": "motor",
   "incident": "windscreen", "score": 0.9}, …],
 "model": {"name": "shabih", "version": "1.0.0"}}
```

> **Minimise at the source.** The index keeps claim id, line and incident type only: no name, national id or description can leak through an answer it does not hold.

#### [day2#share-or-split] Same image, separate deployments: the two models age differently

*One deployment or two?*

|  | Farz | Shabih |
| --- | --- | --- |
| Memory limit | 512Mi | 768Mi |
| Startup probe budget | 2 s × 30 | 2 s × 60 |
| Scales with | new claims | adjusters' searches |
| Released when | the triage model changes | the encoder or the index changes |

#### [day2#check-shabih] How should Shabih be deployed?

*Checkpoint*

**Question:** Shabih needs about 40 MiB more memory than Farz and loads ten times slower. Searches peak in the afternoon, when adjusters work; new claims arrive all day. The team wants to put both models in one pod to save a deployment. What do you advise?

- A. One pod with both models: fewer things to run
- B. Two images, because the models differ
- C. One image, two deployments, each with its own limits, startup probe and replica count
- D. Run Shabih as a nightly batch instead of a service

#### [day2#lab-2-4] The similar-claims endpoint

Lab 2.4 · 25 min

Add the similar-claims endpoint and compare its memory use and start-up time with the classifier.

[D2_4_similar_claims.html](https://sdaiaacademy.github.io/ae-205/labs/D2_4_similar_claims.html)

- [ ] Read the Shabih artefact and its index (4 min)
- [ ] Add /v1/similar with a contract and no personal fields (9 min)
- [ ] Measure memory and time to ready for both models (7 min)
- [ ] Check (5 min)
- [ ] ✱ Stretch: Halve the index with float16 vectors and measure what it saves and what it changes in the results

#### [day2#wrap-up] Three things to keep from today

*Day 2 · wrap-up*

- **Order layers by change.** Lock first, code last, two stages, a slim base and a non-root user.
- **Scan, fix, rescan, record.** Fix what is reachable and fixable; secrets come from the runtime and leaked ones are rotated.
- **Probes and limits are the contract with the cluster.** Ready decides traffic, alive decides restarts, and the data decides where it runs.

#### [day2#next] Day 3: observe and size

*Next*

- Metrics with percentiles, logs with no personal data, and a trace of one slow request
- A load test at three rates against Munira's objective: 95th percentile under 150 ms at 200 requests a second
- Workers, replicas and the cost of 1,000 predictions

## Day 3: Observe and size

Metrics, logs and traces that answer questions, then the load the service can carry and what it costs

#### [day3#title] Observe and size

*SDAIA Academy · Deploying AI Services: Containers, Serving and Monitoring*

Day 3: Metrics, logs and traces that answer questions, then the load the service can carry and what it costs

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-205

#### [day3#agenda] Observe and size

*Today*

- **Session 1 · Metrics that matter**: Rate, errors and duration, histograms and their buckets, percentiles, the distribution of predictions and dashboards defined as code
- **Session 2 · Logs and traces**: Structured logs with a request id, personal fields redacted at the edge, and traces that show where one slow request spent its time
- **Session 3 · Load testing**: Open and closed load, warm-up, steady rates, percentiles under load and the knee where latency breaks the objective
- **Session 4 · Sizing and cost**: Workers and replicas, concurrency on a processor, headroom, processor against graphics-processor serving and the cost of 1,000 predictions

### Session 1: Metrics that matter

#### [day3#s1] Metrics that matter

*Session 1*

- Instrument a service with request, error and latency metrics
- Compute the 50th, 95th and 99th percentiles from histogram buckets
- Define a dashboard as code with latency, errors and predictions

#### [day3#three-questions] Rate, errors and duration describe what every caller felt

*What to measure*

- **Rate.** Requests a second, by route. The claims system's traffic, as Farz saw it.
- **Errors.** The share of requests that failed, by status. A 5xx is Farz's fault; a 4xx is the caller's.
- **Duration.** How long requests took, as a distribution: percentiles, not an average.

> **A model adds a fourth.** What it predicted: the share of each label, by version.

#### [day3#metric-types] Counters only go up; a histogram counts observations into buckets

*Prometheus metric types*

| Type | What it holds | Farz uses it for |
| --- | --- | --- |
| Counter | a total that only increases; `rate()` turns it into a speed | `rifd_requests_total`, `rifd_predictions_total` |
| Gauge | a value that goes up and down | `rifd_model_ready` |
| Histogram | a count per bucket boundary, plus a sum and a count | `rifd_request_duration_seconds` |
| Summary | percentiles computed in the process | nothing: they cannot be added across replicas |

#### [day3#labels-cardinality] Every distinct set of label values is a new time series

*Labels*

```python
# file: src/rifd/metrics.py
self.predictions = Counter(
    "rifd_predictions",
    "Predictions made, by model version and label",
    ["model", "version", "label"])
```

- 2 versions × 3 labels: **6 series**
- Add `claim_id`: a series per claim, and the monitoring system stores every one
- A label value is also data that leaves the service: never a member field

#### [day3#histogram-quantile] histogram_quantile finds the bucket and draws a straight line inside it

*Percentiles from buckets*

```text
# file: PromQL
histogram_quantile(0.95,
  sum by (le) (rate(rifd_request_duration_seconds_bucket{route="/v1/triage"}[1m])))
```

> **Sum, then estimate.** Bucket rates add up across replicas; the 95th percentile of the sum is the 95th percentile of the service.

> **Only as precise as the buckets.** Farz's boundaries are 0.1, 0.15 and 0.2 around the objective; with only 0.1 and 0.5 the estimate could be anywhere in between.

#### [day3#prediction-panel] The share of each label is the first sign that something changed

*The model's own signal*

- **36%** fast track in the training claims
- **47%** standard
- **16%** investigate

The panel `sum by (version, label) (rate(rifd_predictions_total[1m]))` shows these shares live, per version. A canary whose shares differ by more than 10 points breaks one of Munira's rollback criteria on Day 4.

#### [day3#dashboard-as-code] The dashboard is a file in the repository, reviewed like code

*Dashboards as code*

- `monitoring/dashboard.json`: four panels, each a PromQL query
- Grafana loads it at start from `monitoring/grafana/` (provisioning)
- The lab's check reads the file: a test of the dashboard
- A change to a metric name breaks a test, not the on-call engineer's night

- **Four panels.** Requests a second by status; error ratio; p50, p95 and p99 of triage; predictions a second by version and label.

#### [day3#check-metrics] How do you get the service's 95th percentile?

*Checkpoint*

**Question:** Farz runs four replicas. Each exposes its latency histogram. The dashboard must show the 95th percentile of all triage requests in the last minute. Which query is right?

- A. avg of histogram_quantile(0.95, …) computed for each replica
- B. max of histogram_quantile(0.95, …) over the replicas
- C. rate of the duration sum divided by the rate of the count
- D. histogram_quantile(0.95, sum by (le) (rate(…_bucket[1m])))

#### [day3#lab-3-1] Rate, errors and latency

Lab 3.1 · 25 min

Expose request rate, error rate and latency histograms and graph the 50th, 95th and 99th percentiles.

[D3_1_metrics.html](https://sdaiaacademy.github.io/ae-205/labs/D3_1_metrics.html)

- [ ] Add the counters and the latency histogram (8 min)
- [ ] Add the prediction distribution (4 min)
- [ ] Drive traffic and compute the percentiles (7 min)
- [ ] Read the dashboard file; check (6 min)
- [ ] ✱ Stretch: Move the histogram buckets and see how far the estimated 95th percentile moves

### Session 2: Logs and traces

#### [day3#s2] Logs and traces

*Session 2*

- Write one structured log line per request with a request id
- Redact personal fields before they reach a log or a trace, and test it
- Follow one slow request through its spans to the slow step

#### [day3#structured-logs] One JSON line per event, with the fields you will search on

*Structured logs*

```json
// file: runs/service.log
{"claim_id": "CLM-050017", "line": "health", "label": "investigate", "version": "1.0.0",
 "event": "triage", "request_id": "bf97fe2e0dc94165", "level": "info", "timestamp": "2026-11-15T06:40:42Z"}
{"method": "POST", "route": "/v1/triage", "status": 200, "ms": 28.37,
 "event": "request", "request_id": "bf97fe2e0dc94165", "level": "info", "timestamp": "2026-11-15T06:40:42Z"}
```

- The **request id** joins every line of one request, and the claims system's own log
- Fields, not sentences: a query finds every investigate label of version 1.0.0

#### [day3#what-leaked] Half the start state's log lines held a national id or a mobile number

*Lab 3.2 · step 1*

**200 / 401** log lines with personal numbers after 200 claims

```python
# file: src/rifd/app.py · start state
logs.get().info("triage", claim=claim.model_dump(),
                label=out["label"], version=m.version)
```

> **What goes wrong.** Logging the whole object "for debugging" copies the member block into every log store, backup and search index.

#### [day3#redact-at-edge] Do not log it; then redact what slips through; then test both

*Redaction*

1. **1 · Do not log it** log claim id, line, label, version: never the body
2. **2 · Redact** a logger processor masks national ids, mobiles and member fields
3. **3 · Test** `tests/test_redaction.py` sends a claim and searches the log

> **The first line is the defence.** A pattern cannot know every way personal data is written; not logging the body can.

#### [day3#spans] A trace is one request; each span is one step inside it

*Traces*

| Span | Parent |
| --- | --- |
| `POST /v1/triage` | none: the root |
| `fastapi.endpoint` | the root |
| `triage` | fastapi.endpoint |
| `policy_lookup` | triage |
| `predict` | triage |

- Every span has a trace id, its own id, its parent's id and a duration
- OpenTelemetry writes them; the lab saves them to a file instead of a collector
- The same code sends them over OTLP in production

#### [day3#slow-request] The slowest request spent its time waiting for the policy system

*Lab 3.2 · step 3*

- **policy_lookup.** A 120 ms call to the policy system, made only for health claims outside the network: **7.0%** of 401 requests in the course's run.
- **predict.** About 2 ms. Making the model faster would change nothing the caller feels.

> **7% is more than 5%.** When more than one request in twenty takes the slow path, the 95th percentile falls inside it.

#### [day3#check-logs] Where should the national id stop?

*Checkpoint*

**Question:** The fraud-review service logs each request body at debug level, and the log search tool hides the national id field in its display. A colleague says that is enough. What do you answer?

- A. It is enough while debug logging stays off in production
- B. It is enough, because nobody sees the field
- C. It is not: the id is already stored; stop logging the body and test that no id reaches a log
- D. Encrypt the log store and keep logging the body

#### [day3#lab-3-2] Logs, redaction and a trace

Lab 3.2 · 25 min

Add structured logs with a request id, redact personal fields and follow one slow request through a trace.

[D3_2_logs_traces.html](https://sdaiaacademy.github.io/ae-205/labs/D3_2_logs_traces.html)

- [ ] Find the personal fields in the current logs (4 min)
- [ ] Log JSON with a request id; redact at the edge (9 min)
- [ ] Add spans; find the slowest request and its slow span (8 min)
- [ ] Check (4 min)
- [ ] ✱ Stretch: Pass the request id to the policy lookup as a header and see it in the lookup's own log

### Session 3: Load testing

#### [day3#s3] Load testing

*Session 3*

- Write a load test that sends realistic requests at a fixed rate
- Run it at three rates and read percentiles, errors and throughput
- Locate the rate at which the 95th percentile breaks the objective

#### [day3#the-objective] Munira's objective: 95% of claims answered within 150 ms at 200 a second

*The objective*

- **150 ms** 95th percentile, measured by the caller
- **200 / s** the peak after a sandstorm or a flood
- **1%** most errors allowed

Written in `../data/objective.json` by the owner of the service, before anyone measured anything.

#### [day3#open-closed] Real callers do not wait for each other: test with an open load

*Two kinds of load*

- **Closed.** N users, each sends the next request after the last answer. When Farz slows, the test sends less, and the queue a real caller meets never forms.
- **Open.** Requests leave on a schedule, 200 a second, whatever the answers do. A slowdown shows as a queue and a higher percentile.

> **What goes wrong.** A closed test reports good percentiles exactly when the service is overloaded.

#### [day3#realistic-requests] One claim a hundred times a second is not Farz's traffic

*Lab 3.3 · step 2*

|  | loadtest/one_claim.csv | ../data/replay/week1.csv |
| --- | --- | --- |
| Claims | one motor claim | 3,000 claims: motor, health, property |
| Calls the policy lookup | never | about 7% of claims |
| What its 95th percentile measures | the fast path only | the path a claims handler waits on |

#### [day3#warm-up-rates] Warm up, then hold each rate long enough to count its tail

*Running it*

```bash
# file: terminal
uv run python tools/loadtest.py --rates 80 150 220 --seconds 20 --warmup 3 \
  --file ../data/replay/week1.csv --label "1 worker" --out runs/load.json
```

- The warm-up is not counted: first connections and caches are not the steady state
- 20 s at 150 a second is 3,000 requests: 150 of them are in the slowest 5%
- Choose rates so that one holds the objective and one breaks it

#### [day3#the-knee] Latency stays flat, then rises sharply: that bend is the capacity

*Reading the result*

1. **Below the knee** p95 set by the slow path, about 120 to 130 ms
2. **At the knee** requests start to queue; p95 climbs past 150 ms
3. **Above it** the achieved rate stops following the target

> **Read three columns.** The 95th percentile, the error ratio, and whether the achieved rate kept up with the target.

#### [day3#check-load] What did this load test miss?

*Checkpoint*

**Question:** A team load-tests the fraud-review service with 50 users, each sending the next request when the last answer arrives. The 95th percentile stays at 40 ms while the service's own histogram shows 400 ms in the same minute. What explains it?

- A. A closed load: users waited for slow answers, so fewer requests were sent and timed exactly when it slowed
- B. The network between the test and the service
- C. The test had no warm-up
- D. The histogram buckets are too wide

#### [day3#lab-3-3] Three rates against the objective

Lab 3.3 · 25 min

Run a load test at three request rates and find where latency breaks the objective.

[D3_3_load_test.html](https://sdaiaacademy.github.io/ae-205/labs/D3_3_load_test.html)

- [ ] Read the objective and the locust file (4 min)
- [ ] Make the requests realistic (5 min)
- [ ] Run three rates with a warm-up (10 min)
- [ ] Report where the objective breaks; check (6 min)
- [ ] ✱ Stretch: Run the same rates with k6 and compare the two tools' numbers

### Session 4: Sizing and cost

#### [day3#s4] Sizing and cost

*Session 4*

- Measure the rate one worker carries within the objective
- Choose workers and replicas for a target rate with headroom
- Compute the cost per 1,000 predictions of a configuration

#### [day3#workers-replicas] Workers share a container; replicas are containers of their own

*Two ways to add capacity*

- **Workers.** `uvicorn --workers 2`: two Python processes in one container. Each holds its own copy of the model; together they use more than one processor.
- **Replicas.** `replicas: 3`: three pods, which the cluster can place on different nodes and replace one at a time.

> **One process per processor is the usual start.** Python runs one thread of Python code at a time per process, so a CPU-bound service scales with processes.

#### [day3#headroom] Run each replica below its measured capacity, and keep one spare

*From capacity to replicas*

```python
# file: tools/sizing.py
def replicas_needed(target_rps, capacity_rps, headroom, spare=1):
    return math.ceil(target_rps / (capacity_rps * (1 - headroom))) + spare
```

> **Headroom 30%.** A replica measured at 160 a second is planned at 112: bursts and a noisy neighbour stay inside the objective.

> **One spare.** A rolling update or a lost node takes one replica away without breaking the objective.

#### [day3#cost-per-1000] Cost per 1,000 predictions makes two configurations comparable

*The price of a prediction*

| Rifd's price sheet | SAR an hour |
| --- | --- |
| 1 vCPU | 0.19 |
| 1 GiB of memory | 0.025 |
| 1 GPU | 7.40 |

Three replicas of one worker (1 vCPU, 0.25 GiB each): 3 × 0.19625 = **SAR 0.589 an hour**.

200 a second is 720,000 predictions an hour: **SAR 0.00082 per 1,000**.

#### [day3#cpu-or-gpu] For Farz, a graphics processor would cost over twelve times more and help nothing

*Processor or graphics processor?*

**SAR 0.0103** per 1,000 predictions on one GPU replica alone, at 200 a second

- The model takes about a millisecond; the slow path is a 120 ms wait for another system
- A logistic regression on ten features has little to run in parallel
- Graphics processors pay off for large neural networks and batches

#### [day3#check-sizing] How many replicas?

*Checkpoint*

**Question:** One replica of the fraud-review service holds its objective up to 60 requests a second. The target is 150 a second. The team plans 20% headroom and one spare replica. How many replicas does it need?

- A. 4
- B. 5
- C. 6
- D. 3

#### [day3#lab-3-4] Workers, replicas and cost

Lab 3.4 · 25 min

Tune workers and replicas to meet the latency objective and compute cost per 1,000 predictions.

[D3_4_sizing_cost.html](https://sdaiaacademy.github.io/ae-205/labs/D3_4_sizing_cost.html)

- [ ] Measure one, two and four workers at the target rate (10 min)
- [ ] Choose workers and replicas with headroom (6 min)
- [ ] Compute cost per 1,000 predictions (5 min)
- [ ] Check (4 min)
- [ ] ✱ Stretch: Price the same load on the cheapest configuration that breaks the objective and say what Munira would lose

#### [day3#wrap-up] Three things to keep from today

*Day 3 · wrap-up*

- **Measure what callers feel.** Rate, errors, a latency histogram with buckets near the objective, and the label shares.
- **Never write what you must protect.** Log fields, not bodies; redact as a last defence; test it. Traces find the slow step.
- **Size from a realistic open load.** Find the knee, plan below it with headroom and a spare, and price it per 1,000.

#### [day3#next] Day 4: release and watch

*Next*

- A 10% canary of Farz 1.1.0, compared like with like
- A faulty 1.2.0, rolled back within five minutes on written criteria
- Drift in four weeks of claims, two alert rules and a runbook

## Day 4: Release and watch

Release a new version on evidence, roll back a bad one, watch the inputs drift and hand over to the on-call engineer

#### [day4#title] Release and watch

*SDAIA Academy · Deploying AI Services: Containers, Serving and Monitoring*

Day 4: Release a new version on evidence, roll back a bad one, watch the inputs drift and hand over to the on-call engineer

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-205

#### [day4#agenda] Release and watch

*Today*

- **Session 1 · Rolling, canary and shadow releases**: Blue-green, rolling, canary and shadow releases, and comparing a canary with the current version on the same metrics
- **Session 2 · Rollback on evidence**: Rollback criteria written before the release, who decides, rolling back first and diagnosing second
- **Session 3 · Drift in replayed traffic**: Data drift and concept drift, distribution tests and population stability, delayed labels and when drift should start a retraining
- **Session 4 · Alerts and a runbook**: Alerts on symptoms the caller feels, durations that stop flapping, a runbook the on-call engineer can follow and the person who decides a rollback

### Session 1: Rolling, canary and shadow releases

#### [day4#s1] Rolling, canary and shadow releases

*Session 1*

- Choose a release strategy for a change and its risk
- Send a fixed share of traffic to a new version
- Compare two versions on errors, latency and predictions

#### [day4#strategies] Four ways to put a new version in front of callers

*Release strategies*

| Strategy | What callers get | Answers the question |
| --- | --- | --- |
| Rolling | pods replaced one at a time; all traffic moves in minutes | does it start and stay ready? |
| Blue-green | a full second copy; one switch moves everything, one switch back | can we undo in seconds? |
| Canary | a small share, say 10%, then more if it holds | is it better, or at least no worse, on real traffic? |
| Shadow | none: a copy of each request goes to it and its answer is thrown away | how would it behave, with no caller at risk? |

#### [day4#choose-by-risk] Choose the strategy from what could go wrong, and for whom

*Choosing*

- **A fix to logging.** No change in predictions: a rolling update, watched by the probes.
- **Farz 1.1.0, a new algorithm.** Predictions change a little: a 10% canary with written criteria.
- **A new decision rule.** Who gets investigated changes: shadow first, then a canary.
- **A new contract version.** Callers must change too: a new path, `/v2/`, beside the old one.

#### [day4#router] A hash of the claim id decides which version answers

*Lab 4.1 · the router*

```python
# file: tools/router.py
def to_canary(claim_id: str) -> bool:
    bucket = int(hashlib.sha256(claim_id.encode()).hexdigest()[:8], 16) % 10000
    return bucket < STATE["weight"] * 10000
```

- The same claim always reaches the same version: a retry never gets a second opinion
- `POST /admin/weight` changes the share at once and records when and why
- On a cluster: two Deployments behind one Service in the ratio you want, or a weighted route of a gateway or service mesh

#### [day4#like-with-like] Compare the two versions on the same hour of the same traffic

*Comparing*

- **Errors**: the share of 5xx answers of each version
- **Latency**: the 95th percentile of each, measured by the caller
- **Label shares**: fast track, standard, investigate
- **Agreement** with the delayed labels that have arrived

> **What goes wrong.** Comparing the canary with last week's dashboard: the traffic of a Thursday after a storm is not the traffic of a quiet Sunday.

#### [day4#check-strategy] Which release strategy?

*Checkpoint*

**Question:** The fraud team has a new model that changes which claims are referred to investigators. The head of the team will not let any claim be referred by it until she has seen a week of its decisions on real claims. What do you propose?

- A. A 10% canary for a week
- B. A rolling update with readiness probes
- C. A shadow release for a week: copy each request to it and keep only the current model's answer
- D. Blue-green with a switch back if anything looks wrong

#### [day4#lab-4-1] A 10% canary

Lab 4.1 · 25 min

Send 10% of traffic to a new version and compare its metrics with the current one.

[D4_1_canary.html](https://sdaiaacademy.github.io/ae-205/labs/D4_1_canary.html)

- [ ] Start both versions and the router (5 min)
- [ ] Replay claims with 10% to the canary (7 min)
- [ ] Compare errors, latency and predictions (8 min)
- [ ] Write the release log entry; check (5 min)
- [ ] ✱ Stretch: Run 1.1.0 in shadow instead: copy every request to it, return only 1.0.0's answer, and compare

### Session 2: Rollback on evidence

#### [day4#s2] Rollback on evidence

*Session 2*

- Apply written rollback criteria to a canary's metrics
- Roll back within a time limit and record the evidence
- Name the person accountable for the decision

#### [day4#written-criteria] Write the criteria before the release, while nobody is attached to it

*Rollback criteria*

Judge only after **200** canary requests. Roll back when any one holds:

1. Errors (500 or 503) above **1%**
2. 95th percentile above **150 ms**
3. Any label share more than **10 points** from the current version's

- **Munira Al-Ajmi.** Wrote them, decides, and is accountable. The on-call engineer executes, and rolls back first when one fires.

#### [day4#who-decides] One named person decides; the criteria let anyone act at once

*Accountability*

1. **1 · A criterion fires** the watch prints which one
2. **2 · Roll back** the on-call engineer sets the share to 0
3. **3 · Tell** Munira, with the evidence files
4. **4 · Diagnose** after traffic is safe

> **Roll back first, diagnose second.** Every minute spent finding the cause is a minute of claims triaged by a faulty version.

#### [day4#faulty-release] Farz 1.2.0 answers fast, without errors, and sends too many claims to investigate

*Lab 4.2*

- **18%** investigate share of 1.1.0
- **38%** investigate share of the 1.2.0 canary
- **40 s** from the release to share 0

> **What goes wrong.** A dashboard of errors and latency stays green the whole time.

#### [day4#find-the-cause] The model file is fine; the decision rule beside it is not

*Diagnose second*

```json
// file: models/farz-1.1.0/metadata.json
"decision": {"investigate_threshold": 0.3}
```

```json
// file: models/farz-1.2.0/metadata.json
"decision": {"investigate_threshold": 0.05}
```

Day 1 put the decision rule into the artefact so that it travels with the model. That also means a release can change behaviour without changing a single weight.

#### [day4#evidence] A release log entry is the evidence an auditor will ask for

*The record*

| Row | Comes from |
| --- | --- |
| Canary requests judged, error ratio, p95, label shares | `runs/compare.json` |
| Seconds from the release to share 0, and the reason | `runs/router_events.jsonl` |
| Every answer after the rollback came from 1.1.0 | `runs/after_rollback.jsonl` |
| Cause, decided by, accountable | the metadata diff, and the runbook |

#### [day4#check-rollback] What does the on-call engineer do now?

*Checkpoint*

**Question:** At 02:10 a canary has served 350 requests. Errors and latency are normal, but its investigate share is 14 points above the current version's. Munira's criteria say more than 10 points means roll back. Munira is asleep. What should the engineer do?

- A. Set the canary's share to 0 now, then tell Munira with the evidence
- B. Wait for Munira to decide in the morning
- C. Keep the canary, since errors and latency are normal
- D. Find the cause first, then decide

#### [day4#lab-4-2] Roll back a faulty version

Lab 4.2 · 25 min

Trigger the rollback criteria with a seeded faulty version and roll back within five minutes.

[D4_2_rollback.html](https://sdaiaacademy.github.io/ae-205/labs/D4_2_rollback.html)

- [ ] Read the criteria; start the canary of 1.2.0 (5 min)
- [ ] Watch until a criterion fires (6 min)
- [ ] Roll back and time it (5 min)
- [ ] Find the cause; write the release log (6 min)
- [ ] Check (3 min)
- [ ] ✱ Stretch: Do the same rollback on the cluster with kubectl rollout undo and compare the time

### Session 3: Drift in replayed traffic

#### [day4#s3] Drift in replayed traffic

*Session 3*

- Compute a drift statistic per feature against the training data
- Name the shifted features and rule out a noisy one
- Say what delayed labels allow you to conclude, and when

#### [day4#two-drifts] The inputs can change, or what they mean can change

*Drift*

- **Data drift.** The distribution of the inputs moves: more claims through the app, larger motor amounts. Visible the day it happens.
- **Concept drift.** The link between inputs and the right label moves: the same claim should now be triaged differently. Visible only when the labels arrive.

> **Rifd's labels arrive about two weeks after a claim.** In week 4, weeks 1 and 2 are labelled; weeks 3 and 4 are not.

#### [day4#psi] PSI adds up how much each bin's share moved, weighted by how far

*Population stability index*

```python
# file: tools/drift.py
def psi_from_shares(expected, actual):
    e = np.clip(expected, EPS, None)
    a = np.clip(actual, EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))
```

- **< 0.1** stable
- **0.1 – 0.25** watch
- **≥ 0.25** shifted

#### [day4#ks-decoy] A p-value says a move is not chance; PSI says whether it matters

*Significant is not large*

| Week 3 | KS p-value | PSI | Verdict |
| --- | --- | --- | --- |
| policy tenure | 0.041 | 0.013 | moved about a month: negligible |
| channel | (category) | 0.277 | shifted |
| amount, all lines | 9e-32 | 0.075 | stable when pooled |

With 3,000 claims a week, a tiny move can be significant. Report it, then say it does not matter.

#### [day4#by-segment] Pooled over all lines the amount looks stable; motor amounts shifted

*Lab 4.3 · by line of business*

- **0.064** amount PSI, all lines, week 4
- **0.290** motor claims only
- **0.010 · 0.035** health · property

> **Compute drift where the model behaves differently.** A shift in a minority segment disappears in the pooled number.

#### [day4#what-labels-say] The predictions moved at once; whether they are wrong waits for labels

*What Rifd can conclude*

| Week | Investigate share of Farz 1.0.0 | Agreement with delayed labels |
| --- | --- | --- |
| 1 | 20% | 73.0% |
| 2 | 19% | 74.6% |
| 3 | 26% | not yet known |
| 4 | 26% | not yet known |

> **The retraining trigger.** Drift in the inputs starts a closer watch; agreement with the labels falling below an agreed level starts a retraining.

#### [day4#check-drift] What should the drift report say?

*Checkpoint*

**Question:** In week 3, the region mix has a PSI of 0.02. Customer age has a KS p-value of 0.001 and a PSI of 0.03. The channel has a PSI of 0.31. Labels for week 3 arrive in two weeks. Which summary is right?

- A. Age and channel shifted; the model is degrading
- B. Channel shifted, so accuracy has fallen and the model must be retrained now
- C. Nothing shifted: two of three features are stable
- D. Channel shifted; age moved slightly and does not matter; accuracy is unknown until the labels arrive

#### [day4#lab-4-3] Drift in four weeks

Lab 4.3 · 25 min

Replay four weeks of claims, compute a drift statistic per feature and name the shifted ones.

[D4_3_drift.html](https://sdaiaacademy.github.io/ae-205/labs/D4_3_drift.html)

- [ ] Replay the four weeks through the service (5 min)
- [ ] Compute population stability and a KS test per feature (9 min)
- [ ] Name the shifted features; check the labels you have (7 min)
- [ ] Write the drift report; check (4 min)
- [ ] ✱ Stretch: Recompute the statistics with Evidently and compare its verdicts with yours

### Session 4: Alerts and a runbook

#### [day4#s4] Alerts and a runbook

*Session 4*

- Write an alert rule on error ratio and one on latency
- Test both rules against a recorded error spike
- Write a one-page runbook with the accountable person

#### [day4#symptom-alerts] Alert on what callers feel, not on everything that can be measured

*Alerts*

- **Page someone.**
  - errors above 1% for two minutes
  - 95th percentile above 150 ms for five minutes
- **Put on a dashboard.**
  - CPU of one pod
  - one slow request
  - a label share moving slowly: a weekly drift report

> **What goes wrong.** An alert that fires and resolves by itself every few hours trains the on-call engineer to ignore it.

#### [day4#alert-rule] An expression, a duration, a severity and a runbook link

*A rule*

```yaml
# file: monitoring/alerts.yml
- alert: FarzLatencyP95High
  expr: histogram_quantile(0.95, sum by (le) (rate(rifd_request_duration_seconds_bucket{route="/v1/triage"}[5m]))) > 0.15
  for: 5m
  labels: {severity: page}
  annotations:
    summary: The 95th-percentile triage latency is above the 150 ms objective
    runbook_url: RUNBOOK.md#latency
```

#### [day4#test-on-recording] Test alerts on a recording, before they wake anyone

*Lab 4.4 · testing the rules*

| Rules | Blip at minute 6 | Errors, minutes 12 to 18 | Latency from minute 22 |
| --- | --- | --- | --- |
| Reference: errors 1m, for 2m; latency 5m, for 5m | quiet | fires 14.0 to 18.8 | fires from 28.0 |
| Same, no `for:` | quiet | fires from 12.0 | fires from 23.0 |
| Latency over 1m, no `for:` | fires 6.0 to 7.8 | unchanged rule: 14.0 to 18.8 | fires from 22.0 |

#### [day4#runbook] One page the on-call engineer can follow in the middle of the night

*The runbook*

- **Accountable for a rollback decision:** Munira Al-Ajmi
- For each alert: what the caller sees, the first three checks
- When to roll back, and the exact command
- Who to tell: Munira, the platform channel, Bassam if personal data may have leaked

- **Linked from the alert.** `runbook_url: RUNBOOK.md#errors`: the page opens from the notification.

#### [day4#choose-capstone] Choose the model you will take to a monitored service

*Tomorrow*

- **Farz.** The course's model, with every artefact you built this week.
- **Shabih.** The similar-claims model, with its own memory, start-up and release questions.
- **Your own.** A model from your work, with synthetic or public data only.

Write the choice, the reason and the objective you will defend in `CAPSTONE.md`.

#### [day4#check-alerts] Why does this alert flap?

*Checkpoint*

**Question:** An alert on the 95th-percentile latency uses a 30-second rate window and no for: duration. It fires for a minute about twice a day and resolves by itself. Callers never complain. What is the best first change?

- A. Raise the threshold to 300 ms
- B. Lengthen the window and add a for: duration, then test on a recording
- C. Send it to a wider group
- D. Delete the alert

#### [day4#lab-4-4] Two alerts and a runbook

Lab 4.4 · 25 min

Write two alert rules and a one-page runbook for the on-call engineer, then choose the capstone model.

[D4_4_alerts_runbook.html](https://sdaiaacademy.github.io/ae-205/labs/D4_4_alerts_runbook.html)

- [ ] Write the two rules without AI help (8 min)
- [ ] Test them on the recorded spike (6 min)
- [ ] Write the one-page runbook (8 min)
- [ ] Choose the capstone model; check (3 min)
- [ ] ✱ Stretch: Add a burn-rate alert on the error objective over two windows and test it on the same recording

#### [day4#wrap-up] Three things to keep from the course

*Day 4 · wrap-up*

- **Release on evidence.** A canary against written criteria, compared like with like, and a log entry with its files.
- **Roll back first.** A named person is accountable; the criteria let the person on call act at once.
- **Watch inputs, wait for labels.** Drift by segment, significant is not large, and alerts tested before they page.

#### [day4#next] Day 5: the capstone

*Next*

- Bring your `CAPSTONE.md` and a public GitHub repository with the service, its container file and manifests
- Dashboard and alerts as code, a load test against your objective, a recorded canary and rollback, a drift check
- Eight minutes to defend, four minutes of questions, one injected fault

## Capstone: Capstone: a monitored service and its defence

Eight minutes to show the service, four minutes of questions, and one fault injected by the assessor

#### [capstone#title] Capstone: a monitored service and its defence

*SDAIA Academy · Deploying AI Services: Containers, Serving and Monitoring*

Capstone: Eight minutes to show the service, four minutes of questions, and one fault injected by the assessor

AI Engineering Track · 4 teaching days + capstone day · 8 min talk and demo · 4 min Q&A · AE-205

#### [capstone#agenda] How the presentations run

*Capstone*

- **Expectations and final prep**: the rubric, a last rehearsal, then the first presentations
- **Presentations**: each one timed, with questions after it
- **Review and closing**: peer feedback, the trainer's review, what next

#### [capstone#rubric] The rubric

*How presentations are scored*

| Item | Value |
| --- | --- |
| Packaging and API | 20% |
| Container and deployment | 20% |
| Observability | 20% |
| Sizing against the objective | 15% |
| Release, rollback and drift | 25% |

> **Show results from at least two measured runs.** A claim without a number is a plan, not a result.

#### [capstone#format] 8 minutes to present, 4 to answer

*Format*

- **1 · The problem.** Who, what, why now. One slide.
- **2 · What you built.** Design, decisions, trade-offs. Then the live demo.
- **3 · What you measured.** Baseline, improvement, failures found, what comes next.

> **Peer feedback.** After each talk, everyone writes one strength, one question and one suggestion.

#### [capstone#what-to-submit] One public repository, and the command behind every number

*The submission*

- The service, its artefact and its contract tests
- A container file and the deployment manifests
- The dashboard and two alert rules, as files
- A README: load test against your objective, canary and rollback, drift check

> **No real personal data.** A public repository holds synthetic or public data only, and no key of any kind.

#### [capstone#injected-fault] The assessor breaks one thing; you show how you would know and what you do

*During the defence*

- **For example.** A model folder removed, a decision threshold changed, a slow dependency, a wrong image tag.
- **You show.** Which check, metric, alert or trace tells you, in your own running service.
- **You act.** Roll back, fix or explain, and say who you would tell.

#### [capstone#running-order] Who presents when

*Running order*

| # | Presenter | Project |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |
| 6 |  |  |
| 7 |  |  |
| 8 |  |  |

#### [capstone#final-prep] Final prep · 20 minutes

*Before the first presentation*

Rehearse once, record a backup, try the demo on this screen.

#### [capstone#now-presenting] Talk and demo

*Now presenting*

##### Questions

#### [capstone#review] What the presentations showed

*Trainer review*

- **Strongest patterns.** What several projects got right.
- **Common gaps.** What most projects would fix next.
- **One surprise.** Something nobody expected.

#### [capstone#what-next] Keep going

*After the course*

- **Your project stays yours:** keep it reproducible and add the next improvement you named today
- **Follow-up task:** run your capstone service on one week of replayed traffic and write a short incident note on what you saw
- **Next Academy courses:** AE-305, for retraining pipelines and online evaluation, and AE-307, for autoscaling and accelerators

#### [capstone#thanks] Thank you

*SDAIA Academy*

Deploying AI Services: Containers, Serving and Monitoring
