"""Recurrence-state tests (MVP synchronous version of charter Flow B)."""

from __future__ import annotations

import pytest

import app  # noqa: F401  -- puts services/ on sys.path
from evidence_memory.recurrence import (
    RECURRENCE_TELEMETRY_THRESHOLD,
    assess_recurrence,
    mentions_repeat,
)


# --- repeat-language detection ------------------------------------------


@pytest.mark.parametrize(
    "transcript",
    [
        "Same thing again, rear is loose.",
        "It's doing the same thing as before.",
        "Rear stepped out again on exit.",
        "I've still got no rear grip.",
        "It's like last time, no traction.",
        "This keeps happening every lap.",
        "The rear is going away every lap now.",
    ],
)
def test_repeat_language_is_detected(transcript):
    assert mentions_repeat(transcript) is True


@pytest.mark.parametrize(
    "transcript",
    [
        "Rear is moving on throttle.",
        "No front end into turn one.",
        "Box this lap.",
        "",
    ],
)
def test_first_time_complaints_are_not_repeats(transcript):
    assert mentions_repeat(transcript) is False


@pytest.mark.parametrize(
    "transcript",
    [
        "Say again, I didn't catch that.",
        "Come again?",
        "Can you repeat that please.",
    ],
)
def test_radio_comms_idiom_is_not_a_repeat_complaint(transcript):
    """'Say again' is ubiquitous in real team radio and means the opposite."""
    assert mentions_repeat(transcript) is False


def test_idiom_exclusion_does_not_swallow_a_real_repeat():
    assert mentions_repeat("Say again -- the rear is loose again.") is True


# --- state resolution ----------------------------------------------------


def test_confirmed_by_radio_needs_both_wording_and_a_prior_report():
    result = assess_recurrence(
        transcript="Same thing again, rear is loose out of seven.",
        baseline_status="BEHAVIOR_CONSISTENT",
        echo_incident_id="INC-017",
        telemetry_similarity=0.99,
        same_segment=True,
        has_prior_same_category=True,
    )
    assert result.state == "CONFIRMED_BY_RADIO"
    assert result.radio_repeat_language is True


def test_repeat_wording_without_a_prior_report_is_not_confirmed():
    """Nothing to point at when a judge asks 'a recurrence of what?'."""
    result = assess_recurrence(
        transcript="Same thing again, rear is loose.",
        baseline_status="BEHAVIOR_CONSISTENT",
        echo_incident_id=None,
        telemetry_similarity=None,
        same_segment=False,
        has_prior_same_category=False,
    )
    assert result.state == "NONE"
    assert "no prior report of this phenomenon is on record" in result.reason
    # The observation is preserved even though it did not change the state.
    assert result.radio_repeat_language is True


def test_confirmed_by_radio_outranks_possible_recurrence():
    """The driver's own statement is the stronger signal."""
    result = assess_recurrence(
        transcript="It's the same problem again.",
        baseline_status="NO_DEVIATION",
        echo_incident_id="INC-017",
        telemetry_similarity=0.99,
        same_segment=True,
        has_prior_same_category=True,
    )
    assert result.state == "CONFIRMED_BY_RADIO"


def test_possible_recurrence_when_prior_report_and_current_deviation():
    result = assess_recurrence(
        transcript="Rear is moving on throttle.",
        baseline_status="BEHAVIOR_CONSISTENT",
        echo_incident_id="INC-017",
        telemetry_similarity=0.99,
        same_segment=True,
        has_prior_same_category=True,
    )
    assert result.state == "POSSIBLE_RECURRENCE"
    assert result.matched_incident_id == "INC-017"


def test_no_recurrence_without_a_current_deviation():
    """A retrieved match alone is not a recurrence."""
    result = assess_recurrence(
        transcript="Rear is moving on throttle.",
        baseline_status="NO_DEVIATION",
        echo_incident_id="INC-017",
        telemetry_similarity=0.99,
        same_segment=True,
        has_prior_same_category=True,
    )
    assert result.state == "NONE"
    assert "not currently deviating" in result.reason


def test_no_recurrence_when_baseline_is_unknown():
    result = assess_recurrence(
        transcript="Rear is moving on throttle.",
        baseline_status="INSUFFICIENT_DATA",
        echo_incident_id="INC-017",
        telemetry_similarity=0.99,
        same_segment=True,
        has_prior_same_category=True,
    )
    assert result.state == "NONE"
    assert "not enough baseline laps" in result.reason


def test_no_recurrence_across_different_segments():
    result = assess_recurrence(
        transcript="Rear is moving on throttle.",
        baseline_status="BEHAVIOR_CONSISTENT",
        echo_incident_id="INC-017",
        telemetry_similarity=0.99,
        same_segment=False,
        has_prior_same_category=True,
    )
    assert result.state == "NONE"
    assert "different segment" in result.reason


def test_no_recurrence_when_telemetry_is_not_comparable():
    """Below the comparability threshold the windows describe different track."""
    result = assess_recurrence(
        transcript="Rear is moving on throttle.",
        baseline_status="BEHAVIOR_CONSISTENT",
        echo_incident_id="INC-017",
        telemetry_similarity=0.72,  # measured value for a different corner
        same_segment=True,
        has_prior_same_category=True,
    )
    assert result.state == "NONE"
    assert "not comparable enough" in result.reason


def test_no_recurrence_without_any_retrieved_match():
    result = assess_recurrence(
        transcript="Rear is moving on throttle.",
        baseline_status="BEHAVIOR_CONSISTENT",
        echo_incident_id=None,
        telemetry_similarity=None,
        same_segment=False,
        has_prior_same_category=False,
    )
    assert result.state == "NONE"
    assert result.reason == "no prior incident was retrieved"


def test_telemetry_threshold_sits_between_the_measured_populations():
    """0.90 separates same-corner (~0.99) from different-corner (~0.73)."""
    assert 0.73 < RECURRENCE_TELEMETRY_THRESHOLD < 0.99


def test_deteriorated_and_clean_laps_are_not_separable_by_this_threshold():
    """Documents why the deviation, not similarity, carries the claim.

    A deteriorated lap scores 0.992 against a clean one -- above the
    comparability threshold, as intended. If this metric were being used
    as evidence of deterioration, that would be a false positive.
    """
    for similarity in (0.9920, 1.0000):
        deviating = assess_recurrence(
            transcript="Rear is moving.",
            baseline_status="BEHAVIOR_CONSISTENT",
            echo_incident_id="INC-017",
            telemetry_similarity=similarity,
            same_segment=True,
            has_prior_same_category=True,
        )
        steady = assess_recurrence(
            transcript="Rear is moving.",
            baseline_status="NO_DEVIATION",
            echo_incident_id="INC-017",
            telemetry_similarity=similarity,
            same_segment=True,
            has_prior_same_category=True,
        )
        # Same similarity, opposite outcomes: the baseline decides.
        assert deviating.state == "POSSIBLE_RECURRENCE"
        assert steady.state == "NONE"


def test_state_is_always_one_of_the_three_contract_values():
    allowed = {"NONE", "POSSIBLE_RECURRENCE", "CONFIRMED_BY_RADIO"}
    for transcript in ("Rear is moving.", "Same thing again."):
        for status in ("BEHAVIOR_CONSISTENT", "NO_DEVIATION", "INSUFFICIENT_DATA"):
            for echo in (None, "INC-017"):
                for similarity in (None, 0.5, 0.99):
                    for segment in (True, False):
                        for prior in (True, False):
                            result = assess_recurrence(
                                transcript=transcript,
                                baseline_status=status,
                                echo_incident_id=echo,
                                telemetry_similarity=similarity,
                                same_segment=segment,
                                has_prior_same_category=prior,
                            )
                            assert result.state in allowed
                            assert result.reason


def test_reason_never_claims_a_confirmed_fault():
    """Interpretation-safe register, everywhere."""
    banned = ("fault", "failure", "broken", "diagnos", "lying", "deception")
    for status in ("BEHAVIOR_CONSISTENT", "NO_DEVIATION", "INSUFFICIENT_DATA"):
        for echo in (None, "INC-017"):
            result = assess_recurrence(
                transcript="Same thing again, rear is loose.",
                baseline_status=status,
                echo_incident_id=echo,
                telemetry_similarity=0.99,
                same_segment=True,
                has_prior_same_category=echo is not None,
            )
            lowered = result.reason.lower()
            assert not any(word in lowered for word in banned)
