"""ECHO LAP retrieval: find prior incidents resembling the current one.

Simplified for the MVP: cosine similarity over an in-memory list rather
than a FAISS index. With a 15-25 incident corpus a brute-force scan is
microseconds and has no index to build, persist, or keep in sync with
SQLite. FAISS earns its complexity somewhere around 10^5 vectors; we are
four orders of magnitude short. This is an intentional scope decision,
not an unfinished FAISS integration -- see PROGRESS_REPORT.md.

Semantic and telemetry similarity are returned as two separate numbers
and are never blended into one score. They answer different questions:
"did the driver say something like this before" and "did the car do
something like this before". A match can be strong on one and weak on
the other, and that combination is itself the interesting signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from evidence_memory.embeddings import Encoder, cosine_similarity, encode_resilient
from evidence_memory.telemetry_fingerprint import (
    TelemetryFingerprint,
    compare_fingerprints,
)

if TYPE_CHECKING:
    import numpy as np

# --- Retrieval gate ------------------------------------------------------
#
# MEASURED, not assumed. all-MiniLM-L6-v2 was run over 23 realistic F1
# radio phrasings spanning the five taxonomy categories plus
# non-complaint chatter (247 pairs). Cosine distribution:
#
#   same complaint category   median 0.382   p95 0.594   max 0.618
#   different categories      median 0.213   p95 0.438   max 0.683
#
# The distributions overlap, and the overlap is not incidental: the
# cross-category pair "rear is moving on throttle" / "the front is
# washing out under braking" scores 0.429, ABOVE the genuine same-
# category repeat "rear is moving on throttle" / "the rear stepped out
# again on corner exit" at 0.422.
#
# So a cosine threshold alone cannot separate a repeat of a complaint
# from a different complaint, at any cut. Short idiomatic radio gives
# MiniLM too little to work with. The gate is therefore two independent
# conditions, neither derived from the other:
#
#   1. same complaint category -- from Workstream B's classifier, a model
#      trained for exactly this decision, rather than from cosine over a
#      six-word sentence;
#   2. semantic cosine >= SEMANTIC_SIMILARITY_THRESHOLD -- catches the
#      case where the category label is right but the wording describes
#      something unrelated.
#
# With condition 1 doing the precision work, condition 2 is set for
# recall: 0.40 sits above the cross-category median (0.213) and its 75th
# percentile (0.301), while retaining roughly three-quarters of genuine
# same-category repeats.
#
# ASSUMPTION for the team to re-check: this is calibrated on clean
# hand-written phrasings, not on real ASR output, which will be noisier
# and may score lower. Re-run the calibration once Workstream B has real
# transcripts. One number, one place.
SEMANTIC_SIMILARITY_THRESHOLD = 0.40

# Label bands, on the same measured scale. "PROTOTYPE" is deliberate:
# charter section 9.4 requires these be presented as prototype similarity
# scores, never as the probability of a shared mechanical cause.
STRONG_MATCH_SEMANTIC = 0.55  # near the top of the observed same-category range
STRONG_MATCH_TELEMETRY = 0.75


@dataclass(frozen=True)
class MemoryEntry:
    """One incident held in memory, with whatever evidence is available.

    Deliberately not `app.db.IncidentRecord`: `evidence_memory` is a
    library that must not depend on the service that uses it. core_api
    builds these from its own rows.
    """

    incident_id: str
    transcript: str
    segment: str
    complaint_category: str
    event_time_ms: int
    embedding: "np.ndarray | None" = None
    fingerprint: TelemetryFingerprint | None = None


@dataclass(frozen=True)
class Candidate:
    """A scored prior incident. Components stay separate, always."""

    incident_id: str
    semantic_similarity: float
    telemetry_similarity: float | None
    same_segment: bool
    same_category: bool
    label: str


@dataclass(frozen=True)
class RetrievalResult:
    """Outcome of a search, including why it came out empty.

    `reason` exists so the assessment layer can word `human_message`
    accurately -- "nothing similar was stored" and "something similar was
    stored but its telemetry could not be compared" are different facts
    and the UI should not present them identically.
    """

    match: Candidate | None
    candidates: tuple[Candidate, ...]
    reason: str


class IncidentMemory:
    """In-memory ECHO LAP store: transcripts, embeddings, fingerprints."""

    def __init__(
        self,
        *,
        encoder: Encoder | None = None,
        semantic_threshold: float = SEMANTIC_SIMILARITY_THRESHOLD,
    ) -> None:
        self._entries: list[MemoryEntry] = []
        self._encoder = encoder
        self.semantic_threshold = semantic_threshold

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> tuple[MemoryEntry, ...]:
        return tuple(self._entries)

    def add(self, entry: MemoryEntry) -> None:
        """Add one incident, embedding its transcript if not already done."""
        if entry.embedding is None:
            vector = self._encode([entry.transcript])[0]
            entry = MemoryEntry(
                incident_id=entry.incident_id,
                transcript=entry.transcript,
                segment=entry.segment,
                complaint_category=entry.complaint_category,
                event_time_ms=entry.event_time_ms,
                embedding=vector,
                fingerprint=entry.fingerprint,
            )
        self._entries.append(entry)

    def add_many(self, entries: Sequence[MemoryEntry]) -> None:
        """Add several incidents, embedding them in one batch."""
        missing = [i for i, e in enumerate(entries) if e.embedding is None]
        vectors = self._encode([entries[i].transcript for i in missing]) if missing else []
        by_position = dict(zip(missing, vectors))

        for position, entry in enumerate(entries):
            if position in by_position:
                entry = MemoryEntry(
                    incident_id=entry.incident_id,
                    transcript=entry.transcript,
                    segment=entry.segment,
                    complaint_category=entry.complaint_category,
                    event_time_ms=entry.event_time_ms,
                    embedding=by_position[position],
                    fingerprint=entry.fingerprint,
                )
            self._entries.append(entry)

    def search(
        self,
        query_transcript: str,
        *,
        query_fingerprint: TelemetryFingerprint | None = None,
        query_segment: str | None = None,
        query_category: str | None = None,
        exclude_incident_id: str | None = None,
        before_event_time_ms: int | None = None,
        top_k: int = 3,
    ) -> list[Candidate]:
        """Score every eligible prior incident, best semantic match first.

        `before_event_time_ms` keeps retrieval causal: an incident cannot
        be evidenced by something that had not happened yet. Ranking is by
        semantic similarity alone -- segment and category agreement are
        reported as separate flags rather than folded into the ranking, so
        the ordering stays explainable.
        """
        query_vector = self._encode([query_transcript])[0]

        scored: list[Candidate] = []
        for entry in self._entries:
            if exclude_incident_id is not None and entry.incident_id == exclude_incident_id:
                continue
            if (
                before_event_time_ms is not None
                and entry.event_time_ms >= before_event_time_ms
            ):
                continue

            semantic = cosine_similarity(query_vector, entry.embedding)
            telemetry = None
            if query_fingerprint is not None and entry.fingerprint is not None:
                telemetry = compare_fingerprints(
                    query_fingerprint, entry.fingerprint
                ).overall

            same_segment = query_segment is not None and entry.segment == query_segment
            same_category = (
                query_category is not None
                and entry.complaint_category == query_category
            )
            scored.append(
                Candidate(
                    incident_id=entry.incident_id,
                    semantic_similarity=semantic,
                    telemetry_similarity=telemetry,
                    same_segment=same_segment,
                    same_category=same_category,
                    label=classify_match(semantic, telemetry, same_segment),
                )
            )

        scored.sort(
            key=lambda c: (c.semantic_similarity, c.same_segment, c.incident_id),
            reverse=True,
        )
        return scored[:top_k]

    def best_match(
        self,
        query_transcript: str,
        *,
        query_fingerprint: TelemetryFingerprint | None = None,
        query_segment: str | None = None,
        query_category: str | None = None,
        exclude_incident_id: str | None = None,
        before_event_time_ms: int | None = None,
        require_same_category: bool = True,
    ) -> RetrievalResult:
        """Return the single reportable match, or None with a stated reason.

        Two independent gate conditions, both of which must hold: the
        candidate shares the query's complaint category, and its semantic
        cosine clears the threshold. See the module header for why cosine
        alone is not sufficient -- measured, not assumed.

        Telemetry similarity is deliberately NOT part of the gate. It is
        reported as separate evidence. A driver reporting the same thing
        again while the car looks different is a real and interesting
        case, and gating on telemetry too would hide it.

        A candidate whose telemetry could not be compared is not reported
        as a match. The contract requires `telemetry_similarity` to be a
        number in [0, 1] with no null option, and emitting 0.0 for "no
        data" would render in the UI as "no resemblance" -- a claim the
        data does not support. See PROGRESS_REPORT.md.
        """
        if require_same_category and query_category is None:
            return RetrievalResult(
                None,
                (),
                "no complaint category on the query; retrieval will not fall back "
                "to wording alone",
            )

        candidates = self.search(
            query_transcript,
            query_fingerprint=query_fingerprint,
            query_segment=query_segment,
            query_category=query_category,
            exclude_incident_id=exclude_incident_id,
            before_event_time_ms=before_event_time_ms,
        )

        if not candidates:
            return RetrievalResult(None, (), "no prior incidents in memory to compare")

        eligible = candidates
        if require_same_category:
            eligible = [c for c in candidates if c.same_category]
            if not eligible:
                return RetrievalResult(
                    None,
                    tuple(candidates),
                    f"no stored incident shares the reported category "
                    f"{query_category}",
                )

        above = [
            c for c in eligible if c.semantic_similarity >= self.semantic_threshold
        ]
        if not above:
            return RetrievalResult(
                None,
                tuple(candidates),
                f"no stored incident cleared the retrieval threshold of "
                f"{self.semantic_threshold:.2f}",
            )

        comparable = [c for c in above if c.telemetry_similarity is not None]
        if not comparable:
            return RetrievalResult(
                None,
                tuple(candidates),
                "a similar prior report exists but its telemetry could not be "
                "compared, so no match is reported",
            )

        return RetrievalResult(comparable[0], tuple(candidates), "match found")

    def _encode(self, texts: Sequence[str]) -> "np.ndarray":
        if self._encoder is not None:
            import numpy as np

            return np.asarray(self._encoder(texts), dtype=float)
        return encode_resilient(texts)


def classify_match(
    semantic: float, telemetry: float | None, same_segment: bool
) -> str:
    """Band a candidate for display. Prototype similarity, never probability."""
    if telemetry is None:
        return "SEMANTIC_ONLY_NO_TELEMETRY"
    if (
        semantic >= STRONG_MATCH_SEMANTIC
        and telemetry >= STRONG_MATCH_TELEMETRY
        and same_segment
    ):
        return "STRONG_PROTOTYPE_MATCH"
    if semantic >= SEMANTIC_SIMILARITY_THRESHOLD and (
        telemetry >= SEMANTIC_SIMILARITY_THRESHOLD or same_segment
    ):
        return "MODERATE_PROTOTYPE_MATCH"
    return "WEAK_PROTOTYPE_MATCH"
