"""Guards on the frozen contracts.

`app/models.py` and `contracts/schemas/*.json` are kept in sync by hand
(models.py says so). These tests make a drift fail loudly instead of
silently, in both directions, and check the boundary rules Workstream C
promised the other workstreams it would keep.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import app  # noqa: F401  -- puts services/ on sys.path
from app.config import REPO_ROOT
from app.models import (
    BaselineStatus,
    IncidentAssessment,
    RadioAnalysisOutput,
    RecurrenceState,
    ReportedPhenomenon,
    ToneLabel,
)

CONTRACTS = REPO_ROOT / "contracts"
OWNED_SOURCE_DIRS = (
    REPO_ROOT / "services" / "core_api" / "app",
    REPO_ROOT / "services" / "evidence_memory",
)


def load_schema(name: str) -> dict:
    return json.loads((CONTRACTS / "schemas" / name).read_text())


# --- models mirror the schemas, both directions -------------------------


def test_incident_assessment_fields_match_the_schema():
    schema = load_schema("incident_assessment.schema.json")
    assert set(IncidentAssessment.model_fields) == set(schema["properties"])
    assert set(schema["required"]) == set(schema["properties"])


def test_radio_analysis_output_fields_match_the_schema():
    schema = load_schema("radio_analysis_output.schema.json")
    assert set(RadioAnalysisOutput.model_fields) == set(schema["properties"])


def test_radio_analysis_required_fields_have_no_defaults():
    """A field the contract requires must not be silently defaulted here."""
    schema = load_schema("radio_analysis_output.schema.json")
    for name in schema["required"]:
        assert RadioAnalysisOutput.model_fields[name].is_required(), name


def test_baseline_evidence_fields_match_the_schema():
    schema = load_schema("incident_assessment.schema.json")
    nested = schema["properties"]["baseline_evidence"]
    from app.models import BaselineEvidence

    assert set(BaselineEvidence.model_fields) == set(nested["properties"])
    assert set(nested["required"]) == set(nested["properties"])


def test_echo_match_fields_match_the_schema():
    schema = load_schema("incident_assessment.schema.json")
    nested = schema["properties"]["echo_match"]
    from app.models import EchoMatch

    assert set(EchoMatch.model_fields) == set(nested["properties"])


@pytest.mark.parametrize(
    "enum_cls,schema_file,pointer",
    [
        (ReportedPhenomenon, "incident_assessment.schema.json", "reported_phenomenon"),
        (RecurrenceState, "incident_assessment.schema.json", "recurrence_state"),
        (ToneLabel, "radio_analysis_output.schema.json", "tone_label"),
    ],
)
def test_enums_match_the_schema(enum_cls, schema_file, pointer):
    schema = load_schema(schema_file)
    assert {member.value for member in enum_cls} == set(
        schema["properties"][pointer]["enum"]
    )


def test_baseline_status_enum_matches_schema():
    schema = load_schema("incident_assessment.schema.json")
    allowed = schema["properties"]["baseline_evidence"]["properties"]["status"]["enum"]
    assert {member.value for member in BaselineStatus} == set(allowed)


def test_complaint_taxonomy_is_frozen_at_five_categories():
    """Charter: no more than five categories, ever."""
    assert len(ReportedPhenomenon) == 5


def test_complaint_category_allows_null_but_phenomenon_does_not():
    """The one genuine asymmetry between the two contracts."""
    radio_schema = load_schema("radio_analysis_output.schema.json")
    assert None in radio_schema["properties"]["complaint_category"]["enum"]

    assessment_schema = load_schema("incident_assessment.schema.json")
    assert None not in assessment_schema["properties"]["reported_phenomenon"]["enum"]


# --- the shipped fixtures still parse ------------------------------------


def test_assessment_fixture_parses_with_the_model():
    fixture = json.loads(
        (CONTRACTS / "fixtures" / "incident_assessment.sample.json").read_text()
    )
    assert IncidentAssessment.model_validate(fixture)


def test_radio_fixture_parses_with_the_model():
    fixture = json.loads(
        (CONTRACTS / "fixtures" / "radio_analysis_output.sample.json").read_text()
    )
    parsed = RadioAnalysisOutput.model_validate(fixture)
    assert parsed.incident_id == "INC-017"
    # The Mask field is present in the fixture and must not be required.
    assert parsed.text_tone_disagreement is not None


def test_radio_output_parses_without_the_mask_field():
    """Cut rule: dropping text_tone_disagreement must break nothing."""
    fixture = json.loads(
        (CONTRACTS / "fixtures" / "radio_analysis_output.sample.json").read_text()
    )
    fixture.pop("text_tone_disagreement")
    parsed = RadioAnalysisOutput.model_validate(fixture)
    assert parsed.text_tone_disagreement is None


def test_manifest_fixture_maps_onto_the_storage_schema():
    from app.db import IncidentRecord

    entries = json.loads(
        (CONTRACTS / "fixtures" / "incident_manifest.sample.json").read_text()
    )
    for entry in entries:
        assert IncidentRecord.from_manifest_entry(entry)


# --- workstream boundary -------------------------------------------------


def _owned_python_files() -> list[Path]:
    files: list[Path] = []
    for directory in OWNED_SOURCE_DIRS:
        files.extend(
            path
            for path in directory.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    return files


def test_no_module_imports_another_workstreams_code():
    """Integration happens through JSON contracts only, never imports."""
    forbidden = ("radio_ai", "apps.web", "mock_server", "data_pipeline")
    offenders: list[str] = []

    for path in _owned_python_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if any(name == bad or name.startswith(f"{bad}.") for bad in forbidden):
                    offenders.append(f"{path.name}: {name}")

    assert not offenders, f"cross-workstream imports found: {offenders}"


def test_owned_source_files_exist_where_contributing_says():
    """Workstream C owns these paths and only these."""
    assert (REPO_ROOT / "services" / "core_api").is_dir()
    assert (REPO_ROOT / "services" / "evidence_memory").is_dir()
    assert (REPO_ROOT / "storage" / "schema.sql").is_file()


def test_heavy_dependencies_are_not_imported_at_module_scope():
    """CONTRIBUTING: lazy-import heavy SDKs inside the functions needing them.

    Keeps the service importable, and /health servable, without torch or
    a model cache present.
    """
    heavy = {"torch", "sentence_transformers", "faiss", "transformers"}
    offenders: list[str] = []

    for path in _owned_python_files():
        tree = ast.parse(path.read_text())
        for node in tree.body:  # module scope only
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".")[0] in heavy:
                    offenders.append(f"{path.name}: {name}")

    assert not offenders, f"heavy imports at module scope: {offenders}"


def test_public_dataclasses_expose_no_composite_score():
    """Charter: never a magic risk score; always the components."""
    from evidence_memory.baseline import BaselineComparison
    from evidence_memory.recurrence import RecurrenceAssessment
    from evidence_memory.retrieval import Candidate

    banned = ("risk", "composite", "overall_score", "combined")
    for cls in (Candidate, BaselineComparison, RecurrenceAssessment):
        for field in cls.__dataclass_fields__:
            assert not any(word in field.lower() for word in banned), (cls, field)
