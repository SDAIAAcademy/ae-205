"""Solution of lab 2.3: a manifest that runs on a single-node cluster, and where each service may run.

The deployment is applied only when a cluster answers; otherwise the check reviews the manifest.
"""

import shutil

from common import check, expect_fail, fresh, restore, say, sh, write

PLACEMENT = """# Where may each service run?

Rifd applies the four levels of the national Data Classification Policy (Top Secret, Secret,
Restricted, Public) to its own data. Its hosting options: the in-Kingdom cluster in Riyadh, and a
monitoring service (dashboards and log search) hosted outside the Kingdom.

| Service or data flow | What it holds | Classification | Where it may run | Why |
|---|---|---|---|---|
| Farz, the triage service | claims with the member's name, national id and mobile, and health details | Restricted | the in-Kingdom cluster | personal and health data; Rifd keeps Restricted data in the Kingdom and the transfer regulation would apply to any copy abroad |
| Shabih, the similar-claims service and its index | claim descriptions, which can name people and places; the index keeps claim id, line and incident only | Restricted | the in-Kingdom cluster | the descriptions are free text and can carry personal data even after the personal fields are dropped |
| Metrics and dashboards (counts, latency, labels; no claim content) | aggregate counts and timings by route, status, version and label | Public, by a written decision of the data owner (the metrics carry no personal data) | the monitoring service abroad, if the redaction tests pass and the owner signs | nothing in them identifies a member; the logs stay in the Kingdom because a log line can carry claim content |

Who signs this off at Rifd: Bassam Al-Jaber (data protection officer), with Munira Al-Ajmi (owner of the triage service)
"""

lab = fresh("2.3")
expect_fail("2.3")
restore(lab, "k8s/farz.yaml")
write(lab, "PLACEMENT.md", PLACEMENT)
if shutil.which("kubectl") and sh(["kubectl", "cluster-info"], lab, check=False, timeout=30)[0] == 0:
    say("a cluster answers: applying")
    print(sh(["kubectl", "apply", "-f", "k8s/config.yaml", "-f", "k8s/farz.yaml"], lab)[1])
    print(sh(["kubectl", "rollout", "status", "deployment/farz", "--timeout=180s"], lab, check=False)[1])
else:
    say("no cluster answers here: the manifest was checked as a file only")
check("2.3")
