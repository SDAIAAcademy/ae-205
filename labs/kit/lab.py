"""Check the evidence of a lab.

    uv run ../lab.py check 2.3       (inside the lab's folder, rifd-labs/2.3)

It reads the files the lab asks for, runs the tests and tools that prove them, and prints PASS or
what is missing. It cannot judge a placement decision, a runbook or a release note: your trainer
does that. Standard library only; it runs the project's own tools with uv.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path.cwd()
WS = Path(__file__).resolve().parent
DATA = WS / "data"
problems: list[str] = []
passed: list[str] = []


def need(ok: object, good: str, bad: str = "") -> bool:
    (passed if ok else problems).append(good if ok else (bad or "missing: " + good))
    return bool(ok)


def sh(cmd: list[str], timeout: int = 600) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]} is not installed"
    except subprocess.TimeoutExpired:
        return 124, "timed out"


def py(code: str, *args: str) -> tuple[int, str]:
    return sh(["uv", "run", "--quiet", "python", "-c", code, *args])


def text(rel: str) -> str:
    f = HERE / rel
    return f.read_text(encoding="utf-8", errors="replace") if f.is_file() else ""


def jsonfile(rel: str):
    t = text(rel)
    try:
        return json.loads(t) if t else None
    except ValueError:
        problems.append(f"{rel} is not valid JSON")
        return None


def yaml_docs(rel: str) -> list[dict]:
    code, out = py("import json,sys,yaml; print(json.dumps([d for d in yaml.safe_load_all(open(sys.argv[1], encoding='utf-8')) if d]))", rel)
    if code != 0:
        problems.append(f"{rel} is not valid YAML: {out.splitlines()[-1] if out else ''}")
        return []
    return json.loads(out.splitlines()[-1])


def pytest(target: str) -> bool:
    code, out = sh(["uv", "run", "--quiet", "pytest", target])
    last = [x for x in out.splitlines() if "passed" in x or "failed" in x or "error" in x]
    return need(code == 0, f"{target}: {last[-1] if last else 'passed'}", f"{target} does not pass: {last[-1] if last else out[-300:]}")


def filled(rel: str, rows: list[str]) -> None:
    t = text(rel)
    if not need(t, rel):
        return
    for r in rows:
        line = next((x for x in t.splitlines() if x.startswith("| " + r)), "")
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        need(len(cells) > 1 and all(cells[1:]), f"{rel}: '{r}' is filled", f"{rel}: fill the row '{r}'")


# ---------------------------------------------------------------- Day 1

def check_1_1() -> None:
    art = HERE / "artefacts" / "farz-1.0.0"
    for f in ("model.skops", "signature.json", "metadata.json", "requirements.txt"):
        need((art / f).is_file(), f"artefacts/farz-1.0.0/{f}")
    meta = jsonfile("artefacts/farz-1.0.0/metadata.json") or {}
    need(meta.get("decision", {}).get("investigate_threshold") == 0.30, "the decision rule is in the artefact (investigate at 0.30)",
         "metadata.json has no decision rule: the notebook's cell 14 is not in the artefact")
    pins = text("artefacts/farz-1.0.0/requirements.txt").split()
    need(pins and all("==" in p for p in pins) and any(p.startswith("scikit-learn==") for p in pins), "requirements.txt pins every library with ==")
    if (art / "requirements.txt").is_file():
        code, out = sh(["uv", "run", "--isolated", "--no-project", "--quiet", "--with-requirements", "artefacts/farz-1.0.0/requirements.txt",
                        "python", "tools/check_reload.py", "artefacts/farz-1.0.0"])
        need(code == 0 and "10 of 10" in out, "a clean environment with only the pins reproduces 10 of 10 reference predictions",
             "the clean reload does not reproduce the ten reference predictions: " + (out.splitlines()[0] if out else ""))


def check_1_2() -> None:
    reg = jsonfile("registry/registry.json") or {}
    farz = reg.get("models", {}).get("farz", {})
    versions = farz.get("versions", {})
    need({"1.0.0", "1.1.0"} <= set(versions), "farz 1.0.0 and 1.1.0 are registered")
    data_hash = ""
    code, out = py("import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())", str(DATA / "claims.csv"))
    if code == 0:
        data_hash = out.splitlines()[-1]
    for v, rec in versions.items():
        tags = rec.get("tags", {})
        need(tags.get("data_sha256") == data_hash, f"{v} is tagged with the training data's sha256", f"{v}: tag data_sha256 is missing or is not the hash of data/claims.csv")
        need(len(tags) >= 2, f"{v} has a second tag (who trained it, from which commit)", f"{v}: add a tag naming who trained it or the commit")
        need(rec.get("metrics", {}).get("macro_f1"), f"{v} carries its metrics")
    aliases = farz.get("aliases", {})
    need(aliases.get("champion") == "1.0.0", "champion points at 1.0.0", "set the alias champion to 1.0.0")
    need(aliases.get("challenger") == "1.1.0", "challenger points at 1.1.0", "set the alias challenger to 1.1.0")
    code, out = sh(["uv", "run", "--quiet", "python", "-m", "rifd.registry", "load", "--name", "farz", "--ref", "champion"])
    need(code == 0 and "10 of 10" in out, "farz@champion loads and reproduces its reference predictions", "farz@champion does not load: " + out[-200:])
    code, out = sh(["uv", "run", "--quiet", "python", "-m", "rifd.registry", "register", "--name", "farz", "--version", "1.0.0", "--from", "models/farz-1.1.0"])
    need(code != 0 and "already registered" in out, "the registry refuses to overwrite 1.0.0")


def check_1_3() -> None:
    pytest("tests/test_contract.py")


def check_1_4() -> None:
    pytest("tests/test_health.py")
    app = text("src/rifd/app.py")
    need('"/health"' not in app, "the old /health check is gone", "src/rifd/app.py still serves /health, which says OK with no model")


# ---------------------------------------------------------------- Day 2

def dockerfile_findings(t: str) -> list[str]:
    lines = [x.strip() for x in t.splitlines() if x.strip() and not x.strip().startswith("#")]
    froms = [x for x in lines if x.upper().startswith("FROM ")]
    bad = []
    if len(froms) < 2:
        bad.append("one FROM line: a multi-stage file has a build stage and a runtime stage")
    if any(re.search(r":latest\b", f) or (":" not in f.split()[1] and "@" not in f.split()[1]) for f in froms if len(f.split()) > 1):
        bad.append("a base image without a pinned tag")
    if not any("--frozen" in x or "--locked" in x for x in lines):
        bad.append("the environment is not installed from the lock file (uv sync --frozen)")
    if not any("--no-dev" in x for x in lines):
        bad.append("development tools (pytest, locust) go into the image: use --no-dev")
    if not any(x.upper().startswith("USER ") for x in lines):
        bad.append("the service runs as root: add a USER line")
    if any(re.match(r"COPY\s+\.\s", x) for x in lines[lines.index(froms[-1]):] if froms):
        bad.append("the runtime stage copies the whole folder (COPY . ...)")
    if any(re.search(r"(KEY|SECRET|TOKEN|PASSWORD)\s*=", x, re.I) for x in lines if x.upper().startswith(("ENV", "ARG"))):
        bad.append("a secret in an ENV or ARG line")
    return bad


def docker() -> str | None:
    for tool in ("docker", "podman"):
        if shutil.which(tool):
            code, _ = sh([tool, "info"], timeout=30)
            if code == 0:
                return tool
    return None


def check_2_1() -> None:
    t = text("Dockerfile")
    if need(t, "Dockerfile"):
        for b in dockerfile_findings(t):
            problems.append("Dockerfile: " + b)
        if not dockerfile_findings(t):
            passed.append("Dockerfile: two stages, pinned bases, installed from the lock without dev tools, non-root")
    ign = text(".dockerignore")
    need(all(x in ign for x in (".venv", "tests", "notebook")), ".dockerignore leaves out .venv, tests and notebook")
    tool = docker()
    if not tool:
        passed.append("no container runtime answers here: the image size and build time were not measured by this check")
        return
    code, out = sh([tool, "image", "inspect", "rifd/claims:1.0.0", "--format", "{{.Size}}"], timeout=60)
    if need(code == 0, "the image rifd/claims:1.0.0 exists", "build it: docker build -t rifd/claims:1.0.0 ."):
        mb = int(out.splitlines()[-1]) / 1e6
        need(mb < 500, f"the image is {mb:.0f} MB, under 500 MB", f"the image is {mb:.0f} MB: the objective is under 500 MB")


def check_2_2() -> None:
    lock = text("uv.lock")
    m = re.search(r'name = "h11"\nversion = "([^"]+)"', lock)
    need(m and tuple(int(x) for x in m.group(1).split(".")[:2]) >= (0, 16), f"uv.lock has h11 {m.group(1) if m else '?'}, a fixed version",
         f"uv.lock still has h11 {m.group(1) if m else '?'}: the critical finding is not fixed")
    pyproject = text("pyproject.toml")
    need("h11==0.14.0" not in pyproject, "pyproject.toml no longer pins the vulnerable h11")
    code, out = sh(["uv", "export", "--no-dev", "--no-hashes", "--frozen", "--quiet", "-o", "runs/requirements-audit.txt"])
    if code == 0:
        code, out = sh(["uv", "run", "--quiet", "pip-audit", "-r", "runs/requirements-audit.txt", "--no-deps", "--disable-pip"], timeout=300)
        need(code == 0, "pip-audit finds no known vulnerability in the service's dependencies",
             "pip-audit still reports: " + " ".join(x for x in out.splitlines() if "GHSA" in x or "PYSEC" in x or "CVE" in x)[:300])
    key = "rifd-lookup-key-for-the-labs-only"
    leaks = [str(p.relative_to(HERE)) for p in HERE.rglob("*") if p.is_file() and p.suffix in ("", ".py", ".toml", ".yaml", ".yml", ".md", ".txt", ".json")
             and ".venv" not in p.parts and "secrets" not in p.parts and "runs" not in p.parts and key in p.read_text(encoding="utf-8", errors="ignore")]
    need(not leaks, "the key is in no file of the project (only in configuration)", "the key is still written in: " + ", ".join(leaks))
    code, out = py("from rifd.settings import Settings; import os; os.environ['RIFD_LOOKUP_KEY']='from-env'; print(Settings().lookup_key)")
    need(code == 0 and out.splitlines()[-1] == "from-env", "the service reads the key from its configuration", "src/rifd/settings.py does not read RIFD_LOOKUP_KEY from the environment")


def check_2_3() -> None:
    docs = yaml_docs("k8s/farz.yaml")
    dep = next((d for d in docs if d.get("kind") == "Deployment"), None)
    if not need(dep, "k8s/farz.yaml has a Deployment"):
        return
    c = dep["spec"]["template"]["spec"]["containers"][0]
    image = c.get("image", "")
    need(":" in image and not image.endswith(":latest"), f"the image is pinned ({image})", "the image tag is latest: pin a version")
    need(c.get("imagePullPolicy") in ("IfNotPresent", "Never"), "imagePullPolicy lets the cluster use the image you loaded")
    for probe, path in (("readinessProbe", "/readyz"), ("livenessProbe", "/livez")):
        need(c.get(probe, {}).get("httpGet", {}).get("path") == path, f"{probe} asks {path}")
    need(c.get("startupProbe"), "a startupProbe gives the model time to load", "no startupProbe: a slow start gets the pod restarted")
    res = c.get("resources", {})
    need(res.get("requests", {}).get("memory") and res.get("limits", {}).get("memory") and res.get("limits", {}).get("cpu"), "requests and limits for memory and CPU")
    env = c.get("env", [])
    plain = [e for e in env if e.get("name") == "RIFD_LOOKUP_KEY" and "value" in e]
    need(not plain, "the key comes from a Secret, not a plain value", "RIFD_LOOKUP_KEY is a plain value in the manifest: use valueFrom.secretKeyRef")
    filled("PLACEMENT.md", ["Farz", "Shabih", "Metrics"])
    t = text("PLACEMENT.md")
    need(re.search(r"Who signs this off at Rifd:\s*\S", t), "PLACEMENT.md names who signs it off")
    if shutil.which("kubectl"):
        code, out = sh(["kubectl", "get", "deployment", "farz", "-o", "jsonpath={.status.readyReplicas}"], timeout=30)
        if code == 0:
            need(out.strip() not in ("", "0"), f"the cluster reports {out.strip() or 0} ready replicas of farz")
        else:
            passed.append("no cluster answers here: the deployment was checked as a file only")


def check_2_4() -> None:
    pytest("tests/test_similar.py")
    for svc in ("farz", "shabih"):
        m = jsonfile(f"runs/measure_{svc}.json")
        need(m and m.get("ready_s") and m.get("rss_ready_mib"), f"runs/measure_{svc}.json holds time to ready and memory",
             f"save the measurement: uv run python tools/measure.py --service {svc} > runs/measure_{svc}.json")


# ---------------------------------------------------------------- Day 3

def check_3_1() -> None:
    code, out = py("from fastapi.testclient import TestClient; from rifd.app import create_app\n"
                   "import json\nwith TestClient(create_app()) as c:\n"
                   " c.post('/v1/triage', json={'claim_id':'CLM-050001','line':'property','region':'asir','channel':'app','amount_sar':900.0,'policy_tenure_months':12,'prior_claims_12m':0,'days_to_report':2})\n"
                   " print(json.dumps(c.get('/metrics').text))")
    body = json.loads(out.splitlines()[-1]) if code == 0 else ""
    for name in ("rifd_requests_total", "rifd_request_duration_seconds_bucket", "rifd_predictions_total"):
        need(name in body, f"/metrics exposes {name}")
    need('le="0.15"' in body, "the histogram has a bucket at the 150 ms objective")
    dash = jsonfile("monitoring/dashboard.json") or {}
    exprs = [t["expr"] for p in dash.get("panels", []) for t in p.get("targets", [])]
    need(any("histogram_quantile(0.99" in e for e in exprs), "the dashboard graphs the 99th percentile")
    need(any("rifd_predictions_total" in e for e in exprs), "the dashboard graphs the prediction distribution")
    s = HERE / "runs" / "metrics.jsonl"
    if need(s.is_file(), "runs/metrics.jsonl: a recording of /metrics while traffic ran"):
        code, out = sh(["uv", "run", "--quiet", "python", "tools/promlite.py", "query", "--series", "runs/metrics.jsonl", "--last",
                        "--expr", 'histogram_quantile(0.95, sum by (le) (rate(rifd_request_duration_seconds_bucket{route="/v1/triage"}[30s])))'])
        need(code == 0 and "{}" in out and "nan" not in out.lower(), "the recording gives a 95th percentile: " + (out.splitlines()[-1] if out else ""))


PERSONAL = re.compile(r"(?<!\d)[12]\d{9}(?!\d)|(?<!\d)05\d{8}(?!\d)")


def check_3_2() -> None:
    pytest("tests/test_redaction.py")
    log = text("runs/service.log")
    if need(log, "runs/service.log from your traffic run"):
        need(not PERSONAL.search(log), "no national id or mobile number in runs/service.log", "runs/service.log still holds personal numbers: " + PERSONAL.search(log).group(0)[:3] + "...")
        rows = [json.loads(x) for x in log.splitlines() if x.startswith("{")]
        need(rows and all("request_id" in r for r in rows if r.get("event") in ("request", "triage")), "every request line carries a request id")
    spans = [json.loads(x) for x in text("runs/spans.jsonl").splitlines() if x.strip()]
    if need(spans, "runs/spans.jsonl from your traffic run"):
        need(any(s["name"] == "policy_lookup" for s in spans), "the policy lookup has its own span")
    note = text("runs/slowest.md")
    need("policy_lookup" in note, "runs/slowest.md names the slow span of the slowest request")


def check_3_3() -> None:
    rep = jsonfile("runs/load.json") or {}
    steps = rep.get("steps", [])
    need(len(steps) >= 3, "runs/load.json has three rates")
    need("replay" in rep.get("file", ""), "the load test sends the replay claims, not one claim", "the load test sent loadtest/one_claim.csv: one claim over and over is not the traffic Farz will see")
    need(any(not s["meets_objective"] for s in steps) and any(s["meets_objective"] for s in steps),
         "one rate holds the objective and one breaks it", "choose rates so that one holds the objective and one breaks it")
    need(re.search(r"\d", text("runs/load_note.md")), "runs/load_note.md says where the objective breaks and why")


def check_3_4() -> None:
    code, out = py("import sys; sys.path.insert(0,'tools'); import sizing\n"
                   "assert sizing.replicas_needed(200, 150, 0.3) == 3, sizing.replicas_needed(200, 150, 0.3)\n"
                   "assert abs(sizing.cost_per_1000(0.6075, 200) - 0.000844) < 1e-6\nprint('ok')")
    need(code == 0 and out.endswith("ok"), "replicas_needed and cost_per_1000 give the reference answers", "tools/sizing.py: " + (out.splitlines()[-1] if out else ""))
    s = jsonfile("runs/sizing.json") or {}
    need(len(s.get("options", [])) >= 2 and s.get("chosen"), "runs/sizing.json compares at least two configurations and chooses one")
    need(re.search(r"\d", text("runs/sizing_note.md")), "runs/sizing_note.md gives the choice and its cost per 1,000 predictions")


# ---------------------------------------------------------------- Day 4

def rows_of(rel: str) -> list[dict]:
    return [json.loads(x) for x in text(rel).splitlines() if x.strip()]


def check_4_1() -> None:
    rows = rows_of("runs/canary.jsonl")
    if need(len(rows) >= 1000, "runs/canary.jsonl holds at least 1,000 answers"):
        share = sum(r["version"] == "1.1.0" for r in rows) / len(rows)
        need(0.07 <= share <= 0.13, f"the canary served {share:.1%} of the traffic", f"the canary served {share:.1%}: send 10%")
    filled("RELEASE_LOG.md", ["Change", "Strategy", "Canary requests", "Error ratio", "p95", "Label shares", "Agreement", "Decision", "Decided by"])
    need(re.search(r"\|\s*Decision[^|]*\|\s*(promote|roll back)", text("RELEASE_LOG.md"), re.I), "the decision is promote or roll back")


def check_4_2() -> None:
    events = rows_of("runs/router_events.jsonl")
    start = next((e for e in events if e["event"] == "start"), None)
    back = next((e for e in events if e["event"] == "weight" and e["after"] == 0), None)
    need(start and start.get("weight", 0) > 0, "the router started with a canary share")
    if need(back, "the canary's share was set to 0 (the rollback)"):
        need(back.get("reason"), "the rollback event gives a reason")
        need(back["after_s"] - start["after_s"] <= 300, f"rolled back {back['after_s'] - start['after_s']:.0f} s after the release started, within 5 minutes")
    after = rows_of("runs/after_rollback.jsonl")
    need(after and all(r["version"] == "1.1.0" for r in after), "after the rollback every answer comes from 1.1.0", "replay a few claims after the rollback into runs/after_rollback.jsonl")
    log = text("RELEASE_LOG.md")
    filled("RELEASE_LOG.md", ["Canary requests", "Label shares", "Decision", "Decided by", "Seconds from", "Cause"])
    need(re.search(r"0\.05", log) and re.search(r"threshold", log, re.I), "the cause names the investigate threshold of 0.05")
    need(re.search(r"Munira", log), "the decision names Munira Al-Ajmi, who is accountable")


def check_4_3() -> None:
    code, out = py("import sys, numpy as np; sys.path.insert(0,'tools'); import drift\n"
                   "e=np.array([.5,.3,.2]); a=np.array([.3,.3,.4])\n"
                   "v=drift.psi_from_shares(e,a); assert abs(v-0.2408)<1e-3, v\n"
                   "assert drift.psi_from_shares(np.array([.5,.5,0]), np.array([.5,.4,.1])) < 1, 'empty bin'\nprint('ok')")
    need(code == 0 and out.endswith("ok"), "psi_from_shares gives the reference value and survives an empty bin", "tools/drift.py: " + (out.splitlines()[-1] if out else ""))
    rep = jsonfile("runs/drift.json") or {}
    need(len(rep) == 4 and any("|line=motor" in k for k in rep.get("week4", {})), "runs/drift.json has four weeks, also by line")
    t = text("DRIFT_REPORT.md").lower()
    filled("DRIFT_REPORT.md", ["Statistic", "Shifted", "Features that moved", "Prediction shares", "What the delayed", "What the labels cannot", "Recommendation"])
    need("channel" in t and "amount" in t and "motor" in t, "the report names the channel mix and the motor amounts")
    shifted_row = next((x for x in t.splitlines() if x.startswith("| shifted")), "")
    need("tenure" not in shifted_row, "policy tenure is not called shifted", "policy tenure moved by a month: significant, but not shifted by PSI")


def check_4_4() -> None:
    code, out = sh(["uv", "run", "--quiet", "python", "-c",
                    "import sys, json; sys.path.insert(0,'tools'); import promlite\n"
                    "s = promlite.Series.load(sys.argv[1]); print(json.dumps(promlite.run_rules(s, 'monitoring/alerts.yml')))",
                    str(DATA / "recordings" / "spike.jsonl")])
    if not need(code == 0, "monitoring/alerts.yml parses and runs", "monitoring/alerts.yml: " + (out.splitlines()[-1] if out else "")):
        return
    rules = json.loads(out.splitlines()[-1])
    need(len(rules) >= 2, "two alert rules")
    err = [r for r in rules if any(720 <= f["from_s"] <= 1200 for f in r["fired"])]
    lat = [r for r in rules if any(f["from_s"] >= 1320 for f in r["fired"])]
    need(err, "a rule fires during the error spike (minutes 12 to 18)")
    need(lat, "a rule fires on the sustained latency rise (from minute 22)")
    blip = [r["alert"] for r in rules if any(300 <= f["from_s"] <= 540 for f in r["fired"])]
    need(not blip, "no rule fires on the one-minute latency blip (minute 6)", "fires on the one-minute blip: " + ", ".join(blip) + " (a for: duration stops that)")
    need(all(r["has_runbook"] and r["severity"] for r in rules), "every rule has a severity and a runbook_url")
    rb = text("RUNBOOK.md")
    need(re.search(r"Accountable for a rollback decision:\s*\S", rb) and "Munira" in rb, "the runbook names Munira Al-Ajmi as accountable for a rollback")
    need(rb.count("- ") >= 7 and all(re.search(rf"{h}:\s*\S", rb) for h in ("First three checks", "Roll back when")), "the runbook's sections are filled")
    need(re.search(r"Model:\s*\S", text("CAPSTONE.md")), "CAPSTONE.md names your capstone model")


CHECKS = {k.replace("check_", "").replace("_", "."): v for k, v in globals().items() if k.startswith("check_")}


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "check" or sys.argv[2] not in CHECKS:
        print(f"usage: uv run ../lab.py check <lab>   (labs: {', '.join(CHECKS)})")
        return 2
    lab = sys.argv[2]
    mark = (HERE / "LAB").read_text().strip() if (HERE / "LAB").is_file() else ""
    if mark and mark != lab:
        print(f"this folder is lab {mark}: run the check inside rifd-labs/{lab}")
        return 2
    CHECKS[lab]()
    for p in passed:
        print("  ok   " + p)
    for p in problems:
        print("  TODO " + p)
    print(f"lab {lab}: " + ("PASS" if not problems else f"{len(problems)} thing(s) to do"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
