"""Typed errors as problem details (RFC 9457): every error a caller can act on has its own type."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM = "application/problem+json"


class ServiceError(Exception):
    """An error the service raises on purpose, with a type a caller can switch on."""

    def __init__(self, kind: str, status: int, title: str, detail: str):
        self.kind, self.status, self.title, self.detail = kind, status, title, detail


def problem(kind: str, status: int, title: str, detail: str, request: Request, **extra) -> JSONResponse:
    body = {"type": f"urn:rifd:problem:{kind}", "title": title, "status": status, "detail": detail,
            "instance": request.url.path, **extra}
    rid = getattr(request.state, "request_id", None)
    if rid:
        body["request_id"] = rid
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


def install(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def on_validation(request: Request, exc: RequestValidationError):
        errors = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "message": e["msg"]} for e in exc.errors()]
        return problem("validation-error", 422, "The claim does not match the contract",
                       f"{len(errors)} field(s) failed validation", request, errors=errors)

    @app.exception_handler(ServiceError)
    async def on_service(request: Request, exc: ServiceError):
        return problem(exc.kind, exc.status, exc.title, exc.detail, request)

    @app.exception_handler(Exception)
    async def on_crash(request: Request, exc: Exception):
        return problem("prediction-failed", 500, "The prediction failed", "an unexpected error; the request id is in the logs", request)
