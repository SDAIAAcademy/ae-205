"""Solution of lab 1.4: load and warm at start, /livez and /readyz, and what they say with no model."""

from common import check, expect_fail, fresh, restore, say, server, sh

lab = fresh("1.4")
say("the old /health says OK with no model file")
with server(lab, 18140, env={"RIFD_MODEL_DIR": "models/missing"}, ready_path="/health") as info:
    print("GET /health with no model:", info)
    assert info == {"status": "ok"}
expect_fail("1.4")
restore(lab, "src/rifd/app.py")
say("with the model missing: alive, not ready, and predictions refused with a reason")
with server(lab, 18141, env={"RIFD_MODEL_DIR": "models/missing"}, ready_path="/livez") as info:
    import json
    import urllib.error
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:18141/readyz", timeout=5)
        raise SystemExit("readyz should answer 503")
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        print("GET /readyz:", e.code, body["type"], body["detail"])
        assert e.code == 503
with server(lab, 18142) as info:
    print("GET /readyz with the model:", info)
    assert info["status"] == "ready" and info["warm_ms"] is not None
out = sh(["uv", "run", "--quiet", "pytest", "tests/test_health.py"], lab)[1]
print(out.splitlines()[-1])
check("1.4")
