"""Runtime configuration for core_api.

Every filesystem input the live pipeline needs is declared here, so the
set of things Workstreams A and B must deliver is one short list rather
than paths scattered through the code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    """Resolved paths and mode for one process."""

    evaluate_mode: str
    db_path: str
    manifest_path: Path
    radio_analysis_dir: Path
    telemetry_root: Path
    fixture_path: Path

    @property
    def is_live(self) -> bool:
        return self.evaluate_mode.lower() == "live"


def load_settings() -> Settings:
    """Read settings from the environment, resolving relative paths.

    Relative paths resolve against the repository root, which is where
    the manifest's `telemetry_window_path` values are anchored
    (`data/telemetry/INC-017.parquet`).
    """
    return Settings(
        evaluate_mode=os.environ.get("EVALUATE_MODE", "fixture"),
        db_path=os.environ.get("CORE_API_DB_PATH", str(REPO_ROOT / "storage" / "incidents.db")),
        manifest_path=_resolve(
            os.environ.get("CORE_API_MANIFEST_PATH", "data/incident_manifest.json")
        ),
        radio_analysis_dir=_resolve(
            os.environ.get("CORE_API_RADIO_ANALYSIS_DIR", "data/radio_analysis")
        ),
        telemetry_root=_resolve(os.environ.get("CORE_API_TELEMETRY_ROOT", ".")),
        fixture_path=REPO_ROOT
        / "contracts"
        / "fixtures"
        / "incident_assessment.sample.json",
    )


def _resolve(raw: str) -> Path:
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()
