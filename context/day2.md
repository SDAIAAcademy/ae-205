---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
deck: "day2"
day: 2
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/slides/day2.html"
---

# Deploying AI Services: Containers, Serving and Monitoring

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
