---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "2.2"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D2_2_scan_and_config.html"
---

# Lab 2.2 · Scan, fix, configure

Scan a supplied image, fix one critical finding and move secrets out of the image into configuration.

Day 2 · Session 2: Scanning and configuration

### Goal

Scan the image the claims team was given last quarter, fix its critical finding by moving to a fixed version, and take the lookup key out of the code and the image so that the runtime supplies it.

## What you need

- The lab folder `rifd-labs/2.2`: `supplied/Dockerfile`, a lock file with an old `h11`, and a key written in `src/rifd/settings.py`
- A scanner: `pip-audit` (in the project's dev tools) scans the Python dependencies; Trivy or Grype also scan the image's system packages when a container runtime is available
- AI policy: tutor.

### Scan the supplied image and read the report 6 min

```bash
# file: terminal
cd rifd-labs/2.2
uv export --no-dev --no-hashes --frozen -o runs/requirements-audit.txt
uv run pip-audit -r runs/requirements-audit.txt --no-deps --disable-pip --aliases --desc
```

The supplied image installs exactly what `uv.lock` says, so this is the scan of its Python packages. With a container runtime, build the image and scan all of it, system packages included, with Trivy (`grype rifd/claims:supplied` does the same):

```bash
# file: terminal
docker build -f supplied/Dockerfile -t rifd/claims:supplied .
trivy image --severity HIGH,CRITICAL rifd/claims:supplied
```

For each finding, note the package, the advisory, its severity and the version that fixes it. Open the advisory and read which requests trigger it.

### Fix the critical finding and scan again 7 min

In `pyproject.toml`, replace the pin on `h11` with a lower bound at the fixed version, then lock and scan again.

```bash
# file: terminal
uv lock --upgrade-package h11
uv export --no-dev --no-hashes --frozen -o runs/requirements-audit.txt
uv run pip-audit -r runs/requirements-audit.txt --no-deps --disable-pip
```

With a runtime, build the image again and repeat the `trivy image` scan: the h11 finding is gone, and what remains belongs to the base image.

### Find the key in the image history 4 min

```bash
# file: terminal
grep -rn "rifd-lookup-key" src supplied
# with a runtime: docker history --no-trunc rifd/claims:supplied | grep KEY
```

Anyone who can pull the image can read it. Removing the line from a new image does not remove it from the old one, so the key is rotated as well.

### Read the key from configuration instead 5 min

In `src/rifd/settings.py`, make `lookup_key` come from `_secret("RIFD_LOOKUP_KEY")`, which reads the environment or the file `secrets/lookup.key`. Take the key out of `supplied/Dockerfile` and put it in `secrets/lookup.key`, which git and the build both ignore.

### Check 3 min

```bash
# file: terminal
uv run ../lab.py check 2.2
```

### ✱ Stretch

Scan the multi-stage image of lab 2.1 and compare the counts by severity.

## Check yourself

1. Two findings: one critical with a fixed version, one medium with none. Which do you fix today, and what do you record about the other?
2. Why is a lower bound (`h11>=0.16`) in `pyproject.toml` and an exact version in `uv.lock` the right pair?
3. The key was in an image that was pushed. What must happen besides removing it?
