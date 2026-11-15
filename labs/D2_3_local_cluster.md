---
course: "Deploying AI Services: Containers, Serving and Monitoring"
code: "AE-205"
version: "2027.1.0"
lab: "2.3"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-205/labs/D2_3_local_cluster.html"
---

# Lab 2.3 · Deploy to a local cluster

Deploy the supplied service image to a single-node cluster with probes and resource limits, and decide where each service may run.

Day 2 · Session 3: Running on a local cluster

### Goal

Run Farz on a single-node cluster with a pinned image, probes that match its two checks, and limits on memory and CPU, with the key supplied by a Secret. Then decide, for Farz, Shabih and the dashboards, where each may run under Rifd's data rules.

## What you need

- The lab folder `rifd-labs/2.3`: `k8s/farz.yaml` as someone first wrote it, `k8s/config.yaml`, `k8s/kind.yaml` and `PLACEMENT.md`
- A single-node cluster: kind, k3d or minikube, with `kubectl`, and a container runtime. The folder holds the finished `Dockerfile`, so this lab does not need your image of lab 2.1
- AI policy: tutor.

### Create the cluster and load the image 5 min

```bash
# file: terminal
cd rifd-labs/2.3
docker build -t rifd/claims:1.0.0 .       # seconds if lab 2.1 built it: the layers are cached
kind create cluster --name rifd --config k8s/kind.yaml
kind load docker-image rifd/claims:1.0.0 --name rifd
kubectl create secret generic rifd-lookup --from-file=key=secrets/lookup.key
```

### Apply the supplied manifest; read why it fails 5 min

```bash
# file: terminal
kubectl apply -f k8s/config.yaml -f k8s/farz.yaml
kubectl get pods -l app=farz
kubectl describe pod -l app=farz | tail -20
```

Read the events at the bottom: the pods ask a registry for an image it does not have.

### Add probes, limits and a pinned image 7 min

In `k8s/farz.yaml`: pin the image to `rifd/claims:1.0.0` with `imagePullPolicy: IfNotPresent`; add a `startupProbe` and a `readinessProbe` on `/readyz` and a `livenessProbe` on `/livez`; set requests and limits for memory and CPU; and take the key from the Secret with `valueFrom.secretKeyRef`.

```bash
# file: terminal
kubectl apply -f k8s/farz.yaml
kubectl rollout status deployment/farz
kubectl port-forward service/farz 8000:80   # then: curl 127.0.0.1:8000/readyz
```

### Fill the placement table for three services 5 min

In `PLACEMENT.md`, say for Farz, Shabih and the dashboards what each holds, its classification, where it may run and why, and who at Rifd signs the table.

### Check 3 min

```bash
# file: terminal
uv run ../lab.py check 2.3
```

When you finish the day: `kind delete cluster --name rifd`.

### ✱ Stretch

Change the image tag and watch a rolling update replace the pods one at a time.

## Check yourself

1. Which event told you why the first pods did not start?
2. Why does the startup probe give Farz up to a minute when the readiness probe gives up after ten seconds?
3. The dashboards carry no claim content. What has to be true, and who has to agree, before they run outside the Kingdom?
