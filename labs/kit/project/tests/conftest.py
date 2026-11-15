from __future__ import annotations

import copy
import os

import pytest
from fastapi.testclient import TestClient

from rifd.app import create_app
from rifd.settings import Settings

MODEL_DIR = os.environ.get("RIFD_MODEL_DIR", "models/farz-1.0.0")
SIMILAR_DIR = os.environ.get("RIFD_SIMILAR_DIR", "models/shabih-1.0.0")

MOTOR = {
    "claim_id": "CLM-050123", "line": "motor", "region": "riyadh", "channel": "app",
    "amount_sar": 4200.0, "policy_tenure_months": 30, "prior_claims_12m": 0, "days_to_report": 1,
    "vehicle_age_years": 5, "police_report": True,
    "description": "Rear bumper damaged at a junction",
    "member": {"name": "Arwa Al-Malki", "national_id": "1234567890", "mobile": "0512345678"},
}
HEALTH_OUT = {
    "claim_id": "CLM-050124", "line": "health", "region": "eastern", "channel": "branch",
    "amount_sar": 900.0, "policy_tenure_months": 14, "prior_claims_12m": 1, "days_to_report": 3,
    "in_network": False, "description": "Outpatient visit",
}


def claim(base=MOTOR, **change):
    c = copy.deepcopy(base)
    for k, v in change.items():
        if v is ...:
            c.pop(k, None)
        else:
            c[k] = v
    return c


def make_client(**settings) -> TestClient:
    s = Settings(**{"model_dir": MODEL_DIR, "lookup_key": "test-key", "lookup_ms": 1.0, **settings})
    return TestClient(create_app(s), raise_server_exceptions=False)


@pytest.fixture
def client():
    with make_client() as c:
        yield c


@pytest.fixture
def broken_client(tmp_path):
    (tmp_path / "metadata.json").write_text("{}", encoding="utf-8")
    with make_client(model_dir=str(tmp_path / "missing")) as c:
        yield c
