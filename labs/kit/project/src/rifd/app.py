"""The claims service. RIFD_SERVICE=farz serves triage; RIFD_SERVICE=shabih serves similar claims.

    uv run uvicorn rifd.app:app --port 8000
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from rifd import artefact, errors, logs, policy_lookup, tracing
from rifd import settings as settings_mod
from rifd.metrics import Metrics
from rifd.routes_similar import add_similar_routes
from rifd.schemas import Claim, ModelInfo, Triage


def load_farz(app: FastAPI) -> None:
    s = app.state.settings
    app.state.model = None
    try:
        t0 = time.perf_counter()
        model = artefact.load(s.model_dir)
        app.state.load_ms = round((time.perf_counter() - t0) * 1000, 2)
        start = time.perf_counter()
        warm = model.predict([model.meta["reference"][0]["input"]])  # the first call pays for lazy set-up
        app.state.warm_ms = round((time.perf_counter() - start) * 1000, 2)
        if warm[0]["label"] != model.meta["reference"][0]["label"]:
            raise artefact.ArtefactError("the warm-up prediction disagrees with the artefact's reference")
        app.state.model = model
        app.state.ready = True
        app.state.metrics.ready.set(1)
        logs.get().info("model_loaded", model=model.name, version=model.version, warm_ms=app.state.warm_ms)
    except Exception as e:  # the process stays alive and says why it is not ready
        app.state.load_error = str(e)
        logs.get().error("model_load_failed", error=str(e), model_dir=s.model_dir)


def create_app(settings: settings_mod.Settings | None = None) -> FastAPI:
    s = settings or settings_mod.load()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logs.configure(s.log_file)
        tracing.configure(f"rifd-{s.service}", s.trace_file)
        if s.service == "shabih":
            app.state.load()
        else:
            load_farz(app)
        yield

    app = FastAPI(title=f"Rifd {s.service}", version="1", lifespan=lifespan)
    app.state.settings = s
    app.state.metrics = Metrics()
    app.state.ready = False
    app.state.load_error = "the model has not been loaded yet"
    app.state.model = None
    app.state.load = lambda: None
    errors.install(app)

    @app.middleware("http")
    async def observe(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.request_id = rid
        logs.bind_request(rid)
        start = time.perf_counter()
        response = await call_next(request)
        seconds = time.perf_counter() - start
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        if path not in ("/metrics", "/livez", "/readyz"):
            app.state.metrics.observe(path, response.status_code, seconds)
            logs.get().info("request", method=request.method, route=path, status=response.status_code, ms=round(seconds * 1000, 2))
        response.headers["X-Request-ID"] = rid
        return response

    @app.get("/livez")
    def livez():
        """Liveness: is the process able to answer at all? Never depends on the model."""
        return {"status": "alive"}

    @app.get("/readyz")
    def readyz(request: Request):
        """Readiness: should traffic be sent here now? Only when the model is loaded and warm."""
        if not app.state.ready:
            return errors.problem("model-unavailable", 503, "Not ready", app.state.load_error, request)
        m = app.state.model
        return {"status": "ready", "model": {"name": m.name, "version": m.version}, "load_ms": getattr(app.state, "load_ms", None), "warm_ms": getattr(app.state, "warm_ms", None)}

    @app.get("/metrics")
    def metrics():
        body, ctype = app.state.metrics.render()
        return Response(body, media_type=ctype)

    if s.service == "shabih":
        add_similar_routes(app)
        return app

    @app.get("/v1/model", response_model=ModelInfo)
    def model_info():
        m = app.state.model
        if m is None:
            raise errors.ServiceError("model-unavailable", 503, "No model loaded", app.state.load_error)
        return {"name": m.name, "version": m.version}

    @app.post("/v1/triage", response_model=Triage)
    async def triage(claim: Claim, request: Request):
        m = app.state.model
        if m is None:
            raise errors.ServiceError("model-unavailable", 503, "No model loaded", app.state.load_error)
        view = claim.model_view()
        tr = tracing.tracer()
        with tr.start_as_current_span("triage") as span:
            span.set_attribute("request_id", request.state.request_id)
            span.set_attribute("claim.line", claim.line)
            span.set_attribute("model.version", m.version)
            if policy_lookup.needs_lookup(view):
                with tr.start_as_current_span("policy_lookup"):
                    try:
                        view["benefit_limit"] = await policy_lookup.benefit_limit(view, s.lookup_key, s.lookup_ms)
                    except policy_lookup.LookupError_ as e:
                        raise errors.ServiceError("dependency-failed", 502, "The policy system refused the call", str(e))
            with tr.start_as_current_span("predict"):
                try:
                    out = m.predict([view])[0]
                except Exception as e:
                    logs.get().error("prediction_failed", claim_id=claim.claim_id, error=type(e).__name__)
                    raise errors.ServiceError("prediction-failed", 500, "The prediction failed", "the request id is in the logs")
        app.state.metrics.predicted(m.name, m.version, out["label"])
        logs.get().info("triage", claim_id=claim.claim_id, line=claim.line, label=out["label"], version=m.version)
        return {"claim_id": claim.claim_id, "label": out["label"], "probabilities": out["probabilities"],
                "model": {"name": m.name, "version": m.version}}

    return app


app = create_app()
