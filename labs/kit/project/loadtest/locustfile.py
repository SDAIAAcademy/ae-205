"""Load test for Farz (lab 3.3).

    uv run locust -f loadtest/locustfile.py --headless --host http://127.0.0.1:8000 \
        --users 100 --spawn-rate 50 --run-time 40s --csv runs/load_100 --only-summary

Each simulated caller sends one claim a second (constant_throughput(1)), so the number of users is
the request rate: 100 users is 100 requests a second. The claims are real rows of the replay files,
so the mix of lines, channels and slow lookups is the mix the service will see.
"""

from __future__ import annotations

import itertools
import os
import sys
from pathlib import Path

from locust import HttpUser, constant_throughput, task

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import claims  # noqa: E402

DATA = os.environ.get("RIFD_LOAD_FILE", str(Path(__file__).resolve().parents[2] / "data" / "replay" / "week1.csv"))
BODIES = [claims.request_body(r) for r in claims.read(DATA)]
NEXT = itertools.cycle(range(len(BODIES)))


class ClaimsSystem(HttpUser):
    wait_time = constant_throughput(1)

    @task
    def triage(self) -> None:
        body = BODIES[next(NEXT)]
        with self.client.post("/v1/triage", json=body, name="/v1/triage", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"status {r.status_code}")
