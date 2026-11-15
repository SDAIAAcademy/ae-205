"""Solution of lab 2.2: scan the dependencies, fix the critical finding, take the key out of the code."""

from common import check, expect_fail, fresh, restore, say, sh, write

lab = fresh("2.2")
(lab / "runs").mkdir(exist_ok=True)
say("scan the dependencies as supplied")
sh(["uv", "export", "--no-dev", "--no-hashes", "--frozen", "--quiet", "-o", "runs/requirements-audit.txt"], lab)
code, out = sh(["uv", "run", "--quiet", "pip-audit", "-r", "runs/requirements-audit.txt", "--no-deps", "--disable-pip"], lab, check=False, timeout=600)
print("\n".join(x for x in out.splitlines() if "h11" in x or "Found" in x))
assert code != 0 and "h11" in out, "the supplied lock should carry the vulnerable h11"
expect_fail("2.2")
say("raise h11 to a fixed version and lock again")
restore(lab, "pyproject.toml", "uv.lock", "src/rifd/settings.py")
say("the key leaves the code and the image: it is read from configuration")
supplied = (lab / "supplied" / "Dockerfile").read_text(encoding="utf-8")
supplied = supplied.replace("ENV RIFD_LOOKUP_KEY=rifd-lookup-key-for-the-labs-only RIFD_MODEL_DIR=", "# The key is given at run time (docker run -e RIFD_LOOKUP_KEY or a Secret), never in the image.\nENV RIFD_MODEL_DIR=")
write(lab, "supplied/Dockerfile", supplied)
write(lab, "secrets/lookup.key", "rifd-lookup-key-for-the-labs-only\n")
check("2.2")
