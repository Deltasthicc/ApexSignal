"use client";

import { useState } from "react";
import { Reveal } from "@/components/Reveal";
import { CategoryBadge, ConfidencePill } from "@/components/Badge";

const CATEGORIES = [
  "EXIT_TRACTION_REAR",
  "FRONT_TURNIN_BRAKE",
  "TYRE_GRIP_DEGRADATION",
  "VISIBILITY_TRACK_CONDITION",
  "MECHANICAL_OTHER",
  "NO_COMPLAINT",
];

// Real output from services/radio_ai/app/complaint_classifier.py::classify(),
// production embedding backend, run locally against real MikCil/
// f1-team-radio broadcast clips (run_live_pipeline_demo.py) -- not
// hand-picked for a clean story, just four real results that happen to
// span the honest range: a correct call, a real miss, a shaky call, and
// a correct negative. Pretending the classifier is always right would
// defeat the point of a human-in-the-loop section.
const CLIPS = [
  {
    id: "clip1",
    src: "/audio/live_demo/flagship-nichul01-monaco2023.mp3",
    transcript: "A lot of understeer creeping in. All speeds but also traction getting very poor.",
    aiCategory: "FRONT_TURNIN_BRAKE",
    aiConfidence: 0.598,
  },
  {
    id: "clip2",
    src: "/audio/live_demo/styrian2021-maxver01.mp3",
    transcript: "Max, so specifically the issue is breaking turn 10 whilst on the curb, just for information.",
    aiCategory: null,
    aiConfidence: null,
  },
  {
    id: "clip3",
    src: "/audio/live_demo/italian2018-lewham01.mp3",
    transcript: "Okay, copy, just keep the information coming.",
    aiCategory: null,
    aiConfidence: null,
  },
  {
    id: "clip4",
    src: "/audio/live_demo/spanish2023-oscpia01.mp3",
    transcript:
      "Oscar confirming that tyre degradation is all thermal. Not worried about wear, not worried about graining on this tyre.",
    aiCategory: "TYRE_GRIP_DEGRADATION",
    aiConfidence: 0.606,
  },
];

export function HumanLoopSection() {
  const [reviewed, setReviewed] = useState<Record<string, string>>({});

  const reviewedCount = Object.keys(reviewed).length;
  const corrections = Object.entries(reviewed).filter(
    ([id, label]) => label !== (CLIPS.find((c) => c.id === id)?.aiCategory ?? "NO_COMPLAINT")
  ).length;

  return (
    <section id="human-loop" className="border-t border-rule bg-bg px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Human-in-the-Loop</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            The AI proposes. A human confirms.
          </h2>
          <p className="mt-3 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            Play a real clip. See the AI&rsquo;s real call. Confirm it or
            correct it — the same workflow that grows the classifier&rsquo;s
            training data internally.
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-[9.5px] uppercase tracking-[0.1em]">
            <span className="border border-teal/40 bg-teal/5 px-2 py-1 text-teal">1 correct</span>
            <span className="border border-red/40 bg-red/5 px-2 py-1 text-red">1 real miss</span>
            <span className="border border-gold/40 bg-gold/5 px-2 py-1 text-gold">1 shaky call</span>
            <span className="border border-rule px-2 py-1 text-dim">1 correct pass</span>
          </div>
        </Reveal>

        <Reveal delayMs={100}>
          <div className="mt-8 flex items-center gap-4 border-b border-rule pb-4 text-[10px] uppercase tracking-[0.16em] text-dim">
            <span className="tabular text-ink">
              {reviewedCount} / {CLIPS.length} reviewed
            </span>
            {corrections > 0 && (
              <span className="tabular text-red">{corrections} corrected</span>
            )}
          </div>
        </Reveal>

        <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-2">
          {CLIPS.map((clip, i) => (
            <Reveal key={clip.id} delayMs={i * 90}>
              <ClipCard
                clip={clip}
                humanLabel={reviewed[clip.id]}
                onLabel={(label) =>
                  setReviewed((prev) => ({ ...prev, [clip.id]: label }))
                }
              />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function ClipCard({
  clip,
  humanLabel,
  onLabel,
}: {
  clip: (typeof CLIPS)[number];
  humanLabel: string | undefined;
  onLabel: (label: string) => void;
}) {
  const agreesWithAi = humanLabel === (clip.aiCategory ?? "NO_COMPLAINT");

  return (
    <div
      className={`border p-4 transition ${
        humanLabel
          ? agreesWithAi
            ? "border-teal/40 bg-teal/5"
            : "border-red/40 bg-red/5"
          : "border-rule bg-bg2"
      }`}
    >
      <p className="mb-3 text-[11.5px] italic leading-relaxed text-ink">
        &ldquo;{clip.transcript}&rdquo;
      </p>
      <audio
        controls
        preload="metadata"
        className="h-8 w-full"
        src={clip.src}
        aria-label="Play clip"
      />

      <div className="mt-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.14em] text-dim">
        <span>AI call:</span>
        <CategoryBadge category={clip.aiCategory} />
        <ConfidencePill value={clip.aiConfidence} />
      </div>

      <p className="mb-2 mt-3 text-[9px] uppercase tracking-[0.16em] text-dim">
        Your call
      </p>
      <div className="flex flex-wrap gap-1.5">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => onLabel(cat)}
            className={`border px-2 py-1 text-[9px] uppercase tracking-[0.08em] transition ${
              humanLabel === cat
                ? "border-ink bg-ink text-bg"
                : "border-rule text-dim hover:border-red/50 hover:text-ink"
            }`}
          >
            {cat.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {humanLabel && (
        <p className="mt-3 border-t border-rule pt-2 text-[10px] text-dim">
          {agreesWithAi
            ? "Confirmed — matches the AI's call."
            : "Corrected — logged for the next training pass."}
        </p>
      )}
    </div>
  );
}
