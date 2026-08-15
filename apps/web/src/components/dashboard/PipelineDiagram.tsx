const STEPS = [
  {
    num: "01",
    title: "A radio call comes in",
    body: "“Rear is moving again when I get back on throttle.” Raw audio, nothing structured yet.",
    novelty: null,
  },
  {
    num: "02",
    title: "Speech becomes text",
    body: "faster-whisper ASR transcribes the call. This alone is what most teams building this brief will ship.",
    novelty: null,
  },
  {
    num: "03",
    title: "The voice is scored for tone",
    body: "Calm, elevated/stressed, or fatigued, with a confidence number.",
    novelty: "This is the bare-minimum output the hackathon brief actually required. Everything below is where the real product starts.",
  },
  {
    num: "04",
    title: "The complaint is sorted, not diagnosed",
    body: "One of 5 fixed categories — rear grip, front/braking, tyre wear, visibility/track, other mechanical. Never a fabricated diagnosis, just “this is the kind of thing being reported.”",
    novelty: "FEEL2PHYSICS concept: free-form driver language mapped to a frozen, defensible taxonomy — not reduced to a sentiment score, not invented on the fly.",
  },
  {
    num: "05",
    title: "Checked against the driver's own baseline",
    body: "Not “how a car should behave” in the abstract — this specific driver, this specific session, this specific corner, against their own last 5 laps.",
    novelty: "The single biggest differentiator from a generic anomaly detector: no population average, no invented “correct” driving model. A scrappy driver isn't flagged for being themselves.",
  },
  {
    num: "06",
    title: "Memory kicks in",
    body: "Past incidents are searched for anything that sounds similar and looks similar in telemetry. Two separate scores — sounds alike, looks alike — never mashed into one fake number.",
    novelty: "ECHO LAP concept: nothing is judged in isolation. Every new report is checked against everything reported before — real semantic retrieval + real telemetry fingerprinting, gated together, not blended.",
  },
  {
    num: "07",
    title: "Lead time gets measured",
    body: "Literally: how many seconds passed between the driver's warning and the moment the car's data actually got worse. Reported as null, honestly, when the data doesn't support a number — never forced.",
    novelty: "The actual product thesis: the driver is a sensor arriving before the graph does. This number is what proves that, per incident, with real seconds — not a claim, a measurement.",
  },
  {
    num: "08",
    title: "One incident card, not four tabs",
    body: "Transcript, tone, category, evidence, historical match, lead time, plain-English summary — one screen, one narrative.",
    novelty: "RacePulse concept: every claim decomposed into inspectable, separately-labeled components — built to survive a skeptical engineer, or judge, asking “why?”",
  },
];

export function PipelineDiagram() {
  return (
    <div className="border border-rule bg-bg p-6">
      <p className="mb-1 text-[9px] uppercase tracking-[0.16em] text-red">
        Full Architecture
      </p>
      <h3 className="mb-1 text-lg font-medium uppercase tracking-[0.03em] text-ink">
        Radio in, evidence out — in depth
      </h3>
      <p className="mb-6 max-w-2xl text-[11.5px] leading-relaxed text-dim">
        Not just STT. Four separate hackathon-brainstorm concepts —{" "}
        <span className="text-ink">memory</span>,{" "}
        <span className="text-ink">meaning</span>,{" "}
        <span className="text-ink">evidence</span>, and{" "}
        <span className="text-ink">restraint</span> — merged into one
        pipeline instead of shipping as four disconnected demos.
      </p>

      <div className="relative flex flex-col gap-0">
        {STEPS.map((step, i) => (
          <div key={step.num} className="relative flex gap-4 pb-6 last:pb-0">
            {i < STEPS.length - 1 && (
              <span className="absolute left-[15px] top-8 h-full w-px bg-rule" aria-hidden />
            )}
            <span className="z-10 flex h-8 w-8 shrink-0 items-center justify-center border border-red/50 bg-bg text-[10px] text-red">
              {step.num}
            </span>
            <div className="flex-1 pt-1">
              <p className="text-[12.5px] font-medium text-ink">{step.title}</p>
              <p className="mt-1 text-[11.5px] leading-relaxed text-dim">{step.body}</p>
              {step.novelty && (
                <p className="mt-2 border-l-2 border-teal/50 bg-teal/5 py-1.5 pl-3 text-[10.5px] leading-relaxed text-teal">
                  {step.novelty}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 border-t border-rule pt-5">
        <p className="mb-2 text-[9px] uppercase tracking-[0.16em] text-dim">
          What actually makes this different
        </p>
        <p className="text-[11.5px] leading-relaxed text-dim">
          Most teams tackling this brief ship steps 02–03 and call it done —
          a transcript and a mood badge next to a lap chart. The thesis here
          is that a single opaque &ldquo;risk score&rdquo; is a demo
          crowd-pleaser and a production liability: a confident number nobody
          can decompose is what gets a real incident-review committee to
          switch a system off. Every number in this pipeline traces back to a
          named piece of evidence, and it says &ldquo;I don&rsquo;t know&rdquo;
          out loud (<code className="text-teal">INSUFFICIENT_DATA</code>, a{" "}
          <code className="text-teal">null</code> lead time, no match) rather
          than manufacturing a positive to look impressive. We&rsquo;re not
          shipping a smarter transcript &mdash; we&rsquo;re shipping a plug-in
          layer that sits on top of the telemetry and radio systems a team
          already runs, and turns them into evidence an engineer would
          actually trust enough to act on mid-session.
        </p>
      </div>
    </div>
  );
}
