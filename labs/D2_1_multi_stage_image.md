---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "2.1"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D2_1_multi_stage_image.html"
---

# Lab 2.1 · A multi-stage container file

Write a multi-stage container file and compare its size and build time with a naive one.

Day 2 · Session 1: Images that are small and reproducible

### Goal

Package Farz and Shabih in one image that is small, built from the lock file, runs as a non-root user and rebuilds in seconds after a code change. Compare it with the naive container file the team wrote first.

## What you need

- The lab folder `rifd-labs/2.1`, with `Dockerfile.naive` and no `Dockerfile` yet
- A container runtime: Docker Desktop, Docker Engine or Podman (`podman build` takes the same file). Without one, write the file and let the check review it
- AI policy: off for the first attempt at the container file. Write it yourself, then compare with an assistant's version if you want to.

### Build the naive image; record size and time 5 min

```bash
# file: terminal
cd rifd-labs/2.1
time docker build -f Dockerfile.naive -t rifd/claims:naive .
docker image ls rifd/claims
```

Write the size and the build time down. Then change one line in `src/rifd/app.py` (a comment is enough), build again and watch which steps run.

### Write the multi-stage file without AI help 10 min

Write `Dockerfile` with two stages. The build stage starts from `python:3.12-slim`, copies `uv` from `ghcr.io/astral-sh/uv:0.13.5`, copies `pyproject.toml` and `uv.lock` before the code and runs `uv sync --frozen --no-dev`. The runtime stage starts again from the slim base, copies only the virtual environment, the code and the models, and switches to a user with id 10001. Write `.dockerignore` so that `.venv`, `tests`, `notebook` and `secrets` never reach the build.

### Build it; record size, time and a rebuild after a code change 6 min

```bash
# file: terminal
time docker build -t rifd/claims:1.0.0 .
docker image ls rifd/claims
docker run --rm -p 8000:8000 rifd/claims:1.0.0   # then: curl 127.0.0.1:8000/readyz
```

Change the same line again and rebuild: only the layers after `COPY src` should run.

### Check 4 min

```bash
# file: terminal
uv run ../lab.py check 2.1
```

### ✱ Stretch

Pin the base image by digest and rebuild twice: do the two images have the same id?

## Check yourself

1. Which line of your file decides whether a code change reinstalls the dependencies?
2. What does the runtime stage leave behind that the naive image carries?
3. Why does `secrets` belong in `.dockerignore` even though no line copies it by name?
