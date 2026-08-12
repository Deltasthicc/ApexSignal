"""The manifest is ground truth. A placeholder that reaches disk reaches the UI."""

from __future__ import annotations

import pytest

from build_incident_manifest import build_manifest, validate_entries


def entry(**overrides) -> dict:
    base = {
        "incident_id": "INC-017",
        "session_id": "2023_ITALIAN_GRAND_PRIX_R",
        "driver": "VER",
        "event_time_ms": 1_842_500,
        "lap": 17,
        "sector_or_corner": "T7_EXIT",
        "audio_path": "data/audio/INC-017.wav",
        "verified_transcript": "Rear is moving on throttle.",
        "complaint_label": "EXIT_TRACTION_REAR",
        "telemetry_window_path": "data/telemetry/INC-017.parquet",
    }
    base.update(overrides)
    return base


def test_a_curated_entry_validates():
    assert validate_entries([entry()]) == []


@pytest.mark.parametrize("field", ["incident_id", "session_id", "event_time_ms", "lap"])
def test_a_missing_required_field_is_reported(field):
    problems = validate_entries([entry(**{field: None})])

    assert any(field in problem for problem in problems)


def test_the_fixture_placeholders_are_rejected():
    problems = validate_entries([entry(session_id="PLACEHOLDER_SESSION")])

    assert any("placeholder" in problem for problem in problems)


def test_a_zero_event_time_is_rejected_as_not_a_real_session_time():
    """0 is the fixture default, and a real radio call always follows t0."""
    problems = validate_entries([entry(event_time_ms=0)])

    assert any("event_time_ms" in problem for problem in problems)
    assert any("session t0" in problem for problem in problems)


def test_duplicate_incident_ids_are_rejected():
    problems = validate_entries([entry(), entry()])

    assert any("duplicate" in problem for problem in problems)


def test_writing_an_empty_manifest_needs_an_explicit_opt_in():
    with pytest.raises(SystemExit, match="Refusing to write an empty manifest"):
        build_manifest([])


def test_invalid_entries_are_never_written(tmp_path, monkeypatch):
    import build_incident_manifest

    target = tmp_path / "incident_manifest.json"
    monkeypatch.setattr(build_incident_manifest, "MANIFEST_PATH", target)

    with pytest.raises(SystemExit):
        build_manifest([entry(event_time_ms=0)])

    assert not target.exists()
