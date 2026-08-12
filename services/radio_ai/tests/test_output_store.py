import json

from app.models import RadioAnalysisOutput
from app.output_store import write_radio_analysis


def test_write_radio_analysis_writes_incident_id_json(tmp_path, monkeypatch):
    monkeypatch.setenv("RADIO_ANALYSIS_OUTPUT_DIR", str(tmp_path))
    output = RadioAnalysisOutput(
        incident_id="INC-TEST-001",
        transcript="Rear is moving on throttle.",
        tone_label="ELEVATED_AROUSAL",
        tone_score=0.7,
        tone_confidence=0.6,
    )

    path = write_radio_analysis(output)

    assert path == tmp_path / "INC-TEST-001.json"
    assert path.exists()
    on_disk = json.loads(path.read_text())
    assert on_disk["incident_id"] == "INC-TEST-001"
    # Round-trips through the exact contract core_api validates against.
    RadioAnalysisOutput.model_validate_json(path.read_text())
