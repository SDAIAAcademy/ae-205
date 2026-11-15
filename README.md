<!-- academy:title -->
# Deploying AI Services: Containers, Serving and Monitoring

نشر خدمات الذكاء الاصطناعي: الحاويات وخدمة النماذج والمراقبة

AI Engineering Track · SDAIA Academy · AE-205 · Level 200

REPLACE: one line under the title: what participants can do after the course

Participants take two trained models from a notebook to a monitored service. For a fictional mutual insurer they package a claims-triage classifier and a similar-claims embedding model with pinned dependencies, register model versions, serve them behind a versioned API with input validation, build and scan a container image, run it on a single-node local cluster with health checks, add metrics, structured logs and traces, load-test and size the service, release a new version by canary and roll it back, and detect drift in a replayed stream of claims.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

**Course page:** https://sdaiaacademy.github.io/ae-205/
<!-- /academy:title -->

## Outcomes

| | Outcomes | Level | Evidence |
|---|---|---|---|
| LO1 | Explain the path from a trained model to a served prediction, naming the artefact, image, registry, runtime, endpoint and monitor at each step, given a deployment diagram with the components unlabelled | Awareness | a labelled diagram with a one-sentence role for each component, scored against the reference |
| LO2 | Prepare a model artefact with pinned dependencies, a version, an input and output signature and a reproducible build, given a trained model and its training script | Applied | a registered model version that a fresh environment loads and that reproduces ten reference predictions |
| LO3 | Implement a versioned prediction API with input validation, typed errors and separate health and readiness checks, given the registered model and an API contract | Applied | a passing contract test suite, including malformed inputs and a model file that fails to load |
| LO4 | Configure a container image for the service, scan it for vulnerabilities and run it with resource limits on a single-node cluster, given the service code and a base image | Applied | an image under a stated size, a scan report with no critical findings and a deployment that passes its readiness check |
| LO5 | Implement metrics, structured logs and traces for the service and a dashboard for latency percentiles, error rate and prediction distribution, given the running service and a load generator | Applied | a dashboard defined as code and an alert rule that fires on a seeded error spike |
| LO6 | Measure latency and throughput under load and size workers and replicas to meet a latency objective at the lowest cost, given a target request rate and a 95th-percentile latency objective set by the insurer, on laptop CPUs | Applied | a load-test report with the chosen configuration and its cost per 1,000 predictions |
| LO7 | Deliver a new model version by canary release, decide on promotion or rollback from monitored metrics and detect drift in replayed traffic, given two model versions, four weeks of replayed claims with injected drift and written rollback criteria | Performance | a release log with the decision and its evidence, a completed rollback and a drift report naming the shifted features |

<!-- academy:units -->
## Units

| Unit | Title | Sessions | Slides |
|---|---|---|---|
| Day 1 | Package and serve | From notebook to artefact; A registry for model versions; A prediction API with a contract; Health, readiness and warm-up | [`slides/day1.html`](slides/day1.html) |
| Day 2 | Containers and a cluster | Images that are small and reproducible; Scanning and configuration; Running on a local cluster; Serving the embedding model | [`slides/day2.html`](slides/day2.html) |
| Day 3 | Observe and size | Metrics that matter; Logs and traces; Load testing; Sizing and cost | [`slides/day3.html`](slides/day3.html) |
| Day 4 | Release and watch | Rolling, canary and shadow releases; Rollback on evidence; Drift in replayed traffic; Alerts and a runbook | [`slides/day4.html`](slides/day4.html) |
| Capstone | Capstone project presentations |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**REPLACE: the name of the fictional organisation every lab works on.** REPLACE: two sentences on the case study and its synthetic data

<!-- academy:labs -->
## Labs

Every lab is a page in `labs/`, opened from the course page and from the lab slide of its session.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | Export the claims-triage model with its signature and pinned dependencies and reload it in a clean environment | [`D1_1_export_claims_triage.html`](labs/D1_1_export_claims_triage.html) |
| 1.2 | Day 1 · Session 2 | Register two supplied model versions with metrics and tags and load one by version | [`D1_2_register_two_supplied.html`](labs/D1_2_register_two_supplied.html) |
| 1.3 | Day 1 · Session 3 | Build a versioned prediction endpoint that validates inputs and returns typed errors | [`D1_3_build_versioned_prediction.html`](labs/D1_3_build_versioned_prediction.html) |
| 1.4 | Day 1 · Session 4 | Add health and readiness checks and show how they differ when the model file is missing | [`D1_4_add_health_readiness.html`](labs/D1_4_add_health_readiness.html) |
| 2.1 | Day 2 · Session 1 | Write a multi-stage container file and compare its size and build time with a naive one | [`D2_1_write_multi_stage.html`](labs/D2_1_write_multi_stage.html) |
| 2.2 | Day 2 · Session 2 | Scan a supplied image, fix one critical finding and move secrets out of the image into configuration | [`D2_2_scan_supplied_image.html`](labs/D2_2_scan_supplied_image.html) |
| 2.3 | Day 2 · Session 3 | Deploy the supplied service image to a single-node cluster with probes and resource limits | [`D2_3_deploy_supplied_service.html`](labs/D2_3_deploy_supplied_service.html) |
| 2.4 | Day 2 · Session 4 | Add the similar-claims endpoint and compare its memory use and start-up time with the classifier | [`D2_4_add_similar_claims.html`](labs/D2_4_add_similar_claims.html) |
| 3.1 | Day 3 · Session 1 | Expose request rate, error rate and latency histograms and graph the 50th, 95th and 99th percentiles | [`D3_1_expose_request_rate.html`](labs/D3_1_expose_request_rate.html) |
| 3.2 | Day 3 · Session 2 | Add structured logs with a request id, redact personal fields and follow one slow request through a trace | [`D3_2_add_structured_logs.html`](labs/D3_2_add_structured_logs.html) |
| 3.3 | Day 3 · Session 3 | Run a load test at three request rates and find where latency breaks the objective | [`D3_3_run_load_test.html`](labs/D3_3_run_load_test.html) |
| 3.4 | Day 3 · Session 4 | Tune workers and replicas to meet the latency objective and compute cost per 1,000 predictions | [`D3_4_tune_workers_replicas.html`](labs/D3_4_tune_workers_replicas.html) |
| 4.1 | Day 4 · Session 1 | Send 10% of traffic to a new version and compare its metrics with the current one | [`D4_1_send_10_traffic.html`](labs/D4_1_send_10_traffic.html) |
| 4.2 | Day 4 · Session 2 | Trigger the rollback criteria with a seeded faulty version and roll back within five minutes | [`D4_2_trigger_rollback_criteria.html`](labs/D4_2_trigger_rollback_criteria.html) |
| 4.3 | Day 4 · Session 3 | Replay four weeks of claims, compute a drift statistic per feature and name the shifted ones | [`D4_3_replay_four_weeks.html`](labs/D4_3_replay_four_weeks.html) |
| 4.4 | Day 4 · Session 4 | Write two alert rules and a one-page runbook for the on-call engineer, then choose the capstone model | [`D4_4_write_two_alert.html`](labs/D4_4_write_two_alert.html) |
<!-- /academy:labs -->

## Capstone

A model of the participant's choice taken to a monitored service, submitted as a public repository with container file, deployment manifests and dashboards as code, and a README reporting load-test results against a latency objective, a recorded canary release and rollback and a drift check, followed by an eight-minute defence and four minutes of questions

**Submission:** REPLACE: what participants submit and how: a public repository link, or a shared folder for a course without code

## Prerequisites

- FN-102 Command Line, Git and Reproducible Projects
- AE-201 Machine Learning Foundations and Model Evaluation
- Runs commands in a Linux shell
- Has trained a model and saved it to a file

<!-- academy:tools -->
## Tools

Each line is a capability; the examples are interchangeable.

- **Container runtime and image builder:** Podman, Docker
- **Local single-node cluster:** kind, k3d, minikube
- **Model registry and tracking:** MLflow, a Git repository with tagged artefacts
- **Serving framework:** FastAPI, Ray Serve, KServe
- **Metrics, dashboards and alerts:** Prometheus with Grafana, OpenTelemetry Collector with any compatible back end
- **Tracing and structured logging:** OpenTelemetry, structlog
- **Image vulnerability scanning:** Trivy, Grype
- **Load testing:** Locust, k6
- **Drift statistics:** SciPy, Evidently
<!-- /academy:tools -->

<!-- academy:sources -->
## Sources

- REPLACE: every source the course cites, with its address, in course.json under "sources"; this list is written from there
<!-- /academy:sources -->

### National references

- Personal Data Protection Law and its implementing regulations: REPLACE: the address of the official text
- Regulation on Personal Data Transfer outside the Kingdom: REPLACE: the address of the official text
- NDMO Data Classification Policy: REPLACE: the address of the official text
- National Cybersecurity Authority (NCA) Cloud Cybersecurity Controls: REPLACE: the address of the official text
- SDAIA AI Ethics Principles: REPLACE: the address of the official text
