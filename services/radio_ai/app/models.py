"""Pydantic models mirroring contracts/schemas/radio_analysis_output.schema.json.

Keep this file and the JSON schema in sync by hand; there is no
codegen step for the hackathon build.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ToneLabel(str, Enum):
    CALM = "CALM"
    ELEVATED_AROUSAL = "ELEVATED_AROUSAL"
    FATIGUED = "FATIGUED"


class ComplaintCategory(str, Enum):
    EXIT_TRACTION_REAR = "EXIT_TRACTION_REAR"
    FRONT_TURNIN_BRAKE = "FRONT_TURNIN_BRAKE"
    TYRE_GRIP_DEGRADATION = "TYRE_GRIP_DEGRADATION"
    VISIBILITY_TRACK_CONDITION = "VISIBILITY_TRACK_CONDITION"
    MECHANICAL_OTHER = "MECHANICAL_OTHER"


class TextToneDisagreement(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class RadioAnalysisOutput(BaseModel):
    """Frozen contract. See contracts/api_contract.md before changing this."""

    incident_id: str
    transcript: str
    tone_label: ToneLabel
    tone_score: float = Field(ge=0, le=1)
    tone_confidence: float = Field(ge=0, le=1)
    complaint_category: ComplaintCategory | None = None
    category_confidence: float | None = Field(default=None, ge=0, le=1)
    text_tone_disagreement: TextToneDisagreement | None = None
