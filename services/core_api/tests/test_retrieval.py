"""ECHO LAP retrieval tests.

Most tests inject a deterministic fake encoder so they run in
milliseconds with no model download. The real MiniLM model is exercised
separately in `test_embeddings_real_model.py`, which skips when the
weights are not available offline.
"""

from __future__ import annotations

import numpy as np
import pytest

import app  # noqa: F401  -- puts services/ on sys.path
from evidence_memory import synthetic
from evidence_memory.retrieval import (
    SEMANTIC_SIMILARITY_THRESHOLD,
    Candidate,
    IncidentMemory,
    MemoryEntry,
    classify_match,
)
from evidence_memory.telemetry_fingerprint import build_fingerprint, select_segment

# A tiny keyword-space encoder: deterministic, offline, and similar enough
# in behaviour (unit vectors, cosine in [0, 1]) to stand in for MiniLM.
# Text matching no keyword lands on its own dimension, so it scores 0
# against everything rather than correlating with all of it.
_VOCAB = ("rear", "front", "throttle", "brake", "grip", "visibility")


def fake_encoder(texts):
    rows = []
    for text in texts:
        lowered = text.lower()
        row = np.array([float(word in lowered) for word in _VOCAB] + [0.0])
        if not row.any():
            row[-1] = 1.0
        rows.append(row / np.linalg.norm(row))
    return np.vstack(rows)


@pytest.fixture()
def window():
    return synthetic.synthetic_window(laps=[14, 15, 16, 17, 18, 19])


@pytest.fixture()
def fingerprints(window):
    return {lap: build_fingerprint(select_segment(window, lap=lap)) for lap in
            (14, 15, 16, 17, 18, 19)}


def entry(
    incident_id: str,
    transcript: str,
    *,
    segment: str = "T7_EXIT",
    category: str = "EXIT_TRACTION_REAR",
    event_time_ms: int = 1_000,
    fingerprint=None,
) -> MemoryEntry:
    return MemoryEntry(
        incident_id=incident_id,
        transcript=transcript,
        segment=segment,
        complaint_category=category,
        event_time_ms=event_time_ms,
        fingerprint=fingerprint,
    )


@pytest.fixture()
def memory(fingerprints):
    store = IncidentMemory(encoder=fake_encoder)
    store.add_many(
        [
            entry(
                "INC-017",
                "Rear is moving on throttle.",
                event_time_ms=1_000,
                fingerprint=fingerprints[15],
            ),
            entry(
                "INC-020",
                "No front end on brake into the hairpin.",
                category="FRONT_TURNIN_BRAKE",
                segment="T4_ENTRY",
                event_time_ms=2_000,
                fingerprint=fingerprints[16],
            ),
            entry(
                "INC-024",
                "Visibility is bad in the spray.",
                category="VISIBILITY_TRACK_CONDITION",
                segment="T1_ENTRY",
                event_time_ms=3_000,
                fingerprint=fingerprints[14],
            ),
        ]
    )
    return store


def test_entries_are_embedded_on_add(memory):
    assert len(memory) == 3
    for stored in memory.entries:
        assert stored.embedding is not None
        assert float(np.linalg.norm(stored.embedding)) == pytest.approx(1.0)


def test_add_many_batches_encoder_calls(fingerprints):
    calls: list[int] = []

    def counting_encoder(texts):
        calls.append(len(texts))
        return fake_encoder(texts)

    store = IncidentMemory(encoder=counting_encoder)
    store.add_many([entry(f"INC-{i}", "Rear is moving") for i in range(5)])
    assert calls == [5]


def test_best_match_finds_the_semantically_closest_prior_incident(
    memory, fingerprints
):
    result = memory.best_match(
        "Rear stepped out again on throttle.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="EXIT_TRACTION_REAR",
        before_event_time_ms=9_000,
    )
    assert result.match is not None
    assert result.match.incident_id == "INC-017"
    assert result.match.same_segment is True
    assert result.reason == "match found"


def test_semantic_and_telemetry_similarity_are_separate_numbers(
    memory, fingerprints
):
    """The two scores are never blended; both are independently present."""
    result = memory.best_match(
        "Rear is moving on throttle again.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="EXIT_TRACTION_REAR",
    )
    assert result.match is not None
    semantic = result.match.semantic_similarity
    telemetry = result.match.telemetry_similarity
    assert 0.0 <= semantic <= 1.0
    assert telemetry is not None and 0.0 <= telemetry <= 1.0
    # Two genuinely independent measurements, not one number echoed twice.
    assert semantic != pytest.approx(telemetry)


def test_no_match_below_threshold_returns_none_not_a_guess(memory, fingerprints):
    """Contract cut rule: below threshold is null, never a weak guess."""
    result = memory.best_match(
        "Box this lap for a set of softs please.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="EXIT_TRACTION_REAR",
    )
    assert result.match is None
    assert "threshold" in result.reason
    # The near-misses are still available for debugging, just not reported.
    assert result.candidates
    assert all(
        c.semantic_similarity < SEMANTIC_SIMILARITY_THRESHOLD
        for c in result.candidates
        if c.same_category
    )


def test_no_match_when_no_stored_incident_shares_the_category(memory, fingerprints):
    """Cosine alone is not allowed to bridge two different complaints."""
    result = memory.best_match(
        "The tyres are completely gone, no grip.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="TYRE_GRIP_DEGRADATION",
    )
    assert result.match is None
    assert "shares the reported category" in result.reason


def test_retrieval_refuses_to_fall_back_to_wording_alone(memory, fingerprints):
    """Without a category from Workstream B, retrieval declines rather than guesses."""
    result = memory.best_match(
        "Rear is moving on throttle.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category=None,
    )
    assert result.match is None
    assert "no complaint category" in result.reason


def test_category_gate_can_be_disabled_explicitly(memory, fingerprints):
    """The gate is a default, not a hard-coded rule -- but opting out is explicit."""
    result = memory.best_match(
        "Rear is moving on throttle.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category=None,
        require_same_category=False,
    )
    assert result.match is not None
    assert result.match.incident_id == "INC-017"


def test_empty_memory_returns_none_with_a_reason(fingerprints):
    store = IncidentMemory(encoder=fake_encoder)
    result = store.best_match(
        "Rear is moving",
        query_fingerprint=fingerprints[19],
        query_category="EXIT_TRACTION_REAR",
    )
    assert result.match is None
    assert result.reason == "no prior incidents in memory to compare"


def test_retrieval_never_matches_a_future_incident(fingerprints):
    store = IncidentMemory(encoder=fake_encoder)
    store.add_many(
        [
            entry("INC-EARLY", "Rear is moving on throttle.", event_time_ms=1_000,
                  fingerprint=fingerprints[15]),
            entry("INC-LATER", "Rear is moving on throttle.", event_time_ms=8_000,
                  fingerprint=fingerprints[16]),
        ]
    )
    result = store.best_match(
        "Rear is moving on throttle.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="EXIT_TRACTION_REAR",
        before_event_time_ms=5_000,
    )
    assert result.match is not None
    assert result.match.incident_id == "INC-EARLY"


def test_incident_never_matches_itself(fingerprints):
    store = IncidentMemory(encoder=fake_encoder)
    store.add(entry("INC-017", "Rear is moving on throttle.",
                    fingerprint=fingerprints[15]))
    result = store.best_match(
        "Rear is moving on throttle.",
        query_fingerprint=fingerprints[19],
        query_category="EXIT_TRACTION_REAR",
        exclude_incident_id="INC-017",
    )
    assert result.match is None


def test_match_without_telemetry_is_not_reported(fingerprints):
    """No telemetry means no honest telemetry_similarity, so no match."""
    store = IncidentMemory(encoder=fake_encoder)
    store.add(entry("INC-017", "Rear is moving on throttle.", fingerprint=None))

    result = store.best_match(
        "Rear is moving on throttle.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="EXIT_TRACTION_REAR",
    )
    assert result.match is None
    assert "telemetry could not be compared" in result.reason
    assert result.candidates[0].label == "SEMANTIC_ONLY_NO_TELEMETRY"
    assert result.candidates[0].telemetry_similarity is None


def test_search_returns_ranked_top_k(memory, fingerprints):
    candidates = memory.search(
        "Rear is moving on throttle.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        top_k=2,
    )
    assert len(candidates) == 2
    scores = [c.semantic_similarity for c in candidates]
    assert scores == sorted(scores, reverse=True)


def test_same_segment_and_category_are_flags_not_score_adjustments(
    memory, fingerprints
):
    candidates = memory.search(
        "Rear is moving on throttle.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="EXIT_TRACTION_REAR",
        top_k=3,
    )
    by_id = {c.incident_id: c for c in candidates}
    assert by_id["INC-017"].same_segment is True
    assert by_id["INC-017"].same_category is True
    assert by_id["INC-024"].same_segment is False
    assert by_id["INC-024"].same_category is False


def test_threshold_is_configurable_per_store(fingerprints):
    strict = IncidentMemory(encoder=fake_encoder, semantic_threshold=0.99)
    strict.add(entry("INC-017", "Rear is moving on throttle.",
                     fingerprint=fingerprints[15]))
    result = strict.best_match(
        "Rear grip is going away.",
        query_fingerprint=fingerprints[19],
        query_segment="T7_EXIT",
        query_category="EXIT_TRACTION_REAR",
    )
    assert result.match is None
    assert "0.99" in result.reason


@pytest.mark.parametrize(
    "semantic,telemetry,same_segment,expected",
    [
        (0.60, 0.85, True, "STRONG_PROTOTYPE_MATCH"),
        (0.60, 0.85, False, "MODERATE_PROTOTYPE_MATCH"),
        (0.60, 0.30, True, "MODERATE_PROTOTYPE_MATCH"),
        (0.45, 0.45, False, "MODERATE_PROTOTYPE_MATCH"),
        (0.20, 0.20, False, "WEAK_PROTOTYPE_MATCH"),
        (0.60, None, True, "SEMANTIC_ONLY_NO_TELEMETRY"),
    ],
)
def test_match_labels_are_banded_transparently(
    semantic, telemetry, same_segment, expected
):
    assert classify_match(semantic, telemetry, same_segment) == expected


def test_labels_never_imply_a_confirmed_cause():
    """Charter 9.4: prototype similarity, never probability of a shared fault."""
    labels = {
        classify_match(s, t, seg)
        for s in (0.2, 0.45, 0.6, 0.9)
        for t in (None, 0.2, 0.45, 0.9)
        for seg in (True, False)
    }
    banned = ("FAULT", "CONFIRM", "DIAGNOS", "CAUSE", "PROBABILITY")
    for label in labels:
        assert not any(word in label.upper() for word in banned)


def test_candidate_carries_no_composite_score():
    """Guards against a 'risk score' field being added later."""
    fields = set(Candidate.__dataclass_fields__)
    assert "semantic_similarity" in fields
    assert "telemetry_similarity" in fields
    assert not any(
        word in name for name in fields for word in ("risk", "combined", "composite")
    )
