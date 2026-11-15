"""Solution of lab 2.4: the similar-claims endpoint, its manifest, and the two services measured."""

import json

from common import check, expect_fail, fresh, restore, say, sh, uv

lab = fresh("2.4")
expect_fail("2.4")
restore(lab, "src/rifd/routes_similar.py", "k8s/shabih.yaml")
print(sh(["uv", "run", "--quiet", "pytest", "tests/test_similar.py"], lab)[1].splitlines()[-1])
(lab / "runs").mkdir(exist_ok=True)
for svc, port in (("farz", 18240), ("shabih", 18241)):
    out = uv(lab, "python", "tools/measure.py", "--service", svc, "--port", str(port))
    m = json.loads(out.splitlines()[-1])
    (lab / "runs" / f"measure_{svc}.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    say(f"{svc}: ready in {m['ready_s']} s, load {m['load_ms']} ms, {m['rss_ready_mib']} MiB at ready, {m['rss_after_mib']} MiB after {m['requests']} requests, {m['ok']} ok")
check("2.4")
