"""No personal field reaches a log line or a span (lab 3.2)."""

from __future__ import annotations

import json
import re

from conftest import HEALTH_OUT, MOTOR, make_client

NATIONAL_ID = re.compile(r"(?<!\d)[12]\d{9}(?!\d)")
MOBILE = re.compile(r"(?<!\d)05\d{8}(?!\d)")


def test_logs_and_traces_carry_no_personal_field(tmp_path):
    log, spans = tmp_path / "service.log", tmp_path / "spans.jsonl"
    with make_client(log_file=str(log), trace_file=str(spans)) as c:
        c.post("/v1/triage", json=MOTOR, headers={"X-Request-ID": "rid-1"})
        c.post("/v1/triage", json={**MOTOR, "amount_sar": -1})
        c.post("/v1/triage", json=HEALTH_OUT)
    text = log.read_text(encoding="utf-8") + (spans.read_text(encoding="utf-8") if spans.exists() else "")
    assert "Arwa" not in text
    assert not NATIONAL_ID.search(text), NATIONAL_ID.search(text)
    assert not MOBILE.search(text)


def test_every_log_line_is_json_with_a_request_id(tmp_path):
    log = tmp_path / "service.log"
    with make_client(log_file=str(log)) as c:
        c.post("/v1/triage", json=MOTOR, headers={"X-Request-ID": "rid-2"})
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
    mine = [x for x in lines if x.get("request_id") == "rid-2"]
    assert {x["event"] for x in mine} >= {"triage", "request"}


def test_the_slow_step_has_its_own_span(tmp_path):
    spans = tmp_path / "spans.jsonl"
    with make_client(trace_file=str(spans), lookup_ms=40.0) as c:
        c.post("/v1/triage", json=HEALTH_OUT, headers={"X-Request-ID": "rid-3"})
    rows = [json.loads(x) for x in spans.read_text(encoding="utf-8").splitlines()]
    names = {r["name"] for r in rows}
    assert {"triage", "policy_lookup", "predict"} <= names
    lookup = next(r for r in rows if r["name"] == "policy_lookup")
    assert lookup["duration_ms"] >= 40
