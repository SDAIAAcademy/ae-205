"""Liveness, readiness and warm-up (lab 1.4)."""

from __future__ import annotations

from conftest import MOTOR


def test_live_and_ready_when_the_model_loads(client):
    assert client.get("/livez").status_code == 200
    r = client.get("/readyz")
    assert r.status_code == 200, r.text
    assert r.json()["model"] == {"name": "farz", "version": "1.0.0"}


def test_the_model_is_warm_before_the_first_request(client):
    body = client.get("/readyz").json()
    assert body["warm_ms"] is not None and body["warm_ms"] >= 0


def test_alive_but_not_ready_when_the_model_file_is_missing(broken_client):
    assert broken_client.get("/livez").status_code == 200
    r = broken_client.get("/readyz")
    assert r.status_code == 503
    assert r.json()["type"] == "urn:rifd:problem:model-unavailable"
    assert "no artefact" in r.json()["detail"]


def test_predictions_are_refused_with_a_reason_when_not_ready(broken_client):
    r = broken_client.post("/v1/triage", json=MOTOR)
    assert r.status_code == 503
    assert r.json()["type"] == "urn:rifd:problem:model-unavailable"


def test_an_altered_model_file_is_not_ready(tmp_path):
    import shutil

    from conftest import MODEL_DIR, make_client
    copy = tmp_path / "farz"
    shutil.copytree(MODEL_DIR, copy)
    with open(copy / "model.skops", "ab") as f:
        f.write(b"tampered")
    with make_client(model_dir=str(copy)) as c:
        r = c.get("/readyz")
        assert r.status_code == 503 and "sha256" in r.json()["detail"]
        assert c.get("/livez").status_code == 200
