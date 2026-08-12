"""Persist RadioAnalysisOutput to disk.

core_api reads {incident_id}.json files from a directory rather than
calling this service over HTTP, so its independent test suite can run
with no other service alive (settled 2026-08-12; see
contracts/api_contract.md, "Output location", and
services/core_api/app/pipeline.py::load_radio_analysis). This module
is the radio_ai side of that same convention: both default to
data/radio_analysis relative to the repo root, but each service
resolves its own path independently via its own env var -- there is no
shared config file between them, only an agreed-upon default.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.models import RadioAnalysisOutput

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "radio_analysis"


def output_dir() -> Path:
    configured = os.environ.get("RADIO_ANALYSIS_OUTPUT_DIR")
    return Path(configured) if configured else DEFAULT_OUTPUT_DIR


def write_radio_analysis(output: RadioAnalysisOutput) -> Path:
    """Write one incident's output as {incident_id}.json. Returns the path."""
    target_dir = output_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{output.incident_id}.json"
    path.write_text(output.model_dump_json(indent=2))
    return path
