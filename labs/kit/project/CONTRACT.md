# The Farz API contract, version 1

Agreed between Rifd's claims system team and the platform team before any code was written.

## POST /v1/triage

Request: one claim as JSON. Unknown fields are refused.

| Field | Type | Rule |
|---|---|---|
| claim_id | string | `CLM-` and six digits |
| line | string | motor, health or property |
| region | string | riyadh, makkah, eastern, madinah, qassim, asir |
| channel | string | app, branch or broker |
| amount_sar | number | more than 0, at most 5,000,000 |
| policy_tenure_months | integer | 0 to 600 |
| prior_claims_12m | integer | 0 to 50 |
| days_to_report | integer | 0 to 365 |
| vehicle_age_years | integer | 0 to 60; required for motor |
| police_report | boolean | required for motor |
| in_network | boolean | required for health |
| description | string | up to 2,000 characters; never sent to Farz |
| member | object | name, national_id (10 digits, starting 1 or 2), mobile (05 and 8 digits); never sent to the model, never logged |

Response 200:

```json
{"claim_id": "CLM-050123", "label": "standard",
 "probabilities": {"fast_track": 0.21, "standard": 0.64, "investigate": 0.15},
 "model": {"name": "farz", "version": "1.0.0"}}
```

## Errors

Every error is `application/problem+json` (RFC 9457) with `type`, `title`, `status`, `detail`,
`instance` and `request_id`. A caller switches on `type`, never on the text.

| type | status | When | What the caller does |
|---|---|---|---|
| `urn:rifd:problem:validation-error` | 422 | The claim breaks a rule above; `errors` lists each field | Fix the claim; do not retry as it is |
| `urn:rifd:problem:model-unavailable` | 503 | No model is loaded | Retry later, or route the claim to manual triage |
| `urn:rifd:problem:dependency-failed` | 502 | The policy system refused the lookup | Retry later |
| `urn:rifd:problem:prediction-failed` | 500 | Anything else | Report the request id |

Every response carries the header `X-Request-ID` (the caller's, or a new one).

## Health

| Path | Meaning | 200 when |
|---|---|---|
| GET /livez | The process can answer | Always, while the process runs |
| GET /readyz | Send traffic here | The model is loaded, matches its sha256 and has answered its warm-up |

## Versions

The path carries the contract's major version (`/v1/`). The response carries the model's version.
A change that breaks a caller is `/v2/`, served beside `/v1/` until every caller has moved.
