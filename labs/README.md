# AE-205 labs: setup

Every lab runs in a terminal on a laptop processor. No model is downloaded and no hosted model is
called: the two models (Farz, the claims-triage classifier, and Shabih, the similar-claims model)
are trained on synthetic claims by the setup script in about two minutes.

## What you need

- `git`, a shell (Git Bash on Windows) and [uv](https://docs.astral.sh/uv/) 0.13 or later
- Day 2 only: a container runtime (Docker Desktop, Docker Engine or Podman) and a single-node
  cluster (kind, k3d or minikube) with `kubectl`. Without them, labs 2.1 and 2.3 still run: their
  checks review the container file and the manifest, and say that nothing was built or deployed.

Before Day 2, on the room's network, fetch what the builds and the cluster start from, so that the
first build of lab 2.1 and the first cluster of lab 2.3 fit in their minutes:

```bash
docker pull python:3.12 && docker pull python:3.12-slim && docker pull ghcr.io/astral-sh/uv:0.13.5
kind create cluster --name warm && kind delete cluster --name warm   # fetches the node image
```

Lab 2.2 scans an image with Trivy or Grype when one of them is installed; without it, the lab scans
the image's Python packages from its lock file with pip-audit, which the project already holds.

## Build the workspace

```bash
uv run labs/kit/setup.py                    # every lab, in ../rifd-labs beside the course folder
uv run labs/kit/setup.py --to ~/rifd-labs   # somewhere else
uv run labs/kit/setup.py --only 3.2 --force # start one lab again from its supplied state
```

Each lab has its own folder (`rifd-labs/1.1` to `rifd-labs/4.4`), so a lab you did not finish never
blocks the next one. Inside a lab folder:

```bash
uv run ../lab.py check 2.4   # PASS, or the list of what is left to do
```

## Windows

- Long paths: run `git config --global core.longpaths true`, and if uv reports a path that is too
  long, put the environments in a short folder: `export UV_PROJECT_ENVIRONMENT=C:/uvt/rifd`.
- Use `127.0.0.1`, not `localhost`, in `curl` and in load tests: on some Windows machines
  `localhost` tries IPv6 first and adds about 200 ms to every new connection.
- Load tests measure the laptop as well as the service. Close other heavy programs first.

## Notes for trainers

- Lab 2.2's supplied lock pins `h11 0.14.0` on purpose (advisory GHSA-vqfr-h8mv-ghfj); the scan
  needs the network to fetch advisories. Run it the week before and update the slide.
- `labs/solutions/` holds one script per lab. Each starts its lab again from the supplied state,
  does the steps, and ends with the lab's own check:

```bash
RIFD_LABS=~/rifd-labs uv run --no-project python labs/solutions/run_all.py        # all sixteen
RIFD_LABS=~/rifd-labs uv run --no-project python labs/solutions/run_all.py 3.3 4.2
RIFD_RATES="30 80 160" ...                                                        # lab 3.3's rates
```

- `labs/solutions/answer_key.md` lists what each lab plants and what a finished lab shows.
- `rifd/__init__.py` sets `OMP_NUM_THREADS=1`: without it, gradient boosting starts a thread per core
  for each one-row prediction and becomes very slow on a busy machine.
