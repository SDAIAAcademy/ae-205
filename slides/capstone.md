---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
deck: "capstone"
day: 5
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/slides/capstone.html"
---

# Deploying AI Services: Containers, Serving and Monitoring

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
