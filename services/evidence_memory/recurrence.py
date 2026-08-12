"""Recurrence state -- MVP-simplified, computed synchronously.

## What this is, and what it replaces

Charter section 6.1 describes two operational flows. Flow A is incident
capture. **Flow B is a background recurrence monitor**: a process that
continuously scans new telemetry against stored incident fingerprints,
independent of any new radio event, and raises a possible recurrence
before the driver reports the issue again.

**Flow B is cut from the MVP.** This module is its synchronous
stand-in: recurrence is evaluated once, inside `evaluate()`, using the
evidence already gathered for that incident. Nothing scans in the
background, and nothing raises an alert between radio events.

The honest consequence: the system cannot currently claim to surface a
recurrence *before* the driver reports it. It can only characterise a
recurrence at the moment a report arrives. Any demo narration must
respect that -- see PROGRESS_REPORT.md.

## Why telemetry similarity is not the discriminator

Measured over synthetic segment traces:

    clean lap vs clean lap, same corner        1.0000
    clean lap vs deteriorated lap, same corner 0.9920
    same corner vs a different corner          0.7265

Fingerprint similarity separates *corners* (0.73 vs 0.99, a wide gap)
but barely separates a deteriorated lap from a clean one at the same
corner (0.008 apart). That is not a defect -- `telemetry_fingerprint`
normalizes by distance and standardizes channels precisely so that shape
comparison ignores magnitude. Magnitude is `baseline`'s job.

So `telemetry_similarity` is used here as a **comparability check** --
confirmation that two windows describe the same stretch of track and can
meaningfully be compared -- and never as evidence that the car is
misbehaving. The claim that something changed rests entirely on the
own-baseline deviation, which is magnitude-sensitive and calibrated
against the driver's own spread.

Workstream D must not label `telemetry_similarity` as severity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Comparability threshold, from the distribution above: same-corner pairs
# sit at 0.99+, different-corner pairs at ~0.73. 0.90 separates them with
# a wide margin on both sides and is deliberately NOT tuned to the narrow
# clean/deteriorated gap, which this metric cannot resolve.
RECURRENCE_TELEMETRY_THRESHOLD = 0.90

# Phrases in which a driver states this has happened before. A plain,
# inspectable keyword list, not a model: a judge can read it in ten
# seconds and see exactly what triggers CONFIRMED_BY_RADIO. Matching is
# case-insensitive and word-bounded.
REPEAT_PHRASES: tuple[str, ...] = (
    r"\bsame (thing|issue|problem)\b",
    r"\bsame as (before|last time|earlier|it was)\b",
    r"\bagain\b",
    r"\bstill\b",
    r"\blike (before|last time|earlier)\b",
    r"\bkeeps? (happening|doing|going)\b",
    r"\bevery (lap|time)\b",
    r"\bonce more\b",
)

# "Say again" and "come again" are standard radio idiom for "repeat your
# transmission" and say nothing about the car. They are extremely common
# in real team radio, so they are removed before the repeat patterns run.
RADIO_IDIOM_EXCLUSIONS: tuple[str, ...] = (
    r"\bsay again\b",
    r"\bcome again\b",
    r"\brepeat that\b",
)

_VALID_STATES = ("NONE", "POSSIBLE_RECURRENCE", "CONFIRMED_BY_RADIO")


@dataclass(frozen=True)
class RecurrenceAssessment:
    """A recurrence state and the evidence that produced it."""

    state: str
    reason: str
    matched_incident_id: str | None
    radio_repeat_language: bool
    telemetry_comparable: bool


def mentions_repeat(transcript: str) -> bool:
    """Does the driver's own wording say this has happened before?

    Deliberately literal. This detects that the driver *said* something,
    it does not infer intent, mood, or truthfulness. Known limitation:
    "again" in an unrelated clause ("can we try that again") will match.
    Radio-comms idiom is excluded first because "say again" is ubiquitous
    in real team radio and means the opposite of a repeat complaint.
    """
    if not transcript:
        return False

    cleaned = transcript.lower()
    for idiom in RADIO_IDIOM_EXCLUSIONS:
        cleaned = re.sub(idiom, " ", cleaned)

    return any(re.search(pattern, cleaned) for pattern in REPEAT_PHRASES)


def assess_recurrence(
    *,
    transcript: str,
    baseline_status: str,
    echo_incident_id: str | None = None,
    telemetry_similarity: float | None = None,
    same_segment: bool = False,
    has_prior_same_category: bool = False,
    telemetry_threshold: float = RECURRENCE_TELEMETRY_THRESHOLD,
) -> RecurrenceAssessment:
    """Decide the recurrence state from evidence already gathered.

    `CONFIRMED_BY_RADIO` -- the driver's own words say this has happened
    before, AND a prior incident of the same reported phenomenon is on
    record for the "again" to refer to. Both halves are required: without
    the driver's wording this would be our inference dressed up as their
    statement, and without a stored prior there is nothing to point at
    when a judge asks "a recurrence of what?".

    `POSSIBLE_RECURRENCE` -- a retrieved prior report at the same segment,
    telemetry comparable enough to be talking about the same stretch of
    track, and the car currently deviating from the driver's own baseline.
    The deviation is what carries the claim.

    `NONE` -- anything else. The common and unremarkable answer.
    """
    repeat_language = mentions_repeat(transcript)
    comparable = (
        telemetry_similarity is not None and telemetry_similarity >= telemetry_threshold
    )

    if repeat_language and has_prior_same_category:
        return RecurrenceAssessment(
            state="CONFIRMED_BY_RADIO",
            reason=(
                "the driver's message refers to a repeat and a prior report of "
                "the same phenomenon is on record"
            ),
            matched_incident_id=echo_incident_id,
            radio_repeat_language=True,
            telemetry_comparable=comparable,
        )

    if (
        echo_incident_id is not None
        and same_segment
        and comparable
        and baseline_status == "BEHAVIOR_CONSISTENT"
    ):
        return RecurrenceAssessment(
            state="POSSIBLE_RECURRENCE",
            reason=(
                f"a prior report at this segment ({echo_incident_id}) was "
                f"retrieved, the telemetry windows are comparable "
                f"({telemetry_similarity:.3f}), and the car is currently "
                f"deviating from this driver's own baseline"
            ),
            matched_incident_id=echo_incident_id,
            radio_repeat_language=repeat_language,
            telemetry_comparable=True,
        )

    return RecurrenceAssessment(
        state="NONE",
        reason=_explain_none(
            echo_incident_id=echo_incident_id,
            same_segment=same_segment,
            comparable=comparable,
            baseline_status=baseline_status,
            repeat_language=repeat_language,
            has_prior_same_category=has_prior_same_category,
        ),
        matched_incident_id=echo_incident_id,
        radio_repeat_language=repeat_language,
        telemetry_comparable=comparable,
    )


def _explain_none(
    *,
    echo_incident_id: str | None,
    same_segment: bool,
    comparable: bool,
    baseline_status: str,
    repeat_language: bool,
    has_prior_same_category: bool,
) -> str:
    """State the specific reason nothing was flagged, for the audit trail."""
    if repeat_language and not has_prior_same_category:
        return (
            "the driver's message refers to a repeat, but no prior report of "
            "this phenomenon is on record to attribute it to"
        )
    if echo_incident_id is None:
        return "no prior incident was retrieved"
    if not same_segment:
        return f"the retrieved prior report ({echo_incident_id}) is at a different segment"
    if not comparable:
        return (
            f"the telemetry window is not comparable enough to the prior report "
            f"({echo_incident_id}) to judge a recurrence"
        )
    if baseline_status == "INSUFFICIENT_DATA":
        return "not enough baseline laps to say whether the car is deviating"
    return "the car is not currently deviating from this driver's own baseline"
