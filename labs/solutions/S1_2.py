"""Solution of lab 1.2: two versions in the registry, an overwrite refused, aliases, loading by version."""

import hashlib

from common import WS, check, expect_fail, fresh, say, sh, uv

lab = fresh("1.2")
expect_fail("1.2")
data_hash = hashlib.sha256((WS / "data" / "claims.csv").read_bytes()).hexdigest()
for v in ("1.0.0", "1.1.0"):
    out = uv(lab, "python", "-m", "rifd.registry", "register", "--name", "farz", "--version", v, "--from", f"models/farz-{v}",
             "--tag", f"data_sha256={data_hash}", "--tag", "trained_by=Adel Al-Shaikh", "--tag", f"source=notebook/train_triage.py ({'logistic regression' if v == '1.0.0' else 'gradient boosting'})")
    print(out)
say("a registered version never changes")
code, out = sh(["uv", "run", "--quiet", "python", "-m", "rifd.registry", "register", "--name", "farz", "--version", "1.0.0", "--from", "models/farz-1.1.0"], lab, check=False)
print(out)
assert code == 1 and "already registered" in out
uv(lab, "python", "-m", "rifd.registry", "alias", "--name", "farz", "--alias", "champion", "--version", "1.0.0")
uv(lab, "python", "-m", "rifd.registry", "alias", "--name", "farz", "--alias", "challenger", "--version", "1.1.0")
for ref in ("1.1.0", "champion", "challenger"):
    out = uv(lab, "python", "-m", "rifd.registry", "load", "--name", "farz", "--ref", ref)
    print(out)
    assert "10 of 10" in out
check("1.2")
