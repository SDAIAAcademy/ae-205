# Farz and Shabih: one image, two services (RIFD_SERVICE picks one).
# Build:  docker build -t rifd/claims:1.0.0 .      (podman build works the same)

# ---- stage 1: build the environment from the lock file ----
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first: this layer is rebuilt only when the lock file changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Then the code, which changes often.
COPY src ./src
RUN uv sync --frozen --no-dev

# ---- stage 2: the runtime, without the build tools ----
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 rifd
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src /app/src
COPY models/ /app/models/
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 RIFD_SERVICE=farz RIFD_MODEL_DIR=/app/models/farz-1.0.0 RIFD_SIMILAR_DIR=/app/models/shabih-1.0.0
USER 10001
EXPOSE 8000
CMD ["uvicorn", "rifd.app:app", "--host", "0.0.0.0", "--port", "8000"]
