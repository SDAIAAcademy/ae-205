"""The contract of POST /v1/triage (CONTRACT.md). Lab 1.3 makes all of these pass."""

from __future__ import annotations

import pytest

from conftest import HEALTH_OUT, MOTOR, claim

PROBLEM = "application/problem+json"


def problem_of(r, status, kind):
    assert r.status_code == status, r.text
    assert r.headers["content-type"].startswith(PROBLEM), r.headers["content-type"]
    body = r.json()
    assert body["type"] == f"urn:rifd:problem:{kind}", body
    assert body["status"] == status
    return body


def test_a_valid_motor_claim_is_triaged(client):
    r = client.post("/v1/triage", json=MOTOR)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["claim_id"] == "CLM-050123"
    assert body["label"] in ("fast_track", "standard", "investigate")
    assert set(body["probabilities"]) == {"fast_track", "standard", "investigate"}
    assert abs(sum(body["probabilities"].values()) - 1) < 1e-6


def test_the_response_names_the_model_version(client):
    body = client.post("/v1/triage", json=MOTOR).json()
    assert body["model"] == {"name": "farz", "version": "1.0.0"}


def test_a_health_claim_outside_the_network_is_triaged(client):
    assert client.post("/v1/triage", json=HEALTH_OUT).status_code == 200


def test_the_path_is_versioned(client):
    assert client.post("/triage", json=MOTOR).status_code == 404


def test_a_missing_field_is_a_validation_error_naming_the_field(client):
    body = problem_of(client.post("/v1/triage", json=claim(amount_sar=...)), 422, "validation-error")
    assert any(e["field"] == "amount_sar" for e in body["errors"]), body


def test_a_wrong_type_is_a_validation_error(client):
    problem_of(client.post("/v1/triage", json=claim(prior_claims_12m="two")), 422, "validation-error")


@pytest.mark.parametrize("amount", [0, -50, 9_000_000])
def test_an_amount_out_of_range_is_refused(client, amount):
    problem_of(client.post("/v1/triage", json=claim(amount_sar=amount)), 422, "validation-error")


def test_an_unknown_line_is_refused(client):
    problem_of(client.post("/v1/triage", json=claim(line="marine")), 422, "validation-error")


def test_an_unknown_field_is_refused(client):
    problem_of(client.post("/v1/triage", json=claim(discount_code="X1")), 422, "validation-error")


def test_a_motor_claim_needs_the_vehicle_age(client):
    problem_of(client.post("/v1/triage", json=claim(vehicle_age_years=...)), 422, "validation-error")


def test_a_malformed_national_id_is_refused(client):
    bad = claim(member={"name": "A", "national_id": "12345", "mobile": "0512345678"})
    problem_of(client.post("/v1/triage", json=bad), 422, "validation-error")


def test_a_body_that_is_not_json_is_a_validation_error(client):
    r = client.post("/v1/triage", content=b"line=motor", headers={"content-type": "application/json"})
    problem_of(r, 422, "validation-error")


def test_every_response_carries_a_request_id(client):
    r = client.post("/v1/triage", json=MOTOR, headers={"X-Request-ID": "lab-1-3"})
    assert r.headers["X-Request-ID"] == "lab-1-3"
    assert client.post("/v1/triage", json=claim(line="marine")).json()["request_id"]


def test_a_model_that_fails_to_load_gives_model_unavailable(broken_client):
    problem_of(broken_client.post("/v1/triage", json=MOTOR), 503, "model-unavailable")
