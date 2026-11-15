"""Rate, errors and duration, and what the model predicts: the metrics of the service."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

# Buckets in seconds, dense around the 150 ms objective so the 95th percentile is estimated well there.
BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.5)


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter("rifd_requests", "Requests served, by route and status code",
                                ["route", "status"], registry=self.registry)
        self.duration = Histogram("rifd_request_duration_seconds", "Time to answer a request, measured in the service",
                                  ["route"], buckets=BUCKETS, registry=self.registry)
        self.predictions = Counter("rifd_predictions", "Predictions made, by model version and label",
                                   ["model", "version", "label"], registry=self.registry)
        self.ready = Gauge("rifd_model_ready", "1 when the model is loaded and warm", registry=self.registry)

    def observe(self, route: str, status: int, seconds: float) -> None:
        self.requests.labels(route=route, status=str(status)).inc()
        self.duration.labels(route=route).observe(seconds)

    def predicted(self, model: str, version: str, label: str) -> None:
        self.predictions.labels(model=model, version=version, label=label).inc()

    def render(self) -> tuple[bytes, str]:
        return generate_latest(self.registry), CONTENT_TYPE_LATEST
