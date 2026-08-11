"""Exercises the real sentence-transformers model.

Separated from the fast retrieval tests because it needs the MiniLM
weights. Skips cleanly when they cannot be loaded (no network, no cache)
so the suite still passes on an offline machine -- but it is the test
that proves the documented retrieval threshold is calibrated against the
actual model rather than against a stand-in.
"""

from __future__ import annotations

import pytest

import app  # noqa: F401  -- puts services/ on sys.path
from evidence_memory import embeddings
from evidence_memory.retrieval import SEMANTIC_SIMILARITY_THRESHOLD


@pytest.fixture(scope="module")
def encoded():
    """Encode the probe phrases once, or skip the module."""
    try:
        vectors = embeddings.encode(list(PHRASES))
    except Exception as exc:  # noqa: BLE001 -- offline, no cache, any load failure
        pytest.skip(f"sentence-transformers model unavailable: {exc}")
    return dict(zip(PHRASES, vectors))


PHRASES = (
    "Rear is moving on throttle.",
    "The rear stepped out again on corner exit.",
    "Same thing again, rear is loose out of seven.",
    "Rear end is snapping on power.",
    "No front end on turn-in, I have understeer.",
    "The front is washing out under braking.",
    "Box this lap, box box.",
)


def test_model_name_defaults_to_the_documented_model(monkeypatch):
    monkeypatch.delenv("HF_EMBEDDING_MODEL", raising=False)
    assert embeddings.default_model_name() == "sentence-transformers/all-MiniLM-L6-v2"


def test_model_name_is_overridable(monkeypatch):
    monkeypatch.setenv("HF_EMBEDDING_MODEL", "some/other-model")
    assert embeddings.default_model_name() == "some/other-model"


def test_embeddings_are_normalized(encoded):
    import numpy as np

    for vector in encoded.values():
        assert float(np.linalg.norm(vector)) == pytest.approx(1.0, abs=1e-5)


def test_restated_complaint_clears_the_threshold(encoded):
    """The demo case: a driver reporting the same thing again must retrieve.

    Calibration guard. If this starts failing, the threshold in
    retrieval.py no longer matches the model's behaviour and must be
    re-measured -- do not just move the assertion.
    """
    for restatement in (
        "Same thing again, rear is loose out of seven.",
        "Rear end is snapping on power.",
        "The rear stepped out again on corner exit.",
    ):
        similarity = embeddings.cosine_similarity(
            encoded["Rear is moving on throttle."], encoded[restatement]
        )
        assert similarity >= SEMANTIC_SIMILARITY_THRESHOLD, (
            f"restated rear-instability complaint {restatement!r} scored "
            f"{similarity:.3f}, below the {SEMANTIC_SIMILARITY_THRESHOLD} threshold"
        )


def test_non_complaint_radio_stays_below_the_threshold(encoded):
    similarity = embeddings.cosine_similarity(
        encoded["Rear is moving on throttle."], encoded["Box this lap, box box."]
    )
    assert similarity < SEMANTIC_SIMILARITY_THRESHOLD


def test_cosine_alone_cannot_separate_complaint_categories(encoded):
    """Documents WHY the category gate exists, and fails if that stops being true.

    A different complaint ("front is washing out") scores higher against
    the rear complaint than a genuine restatement of it does. This is the
    measured fact that makes a cosine-only threshold indefensible and
    forces the same-category gate in retrieval.best_match. If this ever
    inverts, the gate can be reconsidered -- but not before.
    """
    reference = encoded["Rear is moving on throttle."]
    cross_category = embeddings.cosine_similarity(
        reference, encoded["The front is washing out under braking."]
    )
    genuine_repeat = embeddings.cosine_similarity(
        reference, encoded["The rear stepped out again on corner exit."]
    )
    assert cross_category > genuine_repeat, (
        "cosine now separates these categories correctly "
        f"(cross={cross_category:.3f} < repeat={genuine_repeat:.3f}); "
        "revisit the same-category gate and this test's rationale"
    )


def test_cosine_of_a_phrase_with_itself_is_one(encoded):
    vector = encoded["Rear is moving on throttle."]
    assert embeddings.cosine_similarity(vector, vector) == pytest.approx(1.0, abs=1e-6)


def test_cosine_clamps_negatives_to_zero():
    import numpy as np

    assert embeddings.cosine_similarity(np.array([1.0, 0.0]), np.array([-1.0, 0.0])) == 0.0


def test_cosine_handles_a_zero_vector():
    import numpy as np

    assert embeddings.cosine_similarity(np.array([0.0, 0.0]), np.array([1.0, 0.0])) == 0.0
