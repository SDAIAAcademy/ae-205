---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "1.2"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D1_2_registry.html"
---

# Lab 1.2 · Register two versions

Register two supplied model versions with metrics and tags and load one by version.

Day 1 · Session 2: A registry for model versions

### Goal

Put two supplied versions of Farz in a registry with their metrics, the hash of the data they were trained on and who trained them; see the registry refuse to overwrite a version; and load a model by version and by alias.

## What you need

- The lab folder `rifd-labs/1.2`: the artefacts `models/farz-1.0.0` (Adel's logistic regression) and `models/farz-1.1.0` (gradient boosting)
- The course's registry, `rifd.registry`: a folder with an index file, so that you can read everything it does. MLflow and a git repository of tagged artefacts are the same ideas.
- AI policy: tutor.

### Read the two supplied artefacts and their metrics 4 min

```bash
# file: terminal
cd rifd-labs/1.2
uv run python -c "import json; [print(v, json.load(open(f'models/farz-{v}/metadata.json'))['metrics']) for v in ('1.0.0','1.1.0')]"
```

Which version is better, by how much, and on which measure? Write it down: the registry will carry it.

### Register 1.0.0 and 1.1.0 with tags and a data hash 8 min

```bash
# file: terminal
DATA=$(sha256sum ../data/claims.csv | cut -d' ' -f1)
uv run python -m rifd.registry register --name farz --version 1.0.0 --from models/farz-1.0.0 \
  --tag data_sha256=$DATA --tag trained_by="Adel Al-Shaikh"
```

Register 1.1.0 the same way. The registry copies the artefact into `registry/store/` and records its sha256: from now on the registry, not a folder on someone's laptop, is where the model lives. In PowerShell, take the hash from `(Get-FileHash ../data/claims.csv).Hash.ToLower()`.

### Try to overwrite 1.0.0 and read the refusal 3 min

```bash
# file: terminal
uv run python -m rifd.registry register --name farz --version 1.0.0 --from models/farz-1.1.0
```

A version is a promise that a name means one thing forever. A release log, a canary comparison and an incident note all point at "farz 1.0.0"; if it could change, none of them could be checked.

### Set the champion alias; load by version and by alias 7 min

```bash
# file: terminal
uv run python -m rifd.registry alias --name farz --alias champion --version 1.0.0
uv run python -m rifd.registry alias --name farz --alias challenger --version 1.1.0
uv run python -m rifd.registry load --name farz --ref 1.1.0
uv run python -m rifd.registry load --name farz --ref champion
uv run python -m rifd.registry show --name farz
```

A service that loads `champion` changes model when someone moves the alias; one that loads `1.0.0` never does. Decide which of the two the production deployment should name, and why.

### Check 3 min

```bash
# file: terminal
uv run ../lab.py check 1.2
```

### ✱ Stretch

Write the same two registrations as MLflow calls (a registered model, two versions, tags, the alias `champion`), or as annotated git tags on a repository that holds the artefact folders. What does each give you that the folder registry does not?

## Check yourself

1. A colleague retrains 1.0.0 with one more month of claims. What version does it get, and what tag shows the difference?
2. Why is the data hash a tag of the version and not a line in a wiki?
3. When should a deployment name an alias rather than a version?
