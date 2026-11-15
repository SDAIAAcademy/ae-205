---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/index.html"
---

# Deploying AI Services: Containers, Serving and Monitoring

نشر خدمات الذكاء الاصطناعي: الحاويات وتقديم النماذج والمراقبة

AI Engineering Track · 4 teaching days + capstone day · 26 hours · Level 200

Take a trained model from a notebook to a versioned, containerised, monitored service, size it against a latency objective, and release and roll it back on evidence

Participants take two trained models from a notebook to a monitored service. For a fictional mutual insurer they package a claims-triage classifier and a similar-claims embedding model with pinned dependencies, register model versions, serve them behind a versioned API with input validation, build and scan a container image, run it on a single-node local cluster with health checks, add metrics, structured logs and traces, load-test and size the service, release a new version by canary and roll it back, and detect drift in a replayed stream of claims.

**Who it is for:** Practitioners. Graduates and early-career developers who have completed the FN courses or passed the placement test, and software engineers moving into AI work.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

## The case study

**Rifd Mutual Insurance.** Rifd Mutual Insurance is a fictional cooperative insurer whose claims team wants two notebook models in service: Farz, which triages each new motor, health or property claim, and Shabih, which finds similar past claims for an adjuster. Every lab works on 50,000 synthetic claims made by a seeded generator, the models the kit trains on a laptop processor, and four weeks of replayed claims with drift injected from the third week; the personal fields in the data are invented.

## The course

### Day 1: Package and serve

Slides: https://sdaiaacademy.github.io/ae-205/slides/day1.md

- **Session 1: From notebook to artefact**
  - Name the artefact, image, registry, runtime, endpoint and monitor on a deployment path
  - Convert a notebook pickle into an artefact with a signature, pins and its decision rule
  - Prove an artefact by reloading it in a clean environment against reference predictions
  - [Lab 1.1: Export Farz as an artefact (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D1_1_export_artefact.html)
- **Session 2: A registry for model versions**
  - Register a model version with metrics, a data hash and a commit
  - Explain why a registered version is never overwritten
  - Load a model by version and by alias and say when to use each
  - [Lab 1.2: Register two versions (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D1_2_registry.html)
- **Session 3: A prediction API with a contract**
  - Choose online, batch or streaming prediction for a use case
  - Validate a request against a written contract before the model sees it
  - Return typed errors that a caller can act on
  - [Lab 1.3: A versioned endpoint with a contract (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D1_3_prediction_api.html)
- **Session 4: Health, readiness and warm-up**
  - Separate a liveness check from a readiness check
  - Load and warm a model before the service accepts traffic
  - Show the behaviour of each check when the model file fails to load
  - [Lab 1.4: Health and readiness checks (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D1_4_health_readiness.html)

### Day 2: Containers and a cluster

Slides: https://sdaiaacademy.github.io/ae-205/slides/day2.md

- **Session 1: Images that are small and reproducible**
  - Read a container file and predict which layers a change rebuilds
  - Write a multi-stage container file that installs from the lock file
  - Measure image size and build time and explain the difference
  - [Lab 2.1: A multi-stage container file (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D2_1_multi_stage_image.html)
- **Session 2: Scanning and configuration**
  - Read a vulnerability report and pick the finding to fix first
  - Fix a finding by moving to a fixed version and scan again
  - Move a secret out of an image into configuration the runtime supplies
  - [Lab 2.2: Scan, fix, configure (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D2_2_scan_and_config.html)
- **Session 3: Running on a local cluster**
  - Deploy a service with probes and resource limits to a single-node cluster
  - Diagnose a pod that does not become ready from its events
  - Decide where each service may run from its data classification
  - [Lab 2.3: Deploy to a local cluster (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D2_3_local_cluster.html)
- **Session 4: Serving the embedding model**
  - Serve a nearest-neighbour search behind a versioned endpoint
  - Measure memory and time to ready for two models
  - Decide whether two models share a deployment
  - [Lab 2.4: The similar-claims endpoint (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D2_4_similar_claims.html)

### Day 3: Observe and size

Slides: https://sdaiaacademy.github.io/ae-205/slides/day3.md

- **Session 1: Metrics that matter**
  - Instrument a service with request, error and latency metrics
  - Compute the 50th, 95th and 99th percentiles from histogram buckets
  - Define a dashboard as code with latency, errors and predictions
  - [Lab 3.1: Rate, errors and latency (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D3_1_metrics.html)
- **Session 2: Logs and traces**
  - Write one structured log line per request with a request id
  - Redact personal fields before they reach a log or a trace, and test it
  - Follow one slow request through its spans to the slow step
  - [Lab 3.2: Logs, redaction and a trace (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D3_2_logs_traces.html)
- **Session 3: Load testing**
  - Write a load test that sends realistic requests at a fixed rate
  - Run it at three rates and read percentiles, errors and throughput
  - Locate the rate at which the 95th percentile breaks the objective
  - [Lab 3.3: Three rates against the objective (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D3_3_load_test.html)
- **Session 4: Sizing and cost**
  - Measure the rate one worker carries within the objective
  - Choose workers and replicas for a target rate with headroom
  - Compute the cost per 1,000 predictions of a configuration
  - [Lab 3.4: Workers, replicas and cost (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D3_4_sizing_cost.html)

### Day 4: Release and watch

Slides: https://sdaiaacademy.github.io/ae-205/slides/day4.md

- **Session 1: Rolling, canary and shadow releases**
  - Choose a release strategy for a change and its risk
  - Send a fixed share of traffic to a new version
  - Compare two versions on errors, latency and predictions
  - [Lab 4.1: A 10% canary (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D4_1_canary.html)
- **Session 2: Rollback on evidence**
  - Apply written rollback criteria to a canary's metrics
  - Roll back within a time limit and record the evidence
  - Name the person accountable for the decision
  - [Lab 4.2: Roll back a faulty version (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D4_2_rollback.html)
- **Session 3: Drift in replayed traffic**
  - Compute a drift statistic per feature against the training data
  - Name the shifted features and rule out a noisy one
  - Say what delayed labels allow you to conclude, and when
  - [Lab 4.3: Drift in four weeks (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D4_3_drift.html)
- **Session 4: Alerts and a runbook**
  - Write an alert rule on error ratio and one on latency
  - Test both rules against a recorded error spike
  - Write a one-page runbook with the accountable person
  - [Lab 4.4: Two alerts and a runbook (25 min)](https://sdaiaacademy.github.io/ae-205/labs/D4_4_alerts_runbook.html)

### Capstone: Capstone: a monitored service and its defence

Slides: https://sdaiaacademy.github.io/ae-205/slides/capstone.md

## Capstone

A model of the participant's choice taken to a monitored service, submitted as a public repository with container file, deployment manifests and dashboards as code, and a README reporting load-test results against a latency objective, a recorded canary release and rollback and a drift check, followed by an eight-minute defence and four minutes of questions

**What you submit:** A public GitHub repository link: the service with its container file, deployment manifests, dashboard and alert rules as code, and a README that reports the load-test results against a stated latency objective, the recorded canary release and rollback, and a drift check, with the command that produced each number.

**Rubric:**

- Packaging and API: 20%
- Container and deployment: 20%
- Observability: 20%
- Sizing against the objective: 15%
- Release, rollback and drift: 25%

## Outcomes

- **LO1** Explain the path from a trained model to a served prediction, naming the artefact, image, registry, runtime, endpoint and monitor at each step, given a deployment diagram with the components unlabelled (Awareness) Evidence: a labelled diagram with a one-sentence role for each component, scored against the reference
- **LO2** Prepare a model artefact with pinned dependencies, a version, an input and output signature and a reproducible build, given a trained model and its training script (Applied) Evidence: a registered model version that a fresh environment loads and that reproduces ten reference predictions
- **LO3** Implement a versioned prediction API with input validation, typed errors and separate health and readiness checks, given the registered model and an API contract (Applied) Evidence: a passing contract test suite, including malformed inputs and a model file that fails to load
- **LO4** Configure a container image for the service, scan it for vulnerabilities and run it with resource limits on a single-node cluster, given the service code and a base image (Applied) Evidence: an image under a stated size, a scan report with no critical findings and a deployment that passes its readiness check
- **LO5** Implement metrics, structured logs and traces for the service and a dashboard for latency percentiles, error rate and prediction distribution, given the running service and a load generator (Applied) Evidence: a dashboard defined as code and an alert rule that fires on a seeded error spike
- **LO6** Measure latency and throughput under load and size workers and replicas to meet a latency objective at the lowest cost, given a target request rate and a 95th-percentile latency objective set by the insurer, on laptop CPUs (Applied) Evidence: a load-test report with the chosen configuration and its cost per 1,000 predictions
- **LO7** Deliver a new model version by canary release, decide on promotion or rollback from monitored metrics and detect drift in replayed traffic, given two model versions, four weeks of replayed claims with injected drift and written rollback criteria (Performance) Evidence: a release log with the decision and its evidence, a completed rollback and a drift report naming the shifted features

## Tools

- **Container runtime and image builder:** Podman, Docker
- **Local single-node cluster:** kind, k3d, minikube
- **Model registry and tracking:** MLflow, a Git repository with tagged artefacts
- **Serving framework:** FastAPI, Ray Serve, KServe
- **Metrics, dashboards and alerts:** Prometheus with Grafana, OpenTelemetry Collector with any compatible back end
- **Tracing and structured logging:** OpenTelemetry, structlog
- **Image vulnerability scanning:** Trivy, Grype
- **Load testing:** Locust, k6
- **Drift statistics:** SciPy, Evidently

## Prerequisites

- FN-102 Command Line, Git and Reproducible Projects
- AE-201 Machine Learning Foundations and Model Evaluation
- Runs commands in a Linux shell
- Has trained a model and saved it to a file

## Sources

### Containers and clusters

- [Docker Docs: Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Docs: Building best practices](https://docs.docker.com/build/building/best-practices/)
- [uv: Using uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [uv: Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [Podman: Getting started](https://podman.io/docs)
- [Kubernetes: Liveness, readiness and startup probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
- [Kubernetes: Configure liveness, readiness and startup probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Kubernetes: Resource management for pods and containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes: Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes: Horizontal Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/)
- [Kubernetes: Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [kind: Quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [k3d (repository)](https://github.com/k3d-io/k3d)
- [minikube start](https://minikube.sigs.k8s.io/docs/start/)
- [The Twelve-Factor App: Config](https://12factor.net/config)

### Scanning

- [Trivy documentation](https://trivy.dev/latest/docs/)
- [Grype (repository)](https://github.com/anchore/grype)
- [pip-audit (repository)](https://github.com/pypa/pip-audit)
- [OSV: Open Source Vulnerabilities](https://osv.dev/)

### Artefacts, registries and serving

- [Python: pickle (the security warning)](https://docs.python.org/3/library/pickle.html)
- [skops: Secure persistence](https://skops.readthedocs.io/en/stable/persistence.html)
- [MLflow: Model registry](https://mlflow.org/docs/latest/ml/model-registry/)
- [MLflow: Model signatures and input examples](https://mlflow.org/docs/latest/ml/model/signatures/)
- [FastAPI: Handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI: Testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [FastAPI in containers](https://fastapi.tiangolo.com/deployment/docker/)
- [Uvicorn: Deployment](https://uvicorn.dev/deployment/)
- [Pydantic: Models](https://docs.pydantic.dev/latest/concepts/models/)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [Ray Serve](https://docs.ray.io/en/latest/serve/index.html)
- [KServe](https://kserve.github.io/website/)

### Observability, load and releases

- [Prometheus: Histograms and summaries](https://prometheus.io/docs/practices/histograms/)
- [Prometheus: Query functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Prometheus: Alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Prometheus Python client](https://prometheus.github.io/client_python/)
- [Grafana: Dashboard JSON model](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/)
- [OpenTelemetry: Python](https://opentelemetry.io/docs/languages/python/)
- [OpenTelemetry: Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
- [structlog documentation](https://www.structlog.org/en/stable/)
- [Locust documentation](https://docs.locust.io/en/stable/)
- [Grafana k6 documentation](https://grafana.com/docs/k6/latest/)
- [Google SRE book: Monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Google SRE workbook: Canarying releases](https://sre.google/workbook/canarying-releases/)
- [Google SRE workbook: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
- [SciPy: ks_2samp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html)
- [Evidently documentation](https://docs.evidentlyai.com/)

### National references

- [Personal Data Protection Law (SDAIA)](https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf)
- [Implementing Regulation of the Personal Data Protection Law (SDAIA)](https://sdaia.gov.sa/en/SDAIA/about/Documents/ImplementingRegulationPersonalDataProtectionLaw.pdf)
- [Regulation on Personal Data Transfer outside the Kingdom (SDAIA)](https://sdaia.gov.sa/Documents/RegulationonPersonalDataEN.pdf)
- [Data Classification Policy (NDMO, SDAIA)](https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf)
- [AI Ethics Principles (SDAIA)](https://sdaia.gov.sa/en/SDAIA/about/Documents/ai-principles.pdf)
- [National Cybersecurity Authority: Cloud Cybersecurity Controls](https://nca.gov.sa/en/regulatory-documents/controls-list/ccc/)

---

SDAIA Academy · AI Engineering Track · Deploying AI Services: Containers, Serving and Monitoring

Course version 2027.1.0 · engine 1.0.0 · built 2026-11-15 · commit fec8449
