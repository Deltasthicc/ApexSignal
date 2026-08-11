"""Pydantic models mirroring contracts/schemas/incident_assessment.schema.json.

Keep this file and the JSON schema in sync by hand; there is no
codegen step for the hackathon build.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ReportedPhenomenon(str, Enum):
    EXIT_TRACTION_REAR = "EXIT_TRACTION_REAR"
    FRONT_TURNIN_BRAKE = "FRONT_TURNIN_BRAKE"
    TYRE_GRIP_DEGRADATION = "TYRE_GRIP_DEGRADATION"
    VISIBILITY_TRACK_CONDITION = "VISIBILITY_TRACK_CONDITION"
    MECHANICAL_OTHER = "MECHANICAL_OTHER"


class BaselineStatus(str, Enum):
    BEHAVIOR_CONSISTENT = "BEHAVIOR_CONSISTENT"
    NO_DEVIATION = "NO_DEVIATION"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RecurrenceState(str, Enum):
    NONE = "NONE"
    POSSIBLE_RECURRENCE = "POSSIBLE_RECURRENCE"
    CONFIRMED_BY_RADIO = "CONFIRMED_BY_RADIO"


class ToneLabel(str, Enum):
    CALM = "CALM"
    ELEVATED_AROUSAL = "ELEVATED_AROUSAL"
    FATIGUED = "FATIGUED"


class TextToneDisagreement(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class RadioAnalysisOutput(BaseModel):
    """Workstream B's output, consumed by this service.

    Mirrors contracts/schemas/radio_analysis_output.schema.json exactly.
    core_api never imports services/radio_ai; this JSON shape is the only
    integration point.

    `text_tone_disagreement` is optional and is deliberately not consumed
    by the evidence pipeline: The Mask is a post-core feature (charter
    section 5) and the contract's cut rules allow it to be dropped
    entirely. Nothing here breaks when it is absent.
    """

    incident_id: str
    transcript: str
    tone_label: ToneLabel
    tone_score: float = Field(ge=0, le=1)
    tone_confidence: float = Field(ge=0, le=1)
    complaint_category: ReportedPhenomenon | None = None
    category_confidence: float | None = Field(default=None, ge=0, le=1)
    text_tone_disagreement: TextToneDisagreement | None = None


class BaselineEvidence(BaseModel):
    throttle_pickup_delta_pct: float
    sector_delta_s: float
    status: BaselineStatus


class EchoMatch(BaseModel):
    incident_id: str
    semantic_similarity: float = Field(ge=0, le=1)
    telemetry_similarity: float = Field(ge=0, le=1)
    same_segment: bool
    label: str


class IncidentAssessment(BaseModel):
    """Frozen contract. See contracts/api_contract.md before changing this."""

    incident_id: str
    lap: int = Field(ge=0)
    segment: str
    reported_phenomenon: ReportedPhenomenon
    baseline_evidence: BaselineEvidence
    echo_match: EchoMatch | None
    driver_warning_lead_time_s: float | None
    recurrence_state: RecurrenceState
    human_message: str
