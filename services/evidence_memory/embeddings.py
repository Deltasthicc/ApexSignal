"""Sentence embeddings for ECHO LAP incident memory.

Model: ``sentence-transformers/all-MiniLM-L6-v2`` (README.md tech stack),
overridable via ``HF_EMBEDDING_MODEL``.

The model is imported and loaded lazily inside the functions that need
it, per CONTRIBUTING.md, so importing this module -- or anything that
imports it -- costs nothing and works on a machine with no model cache.
Tests inject their own encoder rather than downloading weights.
"""

from __future__ import annotations

import hashlib
import os
import re
from functools import lru_cache
from typing import TYPE_CHECKING, Callable, Sequence

if TYPE_CHECKING:
    import numpy as np

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FALLBACK_DIMENSIONS = 384

_DOMAIN_NORMALIZATION = {
    "loose": "rear_traction",
    "moving": "rear_traction",
    "snapping": "rear_traction",
    "stepped": "rear_traction",
    "rear": "rear_traction",
    "power": "throttle",
    "traction": "throttle",
    "understeer": "front_turnin",
    "washing": "front_turnin",
    "turning": "front_turnin",
    "front": "front_turnin",
    "brakes": "brake",
    "braking": "brake",
    "tyres": "tyre",
    "tires": "tyre",
    "again": "recurrence",
    "same": "recurrence",
}

# Takes a list of texts, returns one row per text. Anything matching this
# can stand in for the real model.
Encoder = Callable[[Sequence[str]], "np.ndarray"]


def default_model_name() -> str:
    return os.environ.get("HF_EMBEDDING_MODEL") or DEFAULT_MODEL_NAME


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    """Load and cache a SentenceTransformer. Heavy; called on first use only."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def encode(texts: Sequence[str], *, model_name: str | None = None) -> "np.ndarray":
    """Embed texts and L2-normalize each row.

    Normalizing here means cosine similarity downstream is a plain dot
    product, and no caller has to remember to normalize.
    """
    import numpy as np

    if not texts:
        return np.zeros((0, 0), dtype=float)

    model = _load_model(model_name or default_model_name())
    vectors = model.encode(list(texts), convert_to_numpy=True)
    return normalize_rows(np.asarray(vectors, dtype=float))


def encode_resilient(
    texts: Sequence[str], *, model_name: str | None = None
) -> "np.ndarray":
    """Use MiniLM when installed, otherwise keep the pipeline operational."""
    try:
        return encode(texts, model_name=model_name)
    except ImportError:
        return _lexical_encode(texts)


def _lexical_encode(texts: Sequence[str]) -> "np.ndarray":
    """Deterministic CPU fallback when sentence-transformers is unavailable.

    The fallback is deliberately modest: normalized word features, adjacent
    token pairs, and a small F1 vocabulary map. It keeps the evidence pipeline
    operational and testable without pretending to be the MiniLM model. The
    production model remains the preferred path whenever it is installed.
    """
    import numpy as np

    matrix = np.zeros((len(texts), FALLBACK_DIMENSIONS), dtype=float)
    for row, text in enumerate(texts):
        raw_tokens = re.findall(r"[a-z0-9]+", text.lower())
        tokens = [_DOMAIN_NORMALIZATION.get(token, token) for token in raw_tokens]
        features = tokens + [
            f"{left}:{right}" for left, right in zip(tokens, tokens[1:])
        ]
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "little") % FALLBACK_DIMENSIONS
            matrix[row, index] += 1.0
    return normalize_rows(matrix)


def normalize_rows(matrix: "np.ndarray") -> "np.ndarray":
    """L2-normalize each row; all-zero rows are left as zeros."""
    import numpy as np

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def cosine_similarity(left: "np.ndarray", right: "np.ndarray") -> float:
    """Cosine similarity of two vectors, clamped to the contract's 0-1 range.

    Raw cosine runs from -1 to 1. The contract requires
    ``semantic_similarity`` in [0, 1], so negatives clamp to 0.0. That
    loses nothing in practice: a negative cosine between two short radio
    transcripts is far below any retrieval threshold, and the distinction
    between "unrelated" and "anti-correlated" carries no meaning for this
    corpus.
    """
    import numpy as np

    a = np.asarray(left, dtype=float)
    b = np.asarray(right, dtype=float)
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0.0:
        return 0.0
    return max(0.0, min(1.0, float(np.dot(a, b) / denominator)))
