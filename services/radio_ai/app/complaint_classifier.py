"""Complaint classification stage: transcript -> one of the fixed
5-category taxonomy, or None for NO_COMPLAINT.

Backend selectable via ModelConfig.CLASSIFIER_BACKEND (embedding /
nli-base / nli-xsmall). Default is "embedding" as of 2026-08-14 (see
VALIDATION_GATES.md gate 6d, GATE6_ERROR_ANALYSIS.md "Attempt 4"):
sentence-embedding + prototype cosine similarity measurably beat every
zero-shot-NLI variant tried (macro-F1 0.454 vs nli-xsmall's 0.393 on
the 58-example Gate 6 benchmark). NLI stays selectable in case a later
experiment makes it competitive again.
"""

from __future__ import annotations

from app.config import ClassifierConfig, ModelConfig

# NLI backend state
_nli_classifier = None
_active_model_id = None

# Embedding backend state
_embedding_model = None
_prototype_labels: list[str] | None = None
_prototype_embeddings = None


def _load_nli_classifier():
    global _nli_classifier, _active_model_id
    if _nli_classifier is not None:
        return _nli_classifier

    from transformers import pipeline

    if ModelConfig.CLASSIFIER_BACKEND == "nli-xsmall":
        model_id = ModelConfig.CLASSIFIER_FALLBACK_MODEL_ID
        revision = ModelConfig.CLASSIFIER_FALLBACK_MODEL_REVISION
    else:
        model_id = ModelConfig.CLASSIFIER_MODEL_ID
        revision = ModelConfig.CLASSIFIER_MODEL_REVISION

    _nli_classifier = pipeline(
        "zero-shot-classification", model=model_id, revision=revision
    )
    _active_model_id = model_id
    return _nli_classifier


def _load_embedding_model():
    global _embedding_model, _prototype_labels, _prototype_embeddings, _active_model_id
    if _embedding_model is not None:
        return _embedding_model

    from sentence_transformers import SentenceTransformer

    _embedding_model = SentenceTransformer(
        ModelConfig.EMBEDDING_MODEL_ID, revision=ModelConfig.EMBEDDING_MODEL_REVISION
    )
    _active_model_id = ModelConfig.EMBEDDING_MODEL_ID

    # Prototype per category = its existing TAXONOMY description text,
    # same text the NLI backend uses as its hypothesis -- ported
    # directly from scripts/experiment_embedding_classifier.py, not
    # re-derived, so this is the exact logic that measured macro-F1
    # 0.454 (see VALIDATION_GATES.md gate 6d).
    _prototype_labels = list(ClassifierConfig.TAXONOMY.keys())
    prototype_texts = [ClassifierConfig.TAXONOMY[label] for label in _prototype_labels]
    _prototype_embeddings = _embedding_model.encode(prototype_texts, convert_to_tensor=True)
    return _embedding_model


def warm_up() -> None:
    if ModelConfig.CLASSIFIER_BACKEND == "embedding":
        _load_embedding_model()
    else:
        _load_nli_classifier()


def _classify_nli(transcript: str) -> tuple[str | None, float | None]:
    classifier = _load_nli_classifier()
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


def _classify_embedding(transcript: str) -> tuple[str | None, float | None]:
    from sentence_transformers import util

    model = _load_embedding_model()
    transcript_embedding = model.encode([transcript], convert_to_tensor=True)
    similarity = util.cos_sim(transcript_embedding, _prototype_embeddings)[0]

    real_categories = [l for l in _prototype_labels if l != "NO_COMPLAINT"]
    real_scores = {
        label: float(similarity[_prototype_labels.index(label)]) for label in real_categories
    }
    best_real_label = max(real_scores, key=lambda l: real_scores[l])
    best_real_score = real_scores[best_real_label]
    no_complaint_score = float(similarity[_prototype_labels.index("NO_COMPLAINT")])

    if best_real_score > no_complaint_score + ClassifierConfig.EMBEDDING_SIMILARITY_MARGIN:
        # Cosine similarity isn't guaranteed to land in [0,1] for every
        # possible input the way an NLI entailment score is -- clamp
        # for contract safety (RadioAnalysisOutput.category_confidence
        # requires 0<=x<=1), same reasoning app/tone.py already clamps
        # its own scores for.
        return best_real_label, float(max(0.0, min(1.0, best_real_score)))

    return None, None


def classify(transcript: str) -> tuple[str | None, float | None]:
    """Transcript -> (complaint_category or None, category_confidence or None).

    Returns (None, None) for NO_COMPLAINT so the JSON contract's
    `complaint_category: null` is exact, not a stand-in string.
    Backend chosen by ModelConfig.CLASSIFIER_BACKEND; the public
    interface here does not change regardless of which backend is
    active -- core_api and the contract downstream don't know or care.
    """
    if not transcript.strip():
        return None, None

    if ModelConfig.CLASSIFIER_BACKEND == "embedding":
        return _classify_embedding(transcript)
    return _classify_nli(transcript)
