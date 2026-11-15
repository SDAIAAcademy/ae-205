---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
deck: "day3"
day: 3
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/slides/day3.html"
---

# Deploying AI Services: Containers, Serving and Monitoring

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
