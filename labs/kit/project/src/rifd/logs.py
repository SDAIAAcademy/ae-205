"""Structured logs: one JSON line per event, a request id on every line, personal fields redacted."""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog

PERSONAL_KEYS = {"member", "name", "member_name", "national_id", "mobile"}
NATIONAL_ID = re.compile(r"(?<!\d)[12]\d{9}(?!\d)")
MOBILE = re.compile(r"(?<!\d)05\d{8}(?!\d)")


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("[redacted]" if k in PERSONAL_KEYS else redact_value(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(v) for v in value]
    if isinstance(value, str):
        return MOBILE.sub("[mobile]", NATIONAL_ID.sub("[national_id]", value))
    return value


def redact(_logger: Any, _method: str, event: dict[str, Any]) -> dict[str, Any]:
    """A structlog processor: the last line of defence before a log line leaves the process."""
    return redact_value(event)


def configure(log_file: str = "") -> None:
    stream = open(log_file, "a", encoding="utf-8") if log_file else sys.stdout
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            redact,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=stream),
        cache_logger_on_first_use=False,
    )


def get() -> Any:
    return structlog.get_logger("rifd")


def bind_request(request_id: str) -> None:
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
