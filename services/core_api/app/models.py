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
