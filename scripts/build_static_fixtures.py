"""Compile contract fixtures into a typed browser module for Static Spaces.

The Docker/local path still uses HTTP APIs. Hugging Face Static Space builds
set NEXT_PUBLIC_DATA_MODE=embedded and use this exact contract data so the
public demo remains interactive without pretending an unavailable backend is
online.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "contracts" / "fixtures"
OUTPUT = ROOT / "apps" / "web" / "src" / "data" / "demoFixtures.ts"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    manifest = read(FIXTURES / "incident_manifest.sample.json")
    radio = {
        entry["incident_id"]: read(FIXTURES / "radio_analysis" / f"{entry['incident_id']}.json")
        for entry in manifest
    }
    assessments = {
        entry["incident_id"]: read(FIXTURES / "incident_assessment" / f"{entry['incident_id']}.json")
        for entry in manifest
    }
    payload = {"manifest": manifest, "radio": radio, "assessments": assessments}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "// Generated from contracts/fixtures by scripts/build_static_fixtures.py.\n"
        "// This is the honest offline/static demo path, not live model output.\n"
        f"export const DEMO_FIXTURES = {json.dumps(payload, ensure_ascii=True, separators=(',', ':'))} as const;\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(manifest)} incident fixtures to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
