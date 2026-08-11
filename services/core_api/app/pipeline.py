"""The live evaluation pipeline: evidence in, IncidentAssessment out.

Runs, in order: telemetry fingerprint -> ECHO LAP retrieval -> own-baseline
comparison -> lead time -> recurrence state -> interpretation-safe wording.

Every component score stays visible in the output. Nothing is combined
into a composite risk score, and no field is populated with a plausible
number when the honest answer is "no data".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.db import IncidentRecord
from app.models import (
    BaselineEvidence,
    BaselineStatus,
    EchoMatch,
    IncidentAssessment,
    RadioAnalysisOutput,
    RecurrenceState,
)


class EvaluationError(Exception):
    """An input the live pipeline needs is missing or unusable."""


@dataclass(frozen=True)
class EvaluationInputs:
    """Everything one evaluation needs, gathered before any computation."""

    record: IncidentRecord
    radio: RadioAnalysisOutput
    telemetry_path: Path
    prior_records: tuple[IncidentRecord, ...]
    telemetry_root: Path


def load_radio_analysis(
    incident_id: str, settings: Settings
) -> RadioAnalysisOutput:
    """Read Workstream B's `RadioAnalysisOutput` for one incident.

    Read from a directory of `{incident_id}.json` files rather than by
    calling `services/radio_ai` over HTTP, because Workstream C's
    independent test requires this service to evaluate an incident with
    no other service running. Where Workstream B's real outputs are
    written is not yet defined in any contract -- see PROGRESS_REPORT.md.
    """
    path = settings.radio_analysis_dir / f"{incident_id}.json"
    if not path.exists():
        raise EvaluationError(
            f"no RadioAnalysisOutput for {incident_id}: expected {path}. "
            f"Set CORE_API_RADIO_ANALYSIS_DIR to where Workstream B writes "
            f"its output."
        )
    try:
        return RadioAnalysisOutput.model_validate_json(path.read_text())
    except Exception as exc:  # noqa: BLE001 -- surfaced verbatim to the caller
        raise EvaluationError(
            f"RadioAnalysisOutput for {incident_id} does not match the frozen "
            f"contract: {exc}"
        ) from exc


def resolve_telemetry_path(record: IncidentRecord, settings: Settings) -> Path:
    """Resolve a manifest telemetry path, checking it exists."""
    candidate = Path(record.telemetry_window_path)
    if not candidate.is_absolute():
        candidate = (settings.telemetry_root / candidate).resolve()
    if not candidate.exists():
        raise EvaluationError(
            f"telemetry window for {record.incident_id} not found at {candidate} "
            f"(manifest says {record.telemetry_window_path!r})"
        )
    return candidate


def evaluate_incident(inputs: EvaluationInputs) -> IncidentAssessment:
    """Run the full evidence pipeline for one incident.

    Heavy dependencies are imported here rather than at module scope so
    that importing `app.main` -- and therefore serving `/health` or
    fixture mode -- never loads pandas, torch, or a sentence-transformer.
    """
    from evidence_memory.baseline import compare_to_baseline
    from evidence_memory.lead_time import measure_lead_time
    from evidence_memory.recurrence import assess_recurrence
    from evidence_memory.retrieval import IncidentMemory, MemoryEntry
    from evidence_memory.telemetry_fingerprint import (
        TelemetryWindowError,
        build_fingerprint,
        load_window,
        select_segment,
    )

    record = inputs.record
    radio = inputs.radio

    if radio.complaint_category is None:
        raise EvaluationError(
            f"{record.incident_id} has no complaint_category; there is no "
            f"reported phenomenon to assess. The contract allows a null "
            f"category for radio that is not a complaint, but "
            f"IncidentAssessment.reported_phenomenon has no null option."
        )

    window = load_window(inputs.telemetry_path)
    current_rows = select_segment(window, lap=record.lap, segment=record.segment)
    if current_rows.empty:
        current_rows = select_segment(window, lap=record.lap)

    try:
        current_fingerprint = build_fingerprint(current_rows)
    except TelemetryWindowError:
        current_fingerprint = None

    # --- ECHO LAP retrieval ---------------------------------------------
    memory = IncidentMemory()
    entries: list[MemoryEntry] = []
    for prior in inputs.prior_records:
        entries.append(
            MemoryEntry(
                incident_id=prior.incident_id,
                transcript=prior.transcript,
                segment=prior.segment,
                complaint_category=prior.complaint_category.value,
                event_time_ms=prior.event_time_ms,
                fingerprint=_prior_fingerprint(
                    prior,
                    inputs.telemetry_root,
                    build_fingerprint,
                    load_window,
                    select_segment,
                ),
            )
        )
    if entries:
        memory.add_many(entries)

    retrieval = memory.best_match(
        radio.transcript,
        query_fingerprint=current_fingerprint,
        query_segment=record.segment,
        query_category=radio.complaint_category.value,
        exclude_incident_id=record.incident_id,
        before_event_time_ms=record.event_time_ms,
    )

    echo_match = None
    if retrieval.match is not None:
        candidate = retrieval.match
        assert candidate.telemetry_similarity is not None  # gated in best_match
        echo_match = EchoMatch(
            incident_id=candidate.incident_id,
            semantic_similarity=round(candidate.semantic_similarity, 4),
            telemetry_similarity=round(candidate.telemetry_similarity, 4),
            same_segment=candidate.same_segment,
            label=candidate.label,
        )

    # --- own-baseline evidence ------------------------------------------
    comparison = compare_to_baseline(
        window, current_lap=record.lap, segment=record.segment
    )
    baseline_evidence = BaselineEvidence(
        throttle_pickup_delta_pct=comparison.throttle_pickup_delta_pct,
        sector_delta_s=comparison.sector_delta_s,
        status=BaselineStatus(comparison.status),
    )

    # --- lead time -------------------------------------------------------
    lead = measure_lead_time(
        window,
        radio_event_time_s=record.event_time_ms / 1000.0,
        segment=record.segment,
    )

    # --- recurrence (MVP: synchronous, see evidence_memory/recurrence.py) -
    recurrence = assess_recurrence(
        transcript=radio.transcript,
        baseline_status=comparison.status,
        echo_incident_id=echo_match.incident_id if echo_match else None,
        telemetry_similarity=echo_match.telemetry_similarity if echo_match else None,
        same_segment=echo_match.same_segment if echo_match else False,
        has_prior_same_category=any(
            prior.complaint_category == radio.complaint_category
            for prior in inputs.prior_records
        ),
    )

    return IncidentAssessment(
        incident_id=record.incident_id,
        lap=record.lap,
        segment=record.segment,
        reported_phenomenon=radio.complaint_category,
        baseline_evidence=baseline_evidence,
        echo_match=echo_match,
        driver_warning_lead_time_s=lead.lead_time_s,
        recurrence_state=RecurrenceState(recurrence.state),
        human_message=compose_human_message(
            baseline_status=comparison.status,
            echo_match=echo_match,
            lead_time_s=lead.lead_time_s,
            recurrence_state=recurrence.state,
        ),
    )


def compose_human_message(
    *,
    baseline_status: str,
    echo_match: EchoMatch | None,
    lead_time_s: float | None,
    recurrence_state: str,
) -> str:
    """Interpretation-safe wording for the incident card.

    Rules this wording obeys, from the charter and the contract:

    - "reported phenomenon", never "diagnosed fault";
    - no claim of a confirmed mechanical cause, lie detection, or any
      psychological or physiological state;
    - a null lead time is stated explicitly as "No measurable lead-time
      established", never omitted or softened;
    - similarity is described as resemblance to a prior *report*, never
      as the probability of a shared cause.
    """
    parts: list[str] = []

    if baseline_status == "BEHAVIOR_CONSISTENT":
        parts.append(
            "Telemetry at this segment deviates from the driver's own recent "
            "baseline, consistent with the reported phenomenon"
        )
    elif baseline_status == "NO_DEVIATION":
        parts.append(
            "Telemetry at this segment is within the driver's own recent "
            "baseline; no deviation measured"
        )
    else:
        parts.append(
            "Not enough baseline laps at this segment to compare against the "
            "driver's own recent behaviour"
        )

    if echo_match is not None:
        parts.append(
            f"resembles an earlier reported concern ({echo_match.incident_id}) "
            f"by prototype similarity"
        )
    else:
        parts.append("no earlier report cleared the retrieval threshold")

    if lead_time_s is None:
        parts.append("No measurable lead-time established")
    else:
        parts.append(
            f"an observable performance change followed the radio call by "
            f"{lead_time_s:.1f}s"
        )

    if recurrence_state == "CONFIRMED_BY_RADIO":
        parts.append("The driver's message refers to a repeat")
    elif recurrence_state == "POSSIBLE_RECURRENCE":
        parts.append("Possible recurrence; review recommended")

    return ". ".join(_sentence_case(part) for part in parts) + "."


def _sentence_case(text: str) -> str:
    """Capitalise the first letter without touching the rest."""
    return text[:1].upper() + text[1:] if text else text


def _prior_fingerprint(
    prior: IncidentRecord,
    telemetry_root: Path,
    build_fingerprint,
    load_window,
    select_segment,
):
    """Fingerprint a stored incident's own window, or None if unusable.

    A prior incident whose telemetry cannot be read is kept in memory
    without a fingerprint rather than dropped: it still contributes
    semantic evidence, and `best_match` refuses to report a match it
    cannot evidence with telemetry.
    """
    from evidence_memory.telemetry_fingerprint import TelemetryWindowError

    try:
        path = Path(prior.telemetry_window_path)
        if not path.is_absolute():
            path = (telemetry_root / path).resolve()
        if not path.exists():
            return None
        window = load_window(path)
        rows = select_segment(window, lap=prior.lap, segment=prior.segment)
        if rows.empty:
            rows = select_segment(window, lap=prior.lap)
        return build_fingerprint(rows)
    except (TelemetryWindowError, OSError, KeyError):
        return None


def load_manifest_entries(settings: Settings) -> list[IncidentRecord]:
    """Read Workstream A's incident manifest into storage records."""
    if not settings.manifest_path.exists():
        raise EvaluationError(
            f"incident manifest not found at {settings.manifest_path}. "
            f"Set CORE_API_MANIFEST_PATH, or run Workstream A's "
            f"build_incident_manifest.py."
        )
    entries = json.loads(settings.manifest_path.read_text())
    return [IncidentRecord.from_manifest_entry(entry) for entry in entries]
