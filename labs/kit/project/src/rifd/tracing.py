"""Traces with OpenTelemetry: one span per request and one per step inside it.

Spans go to a JSON Lines file (RIFD_TRACE_FILE) so that the labs need no collector. In production
the same code sends them to an OpenTelemetry Collector with an OTLP exporter.
"""

from __future__ import annotations

import json
import threading
from typing import Sequence

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

_lock = threading.Lock()
_exporter = None


class JsonLinesExporter(SpanExporter):
    def __init__(self, path: str):
        self.path = path

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        if not self.path:
            return SpanExportResult.SUCCESS
        with _lock, open(self.path, "a", encoding="utf-8") as f:
            for s in spans:
                f.write(json.dumps({
                    "trace_id": format(s.context.trace_id, "032x"),
                    "span_id": format(s.context.span_id, "016x"),
                    "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
                    "name": s.name,
                    "duration_ms": round((s.end_time - s.start_time) / 1e6, 3),
                    "attributes": dict(s.attributes or {}),
                    "status": s.status.status_code.name,
                }) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None


def configure(service: str, trace_file: str = "") -> None:
    """Set up tracing once per process; a later call only changes where spans are written."""
    global _exporter
    if _exporter is None:
        _exporter = JsonLinesExporter(trace_file)
        provider = TracerProvider(resource=Resource.create({"service.name": service}))
        provider.add_span_processor(SimpleSpanProcessor(_exporter))
        trace.set_tracer_provider(provider)
    _exporter.path = trace_file


def tracer() -> trace.Tracer:
    return trace.get_tracer("rifd")
