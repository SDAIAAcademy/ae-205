"""The start state of every lab, as changes to the finished project in kit/project.

Each state lists the supplied models it needs and a few edits: `patch` replaces a passage of a
file (the passage must occur exactly once), `write` puts a whole file, `remove` deletes one. The
solutions put the finished passages back, so a state and its solution can never drift apart.
"""

from __future__ import annotations

TODO = "# TODO lab {lab}: "

APP = "src/rifd/app.py"

STATES: dict[str, dict] = {}

# ---------------------------------------------------------------- Day 1
STATES["1.1"] = {
    "models": [],
    "patch": [
        ("tools/export_artefact.py",
         '    decision = {"investigate_threshold": INVESTIGATE_AT}\n',
         '    decision = {}  # TODO lab 1.1: the notebook turns probabilities into a label with a rule of its own (cell 14). Record it here.\n'),
        ("tools/export_artefact.py",
         "    artefact.write_pins(out)  # without pins, a fresh environment may load it with other versions\n",
         "    # TODO lab 1.1: write requirements.txt with the exact versions that load the model (see rifd.artefact)\n"),
        ("tools/export_artefact.py",
         "from train_triage import INVESTIGATE_AT  # noqa: E402  the decision rule lives in the notebook today\n",
         "import train_triage  # noqa: E402,F401  Adel's notebook, exported as a script\n"),
    ],
}

STATES["1.2"] = {"models": ["farz-1.0.0", "farz-1.1.0"], "patch": []}

STATES["1.3"] = {
    "models": ["farz-1.0.0"],
    "patch": [
        (APP, '    @app.post("/v1/triage", response_model=Triage)\n    async def triage(claim: Claim, request: Request):\n',
              '    @app.post("/triage")  # TODO lab 1.3: version the path and declare the response model\n    async def triage(claim: Claim, request: Request):\n'),
        (APP, '        return {"claim_id": claim.claim_id, "label": out["label"], "probabilities": out["probabilities"],\n                "model": {"name": m.name, "version": m.version}}\n',
              '        return {"claim_id": claim.claim_id, "label": out["label"], "probabilities": out["probabilities"]}\n'),
        ("src/rifd/schemas.py",
         '    claim_id: str = Field(pattern=r"^CLM-\\d{6}$")\n    line: Line\n    region: Region\n    channel: Channel\n    amount_sar: float = Field(gt=0, le=5_000_000)\n    policy_tenure_months: int = Field(ge=0, le=600)\n    prior_claims_12m: int = Field(ge=0, le=50)\n    days_to_report: int = Field(ge=0, le=365)\n    vehicle_age_years: int | None = Field(default=None, ge=0, le=60)\n',
         '    claim_id: str = Field(pattern=r"^CLM-\\d{6}$")\n    line: Line\n    # TODO lab 1.3: region, channel, amount_sar, policy_tenure_months, prior_claims_12m and\n    # days_to_report, with the rules of CONTRACT.md\n    region: str = ""\n    channel: str = ""\n    amount_sar: float = 0.0\n    policy_tenure_months: int = 0\n    prior_claims_12m: int = 0\n    days_to_report: int = 0\n    vehicle_age_years: int | None = Field(default=None, ge=0, le=60)\n'),
        ("src/rifd/schemas.py",
         '    @model_validator(mode="after")\n    def by_line(self) -> "Claim":\n        if self.line == "motor" and (self.vehicle_age_years is None or self.police_report is None):\n            raise ValueError("a motor claim needs vehicle_age_years and police_report")\n        if self.line == "health" and self.in_network is None:\n            raise ValueError("a health claim needs in_network")\n        return self\n',
         '    # TODO lab 1.3: a motor claim needs vehicle_age_years and police_report; a health claim needs in_network\n'),
        ("src/rifd/schemas.py", 'class Claim(BaseModel):\n    model_config = ConfigDict(extra="forbid")\n',
         'class Claim(BaseModel):\n    model_config = ConfigDict(extra="ignore")  # TODO lab 1.3: what does the contract say about unknown fields?\n'),
        ("src/rifd/errors.py",
         '    @app.exception_handler(RequestValidationError)\n    async def on_validation(request: Request, exc: RequestValidationError):\n        errors = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "message": e["msg"]} for e in exc.errors()]\n        return problem("validation-error", 422, "The claim does not match the contract",\n                       f"{len(errors)} field(s) failed validation", request, errors=errors)\n\n    @app.exception_handler(ServiceError)\n    async def on_service(request: Request, exc: ServiceError):\n        return problem(exc.kind, exc.status, exc.title, exc.detail, request)\n',
         '    # TODO lab 1.3: two handlers that answer with problem(...):\n    #   RequestValidationError -> validation-error, 422, with an "errors" list of {"field", "message"}\n    #   ServiceError           -> its own kind, status, title and detail\n'),
    ],
}

STATES["1.4"] = {
    "models": ["farz-1.0.0"],
    "patch": [
        (APP, '        if s.service == "shabih":\n            app.state.load()\n        else:\n            load_farz(app)\n        yield\n',
              '        if s.service == "shabih":\n            app.state.load()\n        # TODO lab 1.4: load and warm the model here, before the first request arrives\n        yield\n'),
        (APP, '    @app.get("/livez")\n    def livez():\n        """Liveness: is the process able to answer at all? Never depends on the model."""\n        return {"status": "alive"}\n\n    @app.get("/readyz")\n    def readyz(request: Request):\n        """Readiness: should traffic be sent here now? Only when the model is loaded and warm."""\n        if not app.state.ready:\n            return errors.problem("model-unavailable", 503, "Not ready", app.state.load_error, request)\n        m = app.state.model\n        return {"status": "ready", "model": {"name": m.name, "version": m.version}, "load_ms": getattr(app.state, "load_ms", None), "warm_ms": getattr(app.state, "warm_ms", None)}\n',
              '    @app.get("/health")\n    def health():\n        """TODO lab 1.4: one check that always says OK. Replace it with /livez and /readyz."""\n        return {"status": "ok"}\n'),
        (APP, '        m = app.state.model\n        if m is None:\n            raise errors.ServiceError("model-unavailable", 503, "No model loaded", app.state.load_error)\n        view = claim.model_view()\n',
              '        if app.state.model is None:  # loaded on the first request: that caller waits for it\n            load_farz(app)\n        m = app.state.model\n        if m is None:\n            raise errors.ServiceError("model-unavailable", 503, "No model loaded", app.state.load_error)\n        view = claim.model_view()\n'),
    ],
}

# ---------------------------------------------------------------- Day 2
STATES["2.1"] = {"models": ["farz-1.0.0", "shabih-1.0.0"], "patch": [], "remove": ["Dockerfile", ".dockerignore"]}

SUPPLIED_DOCKERFILE = """# The image the claims team was given last quarter. Lab 2.2 scans it.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY models/ ./models/
RUN uv sync --frozen --no-dev
ENV RIFD_LOOKUP_KEY=rifd-lookup-key-for-the-labs-only RIFD_MODEL_DIR=/app/models/farz-1.0.0
CMD ["uv", "run", "--no-sync", "uvicorn", "rifd.app:app", "--host", "0.0.0.0", "--port", "8000"]
"""

STATES["2.2"] = {
    "models": ["farz-1.0.0"],
    "patch": [
        ("pyproject.toml", '    "h11>=0.16",\n', '    "h11==0.14.0",\n'),
        ("src/rifd/settings.py", '    lookup_key: str = field(default_factory=lambda: _secret("RIFD_LOOKUP_KEY"))\n',
                                 '    lookup_key: str = "rifd-lookup-key-for-the-labs-only"  # TODO lab 2.2: never in the code\n'),
    ],
    "copy": {"uv.lock": "states/2.2/uv.lock"},
    "write": {"supplied/Dockerfile": SUPPLIED_DOCKERFILE},
    "remove": ["secrets/lookup.key"],
}

NAIVE_MANIFEST = """# The first manifest someone wrote for Farz. Lab 2.3 makes it run.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: farz
  labels: {app: farz}
spec:
  replicas: 2
  selector:
    matchLabels: {app: farz}
  template:
    metadata:
      labels: {app: farz}
    spec:
      containers:
        - name: farz
          image: rifd/claims:latest
          imagePullPolicy: Always
          ports: [{containerPort: 8000, name: http}]
          env:
            - {name: RIFD_SERVICE, value: farz}
            - {name: RIFD_LOOKUP_KEY, value: rifd-lookup-key-for-the-labs-only}
---
apiVersion: v1
kind: Service
metadata:
  name: farz
spec:
  selector: {app: farz}
  ports: [{port: 80, targetPort: http, name: http}]
"""

PLACEMENT = """# Where may each service run?

Rifd applies the four levels of the national Data Classification Policy (Top Secret, Secret,
Restricted, Public) to its own data. Its hosting options: the in-Kingdom cluster in Riyadh, and a
monitoring service (dashboards and log search) hosted outside the Kingdom.

| Service or data flow | What it holds | Classification | Where it may run | Why |
|---|---|---|---|---|
| Farz, the triage service | | | | |
| Shabih, the similar-claims service and its index | | | | |
| Metrics and dashboards (counts, latency, labels; no claim content) | | | | |

Who signs this off at Rifd:
"""

STATES["2.3"] = {
    "models": ["farz-1.0.0", "shabih-1.0.0"],
    "write": {"k8s/farz.yaml": NAIVE_MANIFEST, "PLACEMENT.md": PLACEMENT},
    "patch": [],
}

STATES["2.4"] = {
    "models": ["farz-1.0.0", "shabih-1.0.0"],
    "patch": [
        ("src/rifd/routes_similar.py",
         '        with tracing.tracer().start_as_current_span("similar") as span:\n            span.set_attribute("request_id", request.state.request_id)\n            results = m.search(query.description, k=query.k, line=query.line)\n        return {"results": results, "model": {"name": m.name, "version": m.version}}\n',
         '        # TODO lab 2.4: search the index (m.search) inside a span, and answer with the Similar schema\n        raise errors.ServiceError("not-implemented", 501, "Not implemented yet", "lab 2.4")\n'),
    ],
    "remove": ["k8s/shabih.yaml"],
}

# ---------------------------------------------------------------- Day 3
STATES["3.1"] = {
    "models": ["farz-1.0.0"],
    "patch": [
        ("src/rifd/metrics.py",
         '        self.requests = Counter("rifd_requests", "Requests served, by route and status code",\n                                ["route", "status"], registry=self.registry)\n        self.duration = Histogram("rifd_request_duration_seconds", "Time to answer a request, measured in the service",\n                                  ["route"], buckets=BUCKETS, registry=self.registry)\n        self.predictions = Counter("rifd_predictions", "Predictions made, by model version and label",\n                                   ["model", "version", "label"], registry=self.registry)\n',
         '        # TODO lab 3.1: a counter of requests by route and status, a latency histogram by route\n        # with BUCKETS, and a counter of predictions by model, version and label\n'),
        ("src/rifd/metrics.py",
         '    def observe(self, route: str, status: int, seconds: float) -> None:\n        self.requests.labels(route=route, status=str(status)).inc()\n        self.duration.labels(route=route).observe(seconds)\n\n    def predicted(self, model: str, version: str, label: str) -> None:\n        self.predictions.labels(model=model, version=version, label=label).inc()\n',
         '    def observe(self, route: str, status: int, seconds: float) -> None:\n        pass  # TODO lab 3.1\n\n    def predicted(self, model: str, version: str, label: str) -> None:\n        pass  # TODO lab 3.1\n'),
        ("monitoring/dashboard.json",
         ',\n    {"id": 4, "type": "timeseries", "title": "Predictions per second, by label and version", "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},\n     "datasource": {"type": "prometheus", "uid": "prometheus"},\n     "targets": [\n       {"refId": "A", "legendFormat": "{{version}} {{label}}", "expr": "sum by (version, label) (rate(rifd_predictions_total[1m]))"}\n     ]}\n',
         '\n'),
        ("monitoring/dashboard.json",
         ',\n       {"refId": "C", "legendFormat": "p99", "expr": "histogram_quantile(0.99, sum by (le) (rate(rifd_request_duration_seconds_bucket{route=\\"/v1/triage\\"}[1m])))"}\n',
         '\n'),
    ],
}

STATES["3.2"] = {
    "models": ["farz-1.0.0"],
    "patch": [
        ("src/rifd/logs.py", '            redact,\n', ''),
        ("src/rifd/logs.py", '    structlog.contextvars.clear_contextvars()\n    structlog.contextvars.bind_contextvars(request_id=request_id)\n',
                             '    pass  # TODO lab 3.2: bind the request id to every line logged while this request is served\n'),
        (APP, '        logs.get().info("triage", claim_id=claim.claim_id, line=claim.line, label=out["label"], version=m.version)\n',
              '        logs.get().info("triage", claim=claim.model_dump(), label=out["label"], version=m.version)\n'),
        (APP, '            if policy_lookup.needs_lookup(view):\n                with tr.start_as_current_span("policy_lookup"):\n                    try:\n                        view["benefit_limit"] = await policy_lookup.benefit_limit(view, s.lookup_key, s.lookup_ms)\n                    except policy_lookup.LookupError_ as e:\n                        raise errors.ServiceError("dependency-failed", 502, "The policy system refused the call", str(e))\n',
              '            if policy_lookup.needs_lookup(view):  # TODO lab 3.2: give this step a span of its own\n                try:\n                    view["benefit_limit"] = await policy_lookup.benefit_limit(view, s.lookup_key, s.lookup_ms)\n                except policy_lookup.LookupError_ as e:\n                    raise errors.ServiceError("dependency-failed", 502, "The policy system refused the call", str(e))\n'),
    ],
}

ONE_CLAIM_NOTE = "claim_id,day,line,incident,region,channel,amount_sar,policy_tenure_months,prior_claims_12m,days_to_report,vehicle_age_years,police_report,in_network,description,member_name,national_id,mobile\nCLM-099001,364,motor,parking,riyadh,app,2100.0,40,0,1,4,1,,Side door scratched in a parking lot,Test Caller,1000000001,0500000001\n"

STATES["3.3"] = {
    "models": ["farz-1.0.0"],
    "write": {"loadtest/one_claim.csv": ONE_CLAIM_NOTE},
    "patch": [
        ("tools/loadtest.py", '    ap.add_argument("--file", default="../data/replay/week1.csv")\n',
                              '    ap.add_argument("--file", default="loadtest/one_claim.csv")  # TODO lab 3.3: is one claim a realistic load?\n'),
    ],
}

STATES["3.4"] = {
    "models": ["farz-1.0.0"],
    "patch": [
        ("tools/sizing.py", '    """Enough replicas that each stays below (1 - headroom) of the capacity it showed, plus spares."""\n    return math.ceil(target_rps / (capacity_rps * (1 - headroom))) + spare\n',
                            '    """Enough replicas that each stays below (1 - headroom) of the capacity it showed, plus spares."""\n    raise NotImplementedError("TODO lab 3.4")\n'),
        ("tools/sizing.py", '    """The cost of 1,000 predictions when the service carries rate_rps for an hour."""\n    return round(hourly / (rate_rps * 3600 / 1000), 6)\n',
                            '    """The cost of 1,000 predictions when the service carries rate_rps for an hour."""\n    raise NotImplementedError("TODO lab 3.4")\n'),
    ],
}

# ---------------------------------------------------------------- Day 4
RELEASE_LOG = """# Release log: Farz

## Release of farz {version}

| | |
|---|---|
| Change | |
| Strategy and traffic share | |
| Criteria applied | ../data/rollback_criteria.md |
| Canary requests judged | |
| Error ratio: current / canary | |
| p95 ms: current / canary | |
| Label shares: current / canary | |
| Agreement with delayed labels: current / canary | |
| Decision (promote or roll back) | |
| Decided by | |
| Evidence files | |
"""

STATES["4.1"] = {"models": ["farz-1.0.0", "farz-1.1.0"], "write": {"RELEASE_LOG.md": RELEASE_LOG.replace("{version}", "1.1.0")}, "patch": []}
STATES["4.2"] = {"models": ["farz-1.1.0", "farz-1.2.0"], "write": {"RELEASE_LOG.md": RELEASE_LOG.replace("{version}", "1.2.0") + "| Seconds from the criterion firing to traffic share 0 | |\n| Cause | |\n"}, "patch": []}

DRIFT_REPORT = """# Drift report: four weeks of replayed claims

| | |
|---|---|
| Reference | the 40,000 training claims |
| Statistic and thresholds | |
| Shifted features (and in which segment) | |
| Features that moved but do not matter | |
| Prediction shares by week | |
| What the delayed labels show | |
| What the labels cannot show yet | |
| Recommendation | |
"""

STATES["4.3"] = {
    "models": ["farz-1.0.0"],
    "write": {"DRIFT_REPORT.md": DRIFT_REPORT},
    "patch": [
        ("tools/drift.py", '    e = np.clip(expected, EPS, None)\n    a = np.clip(actual, EPS, None)\n    return float(np.sum((a - e) * np.log(a / e)))\n',
                           '    """PSI = sum over bins of (actual share - expected share) * ln(actual share / expected share)."""\n    raise NotImplementedError("TODO lab 4.3: clip both shares at EPS so that an empty bin does not divide by zero")\n'),
    ],
}

RUNBOOK = """# Runbook: Farz, the claims-triage service

On call: the platform engineer of the week. Accountable for a rollback decision:

## errors
Alert FarzErrorRatioHigh.
- What the caller sees:
- First three checks:
- Roll back when:
- How to roll back:

## latency
Alert FarzLatencyP95High.
- What the caller sees:
- First three checks:
- What to change:

## Who to tell
"""

ALERTS_START = """# Two alert rules for Farz, in Prometheus' rule format (lab 4.4: write them without AI help first).
# Test them:  uv run python tools/promlite.py rules --series ../data/recordings/spike.jsonl --rules monitoring/alerts.yml
groups:
  - name: farz
    rules: []
"""

STATES["4.4"] = {
    "models": ["farz-1.0.0"],
    "write": {"monitoring/alerts.yml": ALERTS_START, "RUNBOOK.md": RUNBOOK, "CAPSTONE.md": "# My capstone model\n\nModel:\nWhy:\nLatency objective I will defend:\n"},
    "patch": [],
}
