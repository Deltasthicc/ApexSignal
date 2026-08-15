const STAGES = [
  {
    num: "01",
    title: "Audio in → Transcription",
    plain:
      "The driver's radio call (raw audio) is converted into text. This is the “translation” step — speech to words.",
    model: "distil-whisper/distil-large-v3.5-ct2 (via faster-whisper)",
    code: "services/radio_ai/app/asr.py → transcribe()",
    config: "Model ID + pinned version: services/radio_ai/app/config.py → ModelConfig",
  },
  {
    num: "02",
    title: "Tone / Voice Analysis",
    plain:
      "The raw audio itself (not the words) is scored for how the driver sounds — calm, stressed, or tired.",
    model: "laion/voiceclap-commercial (encoder + attribute heads)",
    code: "services/radio_ai/app/tone.py → score_waveform(), map_to_label()",
    config:
      "services/radio_ai/app/config.py → ToneThresholds class — Arousal threshold 2.565, Fatigue threshold 1.1",
    parameters: [
      "Arousal — how excited/tense the voice sounds",
      "Fatigue_Exhaustion — how tired the voice sounds",
      "Recording_Quality — how clean the audio is",
      "Background_Noise — how much noise is in the clip",
    ],
    rule:
      "Fatigue ≥ 1.1 → FATIGUED. Else if Arousal ≥ 2.565 → ELEVATED_AROUSAL. Else → CALM. Low quality/high noise doesn't change the label — it lowers the confidence score instead.",
  },
  {
    num: "03",
    title: "Complaint Category",
    plain:
      "The transcribed words are matched against 5 fixed problem categories — sorted, not diagnosed.",
    model: "sentence-transformers/all-MiniLM-L6-v2 (embedding + prototype similarity)",
    code: "services/radio_ai/app/complaint_classifier.py → classify()",
    config:
      "services/radio_ai/app/config.py → ClassifierConfig class — 5 category descriptions + similarity margin 0.16",
  },
  {
    num: "04",
    title: "Evidence Engine — the solution being generated",
    plain:
      "This is where the actual answer gets built: is the car really behaving differently, has this happened before, and how much warning did the call give. Plain statistics, not a model.",
    code: "services/evidence_memory/",
    parameters: [
      "baseline.py → compare_to_baseline() — this lap vs. the driver's own last 5 laps at this corner",
      "retrieval.py → best_match() — search past incidents for a similar report",
      "lead_time.py → measure_lead_time() — seconds between the call and the measurable change",
      "recurrence.py → assess_recurrence() — does the driver's own wording say “again”/“still”",
    ],
  },
  {
    num: "05",
    title: "Final Output → Incident Assessment",
    plain:
      "Everything above is combined into one verdict — sent to the dashboard as a single JSON record, never a raw score.",
    code: "services/core_api/app/pipeline.py → evaluate_incident()",
    config: "Served over HTTP by services/core_api/app/main.py → /v1/incidents/{id}",
  },
];

export function WorkflowCodeMap() {
  return (
    <div className="border border-rule bg-bg p-6">
      <p className="mb-1 text-[9px] uppercase tracking-[0.16em] text-red">
        For technical Q&amp;A
      </p>
      <h2 className="mb-1 text-lg font-medium uppercase tracking-[0.03em] text-ink">
        System Design Workflow
      </h2>
      <p className="mb-6 max-w-2xl text-[11.5px] leading-relaxed text-dim">
        What happens, in order, when a radio call comes in — and exactly
        which file and function does it. Every parameter below is a real,
        measured value, not a placeholder.
      </p>

      <div className="flex flex-col gap-5">
        {STAGES.map((stage) => (
          <div key={stage.num} className="border border-rule bg-bg2 p-4">
            <div className="flex items-baseline gap-3">
              <span className="text-[10px] text-red">{stage.num}</span>
              <p className="text-[12.5px] font-medium uppercase tracking-[0.04em] text-ink">
                {stage.title}
              </p>
            </div>
            <p className="mt-2 text-[11.5px] leading-relaxed text-dim">
              {stage.plain}
            </p>

            {stage.parameters && (
              <ul className="mt-3 flex flex-col gap-1">
                {stage.parameters.map((p) => (
                  <li key={p} className="pl-3 text-[10.5px] leading-relaxed text-dim">
                    <span className="mr-2 text-teal">&middot;</span>
                    {p}
                  </li>
                ))}
              </ul>
            )}

            {stage.rule && (
              <p className="mt-3 border-l-2 border-gold/50 bg-gold/5 py-1.5 pl-3 text-[10.5px] leading-relaxed text-gold">
                {stage.rule}
              </p>
            )}

            <div className="mt-3 flex flex-col gap-1 border-t border-rule pt-3">
              {stage.model && (
                <p className="text-[10px] text-dim">
                  <span className="text-teal">model </span>
                  {stage.model}
                </p>
              )}
              <p className="text-[10px] text-dim">
                <span className="text-teal">where in code </span>
                <code className="text-ink">{stage.code}</code>
              </p>
              {stage.config && (
                <p className="text-[10px] text-dim">
                  <span className="text-teal">parameters live in </span>
                  <code className="text-ink">{stage.config}</code>
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
