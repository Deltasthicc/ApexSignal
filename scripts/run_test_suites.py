"""Run each Python service suite in its own import root.

Both backend services intentionally expose a top-level package named `app`.
Running pytest once from the repository root makes those packages collide, so
the supported project-wide command executes the suites in isolated processes.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITES = (
    ROOT / "services" / "core_api",
    ROOT / "services" / "radio_ai",
    ROOT / "data_pipeline",
)


def main() -> int:
    for suite in SUITES:
        print(f"\n== {suite.relative_to(ROOT)} ==", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=suite,
            check=False,
        )
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
