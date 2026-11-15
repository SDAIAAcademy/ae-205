---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "1.1"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D1_1_export_artefact.html"
---

# Lab 1.1 · Export Farz as an artefact

Export the claims-triage model with its signature and pinned dependencies and reload it in a clean environment, reproducing ten reference predictions.

Day 1 · Session 1: From notebook to artefact

### Goal

Turn Adel's notebook pickle of Farz into an artefact that a fresh environment loads and that reproduces the notebook's ten reference predictions. On the way you find the part of the model that was never in the pickle.

## What you need

- A terminal with `git` and `uv`; a laptop processor. Nothing is downloaded but Python packages.
- The workspace, built once for the whole course by `labs/kit/setup.py` (about two minutes)
- AI policy: tutor. An assistant may explain an error; it does not write the export for you.

### Build the workspace and open lab 1.1 4 min

```bash
# file: terminal
git clone https://github.com/SDAIAAcademy/ae-205
uv run ae-205/labs/kit/setup.py        # writes rifd-labs/ beside the course
cd rifd-labs/1.1
uv run python -c "import rifd; print('ready')"
```

The workspace holds the claims (`data/`), Adel's notebook output (`notebook/`), the supplied models (`models/`) and one folder per lab. On Windows, keep the path short; if an install fails with a long-path error, set `UV_PROJECT_ENVIRONMENT` to a short folder first.

### Load the notebook pickle and read what it needs 5 min

A pickle is a program: loading it imports and calls whatever it names. List what this one names before you trust it, then read `notebook/train_triage.py` to the end.

```bash
# file: terminal
uv run python -m pickletools ../notebook/farz_notebook.pkl | grep -i sklearn | sort -u
uv run python tools/export_artefact.py
```

The export runs, and then says how many of the ten reference predictions it reproduces. Find in the notebook what turns probabilities into a label.

### Export with a signature, pins and the decision rule 8 min

Open `tools/export_artefact.py`. Two lines are marked `TODO lab 1.1`: record the rule of the notebook's cell 14 in `decision`, and write `requirements.txt` with the exact versions of this environment (`rifd.artefact` has a function for it). Run the export again until it reports 10 of 10.

```bash
# file: terminal
uv run python tools/export_artefact.py
cat artefacts/farz-1.0.0/signature.json artefacts/farz-1.0.0/requirements.txt
```

### Reload in a clean environment; match ten predictions 6 min

The test that matters: an environment that holds the pins and nothing else.

```bash
# file: terminal
uv run --isolated --no-project --with-requirements artefacts/farz-1.0.0/requirements.txt \
  python tools/check_reload.py artefacts/farz-1.0.0
```

It prints each reference claim with the expected and the predicted label. Then change one pin in a copy of `requirements.txt` and see what `check_reload.py` says.

### Check 2 min

```bash
# file: terminal
uv run ../lab.py check 1.1
```

### ✱ Stretch

Open the pickle with `pickletools` and list every import it would run on load. Then do the same for `model.skops` with `skops.io.get_untrusted_types`: what is the difference in what you have to trust?

## Check yourself

1. Without the rule of cell 14, how many of the ten reference predictions did the export reproduce, and which label did the others lose?
2. Why does the clean environment install only `requirements.txt` and not the whole project?
3. Which file of the artefact would a serving team read first, and why?
