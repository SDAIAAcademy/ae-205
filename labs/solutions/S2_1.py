"""Solution of lab 2.1: a multi-stage container file and its ignore file.

The build and the size measurement run only when a container runtime answers; otherwise the lab's
check reviews the files and says that the image was not measured.
"""

import shutil
import sys

from common import KIT, PROJECT, check, expect_fail, fresh, restore, say, sh

sys.path.insert(0, str(KIT))
from lab import dockerfile_findings  # noqa: E402

lab = fresh("2.1")
expect_fail("2.1")
say("what the naive file gets wrong")
for f in dockerfile_findings((PROJECT / "Dockerfile.naive").read_text(encoding="utf-8")):
    print("  naive:", f)
restore(lab, "Dockerfile", ".dockerignore")
assert dockerfile_findings((lab / "Dockerfile").read_text(encoding="utf-8")) == []
tool = next((t for t in ("docker", "podman") if shutil.which(t) and sh([t, "info"], lab, check=False, timeout=30)[0] == 0), None)
if tool:
    say(f"building with {tool}")
    print(sh([tool, "build", "-t", "rifd/claims:1.0.0", "."], lab, timeout=1800)[1][-800:])
else:
    say("no container runtime answers here: the image was not built")
check("2.1")
