# Answer key: what each lab plants and what a finished lab shows

For trainers. Participants do not receive this file in their workspace.

| Lab | Planted in the supplied state | A finished lab shows |
|---|---|---|
| 1.1 | the notebook's decision rule (investigate at 0.30) is outside the pickle; the export writes no pins | 10 of 10 reference predictions in a clean environment with the pins only (8 of 10 before the rule) |
| 1.2 | an empty registry; an attempt to overwrite 1.0.0 | two versions with data hash and source tags, the overwrite refused, champion and challenger aliases |
| 1.3 | the route is `/triage`, unknown fields are ignored, no typed errors | 16 of 16 contract tests; national id dropped by `model_view()` |
| 1.4 | one `/health` that says OK with no model; the model loads on the first request | `/livez` 200 and `/readyz` 503 `model-unavailable` with no model; load and warm-up times |
| 2.1 | a naive container file: full base, `COPY .`, dev tools, root | two stages, pinned bases, `uv sync --frozen --no-dev`, user 10001, an ignore file |
| 2.2 | `h11==0.14.0` (GHSA-vqfr-h8mv-ghfj, CVE-2025-43859, critical, fixed in 0.16.0); the lookup key in `settings.py` and in an `ENV` line | h11 0.16.0 in the lock, pip-audit clean, the key read from configuration and in no file |
| 2.3 | `rifd/claims:latest` with `imagePullPolicy: Always`, no probes or limits, the key as a plain value | pinned image, startup, readiness and liveness probes, limits, a Secret; the placement table signed by Bassam Al-Jaber with Munira Al-Ajmi |
| 2.4 | `/v1/similar` not implemented; no Shabih manifest | the endpoint returns claim id, line, incident and score only; Shabih loads about ten times slower than Farz and uses about 40 MiB more |
| 3.1 | no metrics; two dashboard panels missing | three metric families, a bucket at 0.15 s, p50/p95/p99 from a recording |
| 3.2 | the whole claim (with the member block) logged; no request id; no span on the policy lookup | no personal numbers in logs; a request id on every line; the slowest request's time in `policy_lookup` (about 7% of claims take it) |
| 3.3 | the load test sends one motor claim | an open load of week 1 at three rates, one holding the objective and one breaking it |
| 3.4 | `replicas_needed` and `cost_per_1000` missing | at least two configurations compared, a choice and its cost per 1,000; a GPU replica far dearer |
| 4.1 | an empty release log | about 10% of claims to 1.1.0, compared on errors, p95, label shares and agreement; a decision by the criteria |
| 4.2 | farz 1.2.0's `metadata.json` sets the investigate threshold to 0.05 instead of 0.30 | the label-share criterion fires after 200 canary requests; share 0 within 5 minutes; every later answer from 1.1.0 |
| 4.3 | the PSI function missing | channel shifted from week 3 (app share 45% to 70%); motor amounts ×1.6 shifted by line but not pooled; tenure +1 month significant and negligible (the decoy) |
| 4.4 | an empty rule group, an empty runbook | an error rule firing in minutes 12 to 18, a latency rule from minute 22 on, quiet on the minute-6 blip; Munira named as accountable |

The numbers measured in the course's own run are in the trainer notes of each lab page.
