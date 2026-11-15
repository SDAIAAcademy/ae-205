---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
deck: "day4"
day: 4
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/slides/day4.html"
---

# Deploying AI Services: Containers, Serving and Monitoring

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
