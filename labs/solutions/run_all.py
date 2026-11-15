"""Run every solution, or the ones named, and stop at the first that fails.

    uv run --no-project python labs/solutions/run_all.py            # all sixteen
    uv run --no-project python labs/solutions/run_all.py 2.4 3.1    # some

Set RIFD_LABS to the workspace (the default is rifd-labs beside the course). Labs 2.1 and 2.3 also
build and deploy when a container runtime and a cluster answer; otherwise they check the files.
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
labs = sys.argv[1:] or [f"{d}.{s}" for d in range(1, 5) for s in range(1, 5)]
for lab in labs:
    script = HERE / f"S{lab.replace('.', '_')}.py"
    t0 = time.monotonic()
    code = subprocess.call([sys.executable, str(script)], cwd=HERE)
    print(f"== lab {lab}: {'PASS' if code == 0 else 'FAILED'} in {time.monotonic() - t0:.0f} s", flush=True)
    if code != 0:
        sys.exit(code)
