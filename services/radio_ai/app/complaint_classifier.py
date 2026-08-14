"""Complaint classification stage: zero-shot NLI over the fixed 5-category
taxonomy plus a NO_COMPLAINT rejection class, via
MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33.

Chosen over embedding-prototype classification because the taxonomy
definition itself becomes the classifier input -- there's no prototype
set, aggregation rule, or cosine threshold to hand-tune for five nuanced
classes. See VALIDATION_GATES.md gate 6 for the acceptance benchmark.
"""

from __future__ import annotations

from app.config import ClassifierConfig, ModelConfig

_classifier = None
_active_model_id = None


def _load_classifier():
    global _classifier, _active_model_id
    if _classifier is not None:
        return _classifier

    from transformers import pipeline

    if ModelConfig.USE_CLASSIFIER_FALLBACK:
        model_id = ModelConfig.CLASSIFIER_FALLBACK_MODEL_ID
        revision = ModelConfig.CLASSIFIER_FALLBACK_MODEL_REVISION
    else:
        model_id = ModelConfig.CLASSIFIER_MODEL_ID
        revision = ModelConfig.CLASSIFIER_MODEL_REVISION

    _classifier = pipeline(
        "zero-shot-classification", model=model_id, revision=revision
    )
    _active_model_id = model_id
    return _classifier


def warm_up() -> None:
    _load_classifier()


def classify(transcript: str) -> tuple[str | None, float | None]:
    """Transcript -> (complaint_category or None, category_confidence or None).

    Returns (None, None) for NO_COMPLAINT so the JSON contract's
    `complaint_category: null` is exact, not a stand-in string.
    """
    if not transcript.strip():
        return None, None

    classifier = _load_classifier()
    labels = list(ClassifierConfig.TAXONOMY.keys())
    hypotheses = [ClassifierConfig.TAXONOMY[label] for label in labels]

    result = classifier(
        transcript,
        hypotheses,
        hypothesis_template=ClassifierConfig.HYPOTHESIS_TEMPLATE,
        multi_label=True,
    )
    # result["labels"]/["scores"] come back keyed by the long descriptive
    # hypothesis text we passed in (that's what candidate_labels was),
    # re-sorted by score -- NOT by our short taxonomy keys. Map back to
    # short keys via the hypothesis text, not by assuming the pipeline
    # echoes our keys directly (it doesn't -- this was silently always
    # returning None/None before, since every scored.get(short_key, 0.0)
    # lookup below missed and fell back to 0.0. See VALIDATION_GATES.md
    # gate 6/7 for how this was found.)
    hypothesis_to_label = dict(zip(hypotheses, labels))
    scored = {
        hypothesis_to_label[hyp]: score
        for hyp, score in zip(result["labels"], result["scores"])
    }

    if scored.get("NO_COMPLAINT", 0.0) >= ClassifierConfig.NULL_THRESHOLD:
        top_non_null = max(
            (label for label in scored if label != "NO_COMPLAINT"),
            key=lambda label: scored[label],
            default=None,
        )
        if top_non_null is None or scored["NO_COMPLAINT"] >= scored[top_non_null]:
            return None, None

    for label in ClassifierConfig.PRECEDENCE_ORDER:
        if scored.get(label, 0.0) >= ClassifierConfig.NULL_THRESHOLD:
            return label, float(scored[label])

    return None, None
