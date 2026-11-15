"""Shabih's routes: POST /v1/similar returns past claims like the one described (lab 2.4)."""

from __future__ import annotations

import time

from fastapi import FastAPI, Request

from rifd import errors, logs, tracing
from rifd.schemas import Similar, SimilarQuery
from rifd.similar import SimilarModel


def add_similar_routes(app: FastAPI) -> None:
    def load() -> None:
        try:
            start = time.perf_counter()
            model = SimilarModel(app.state.settings.similar_dir)
            app.state.load_ms = round((time.perf_counter() - start) * 1000, 2)
            t1 = time.perf_counter()
            model.search("warm-up claim text", k=1)
            app.state.model = model
            app.state.warm_ms = round((time.perf_counter() - t1) * 1000, 2)
            app.state.ready = True
            app.state.metrics.ready.set(1)
            logs.get().info("model_loaded", model=model.name, version=model.version, vectors=len(model.items))
        except Exception as e:
            app.state.load_error = str(e)
            logs.get().error("model_load_failed", error=str(e))

    app.state.load = load

    @app.post("/v1/similar", response_model=Similar)
    def similar(query: SimilarQuery, request: Request):
        m = app.state.model
        if m is None:
            raise errors.ServiceError("model-unavailable", 503, "No model loaded", app.state.load_error)
        with tracing.tracer().start_as_current_span("similar") as span:
            span.set_attribute("request_id", request.state.request_id)
            results = m.search(query.description, k=query.k, line=query.line)
        return {"results": results, "model": {"name": m.name, "version": m.version}}
