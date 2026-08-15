const LAYERS = [
  {
    title: "Audio ingest",
    items: ["Radio clip (.mp3/.wav)", "16kHz mono resample (soundfile + scipy or torchaudio)"],
  },
  {
    title: "Speech-to-text",
    items: [
      "distil-whisper/distil-large-v3.5-ct2 via faster-whisper (CTranslate2)",
      "CPU fallback: Systran/faster-whisper-small.en",
      "Pinned to a specific commit SHA — no silent model upgrades",
    ],
  },
  {
    title: "Acoustic tone model",
    items: [
      "laion/voiceclap-commercial encoder + attribute heads",
      "Outputs raw Arousal/Fatigue/Quality/Noise scores",
      "Mapped to CALM / ELEVATED_AROUSAL / FATIGUED by a threshold calibrated on 20 real human-labeled clips — not the model's raw default",
    ],
  },
  {
    title: "Complaint classifier",
    items: [
      "Production: sentence-transformers/all-MiniLM-L6-v2 embeddings + per-category prototype cosine similarity",
      "Fallback option: zero-shot NLI (DeBERTa v3)",
      "No fine-tuning — the taxonomy description text IS the model input",
    ],
  },
  {
    title: "Evidence engine (classical, not ML)",
    items: [
      "Own-baseline: median + MAD over the driver's own last 5 laps at that segment",
      "Retrieval: brute-force cosine similarity, in-memory (corpus is 15–30 incidents — FAISS is four orders of magnitude of complexity this doesn't need)",
      "Retrieval gate: category match AND cosine ≥ 0.40 — two independent conditions, empirically threshold-set over 247 hand-written phrase pairs",
      "Lead time: first_observable_change_time − radio_event_time, requires 2 consecutive deviating laps or reports null",
    ],
  },
  {
    title: "Storage",
    items: [
      "SQLite (storage/incidents.db) — incident metadata, recurrence flags",
      "Embeddings — in-memory Python list at process runtime, not persisted to SQLite (corpus is tiny; an index would be overhead, not optimization)",
      "Contracts — frozen JSON schemas + fixtures in contracts/, the interface every service is validated against",
      "Telemetry — Parquet windows per incident, read by pandas",
    ],
  },
  {
    title: "API layer",
    items: [
      "radio_ai (FastAPI) — POST /v1/radio/analyze",
      "core_api (FastAPI) — /v1/incidents/*, /v1/replay/*, /v1/live-pipeline",
      "mock_server (FastAPI) — same paths, fixture-backed, for frontend-first development",
      "No service imports another's code directly — every boundary is the JSON contract, not a shared library",
    ],
  },
  {
    title: "Frontend",
    items: [
      "Next.js 16 (Turbopack), React 18, TypeScript, Tailwind",
      "Fetches over HTTP with an embedded fixture fallback baked into the client — stays interactive if the backend is cold-starting",
    ],
  },
];

export function SystemDesignDiagram() {
  return (
    <div className="border border-rule bg-bg p-6">
      <p className="mb-1 text-[9px] uppercase tracking-[0.16em] text-red">System Design</p>
      <h3 className="mb-1 text-lg font-medium uppercase tracking-[0.03em] text-ink">
        Full stack, layer by layer
      </h3>
      <p className="mb-6 max-w-2xl text-[11.5px] leading-relaxed text-dim">
        Every box below is a real, running piece of this system — not a
        planned architecture. Reproduce any layer directly: model IDs and
        pinned revisions are in <code className="text-teal">services/radio_ai/app/config.py</code>.
      </p>

      <div className="grid grid-cols-1 gap-3">
        {LAYERS.map((layer, i) => (
          <div key={layer.title} className="flex gap-4">
            <div className="flex flex-col items-center">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center border border-rule bg-bg2 text-[10px] text-dim">
                {i + 1}
              </span>
              {i < LAYERS.length - 1 && <span className="mt-1 h-full w-px flex-1 bg-rule" />}
            </div>
            <div className="flex-1 border border-rule bg-bg2 p-3 pb-4">
              <p className="mb-1.5 text-[11.5px] font-medium uppercase tracking-[0.04em] text-ink">
                {layer.title}
              </p>
              <ul className="flex flex-col gap-1">
                {layer.items.map((item) => (
                  <li key={item} className="pl-3 text-[10.5px] leading-relaxed text-dim">
                    <span className="mr-2 text-red">&middot;</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 border border-gold/40 bg-gold/5 p-4">
        <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-gold">
          Direct answer: do we use a generative LLM? Tool-calling? MCP?
        </p>
        <p className="text-[11.5px] leading-relaxed text-dim">
          <span className="text-ink">No, deliberately, on all three.</span> No
          GPT/Claude/Gemini-style generative model is in this pipeline, no
          agent framework, no tool-calling loop, no MCP server. Every model
          above is a small, pinned, task-specific pretrained model (an ASR
          transcriber, a speech-emotion encoder, a sentence-embedding
          model) — not a chat model reasoning in free text. That&rsquo;s a
          product decision, not a limitation: a generative model
          summarizing &ldquo;what happened&rdquo; can hallucinate a
          plausible-sounding but wrong diagnosis, and there is no way to
          audit that after the fact. Every number this system produces
          instead traces to a named, deterministic computation — a
          threshold, a cosine similarity, a median — specifically so an
          engineer (or a judge) can ask &ldquo;why did it say that&rdquo;
          and get a real answer, not a plausible-sounding one.
        </p>
      </div>
    </div>
  );
}
