<!-- academy:title -->
# Deploying AI Services: Containers, Serving and Monitoring

نشر خدمات الذكاء الاصطناعي: الحاويات وخدمة النماذج والمراقبة

AI Engineering Track · SDAIA Academy · AE-205 · Level 200

Take a trained model from a notebook to a versioned, containerised, monitored service, size it against a latency objective, and release and roll it back on evidence

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
| Capstone | Capstone: a monitored service and its defence |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**Rifd Mutual Insurance.** A fictional cooperative insurer whose claims team wants two notebook models in service: Farz, which triages each new motor, health or property claim into fast track, standard or investigate, and Shabih, which finds similar past claims for an adjuster. Every lab works on 50,000 synthetic claims from a seeded generator, the models the lab kit trains on a laptop processor, and four weeks of replayed claims with drift injected from the third week. The people (Munira Al-Ajmi, head of claims operations; Adel Al-Shaikh, data scientist; Ghaida Al-Ruqi, on-call engineer; Bassam Al-Jaber, data protection officer; Kholoud Al-Ghannam, senior adjuster) and every name, national id and mobile number in the data are invented.

<!-- academy:labs -->
## Labs

Every lab is a page in `labs/`, opened from the course page and from the lab slide of its session.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | Export Farz as an artefact | [`D1_1_export_artefact.html`](labs/D1_1_export_artefact.html) |
| 1.2 | Day 1 · Session 2 | Register two versions | [`D1_2_registry.html`](labs/D1_2_registry.html) |
| 1.3 | Day 1 · Session 3 | A versioned endpoint with a contract | [`D1_3_prediction_api.html`](labs/D1_3_prediction_api.html) |
| 1.4 | Day 1 · Session 4 | Health and readiness checks | [`D1_4_health_readiness.html`](labs/D1_4_health_readiness.html) |
| 2.1 | Day 2 · Session 1 | A multi-stage container file | [`D2_1_multi_stage_image.html`](labs/D2_1_multi_stage_image.html) |
| 2.2 | Day 2 · Session 2 | Scan, fix, configure | [`D2_2_scan_and_config.html`](labs/D2_2_scan_and_config.html) |
| 2.3 | Day 2 · Session 3 | Deploy to a local cluster | [`D2_3_local_cluster.html`](labs/D2_3_local_cluster.html) |
| 2.4 | Day 2 · Session 4 | The similar-claims endpoint | [`D2_4_similar_claims.html`](labs/D2_4_similar_claims.html) |
| 3.1 | Day 3 · Session 1 | Rate, errors and latency | [`D3_1_metrics.html`](labs/D3_1_metrics.html) |
| 3.2 | Day 3 · Session 2 | Logs, redaction and a trace | [`D3_2_logs_traces.html`](labs/D3_2_logs_traces.html) |
| 3.3 | Day 3 · Session 3 | Three rates against the objective | [`D3_3_load_test.html`](labs/D3_3_load_test.html) |
| 3.4 | Day 3 · Session 4 | Workers, replicas and cost | [`D3_4_sizing_cost.html`](labs/D3_4_sizing_cost.html) |
| 4.1 | Day 4 · Session 1 | A 10% canary | [`D4_1_canary.html`](labs/D4_1_canary.html) |
| 4.2 | Day 4 · Session 2 | Roll back a faulty version | [`D4_2_rollback.html`](labs/D4_2_rollback.html) |
| 4.3 | Day 4 · Session 3 | Drift in four weeks | [`D4_3_drift.html`](labs/D4_3_drift.html) |
| 4.4 | Day 4 · Session 4 | Two alerts and a runbook | [`D4_4_alerts_runbook.html`](labs/D4_4_alerts_runbook.html) |
<!-- /academy:labs -->

## Capstone

A model of the participant's choice taken to a monitored service, submitted as a public repository with container file, deployment manifests and dashboards as code, and a README reporting load-test results against a latency objective, a recorded canary release and rollback and a drift check, followed by an eight-minute defence and four minutes of questions

**Submission:** a public GitHub repository link: the service with its container file, deployment manifests, dashboard and alert rules as code, and a README that reports the load-test results against a stated latency objective, the recorded canary release and rollback, and a drift check, with the command that produced each number.

**Follow-up task:** run the capstone service for one week of replayed traffic and write a short incident note on what the dashboard and alerts showed.

**Assessment:** a supervised entry quiz and exit check without AI assistance (read a container file and a manifest, interpret a latency histogram, choose a release strategy; 20%), the capstone repository on the five-criterion rubric (60%), and a live defence in which the participant rolls back a version and explains a dashboard the assessor selects, while the assessor injects a fault to diagnose (20%). Passing: 70% overall, with at least 60% on the rubric and at least 60% on the supervised check.

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
<!-- /academy:sources -->

### National references

- Personal Data Protection Law and its implementing regulations: https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf and https://sdaia.gov.sa/en/SDAIA/about/Documents/ImplementingRegulationPersonalDataProtectionLaw.pdf
- Regulation on Personal Data Transfer outside the Kingdom: https://sdaia.gov.sa/Documents/RegulationonPersonalDataEN.pdf
- NDMO Data Classification Policy: https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf
- National Cybersecurity Authority (NCA) Cloud Cybersecurity Controls: https://nca.gov.sa/en/regulatory-documents/controls-list/ccc/
- SDAIA AI Ethics Principles: https://sdaia.gov.sa/en/SDAIA/about/Documents/ai-principles.pdf
