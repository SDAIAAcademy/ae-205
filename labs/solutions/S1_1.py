"""Solution of lab 1.1: the notebook's pickle becomes an artefact with its decision rule and its pins."""

import json

from common import check, expect_fail, fresh, restore, say, sh, uv

lab = fresh("1.1")
say("what the pickle needs on load: the modules it imports")
out = uv(lab, "python", "-c", "import pickletools,sys; ops=[a for o,a,p in pickletools.genops(open(sys.argv[1],'rb')) if o.name in ('GLOBAL','STACK_GLOBAL','SHORT_BINUNICODE') and isinstance(a,str) and a.startswith('sklearn')]; print(sorted(set(ops))[:6])", "../notebook/farz_notebook.pkl")
print(out)
assert "sklearn" in out

say("the start state exports without the decision rule: the reference predictions do not match")
code, out = sh(["uv", "run", "--quiet", "python", "tools/export_artefact.py"], lab, check=False)
print(out)
assert code == 1 and "of 10 reference predictions match" in out and "10 of 10" not in out, "without the rule the predictions should differ"
expect_fail("1.1")

say("the finished export: decision rule from cell 14, pins from this environment")
restore(lab, "tools/export_artefact.py")
out = uv(lab, "python", "tools/export_artefact.py")
print(out)
assert "10 of 10" in out
meta = json.loads((lab / "artefacts/farz-1.0.0/metadata.json").read_text(encoding="utf-8"))
assert meta["decision"] == {"investigate_threshold": 0.3}
print((lab / "artefacts/farz-1.0.0/requirements.txt").read_text())

say("reload in an environment that holds only the pins")
out = sh(["uv", "run", "--isolated", "--no-project", "--quiet", "--with-requirements", "artefacts/farz-1.0.0/requirements.txt",
          "python", "tools/check_reload.py", "artefacts/farz-1.0.0"], lab)[1]
print(out)
assert "10 of 10" in out
check("1.1")
