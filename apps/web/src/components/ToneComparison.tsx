// Real output from services/radio_ai/app/tone.py (unmodified production
// code), run locally against real MikCil/f1-team-radio broadcast clips.
// These are the most confidently CALM and most confidently
// ELEVATED_AROUSAL readings across the full 30-clip corpus scored in
// services/radio_ai/tone_test/run_live_pipeline_demo.py -- not cherry-
// picked for effect, just the two extremes the model itself produced.
const CLIPS = [
  {
    id: "calm",
    src: "/audio/live_demo/calm-lannor01-saopaulo2024.mp3",
    label: "Most confidently CALM in the corpus",
    source: "2024 São Paulo Grand Prix — Lando Norris, real broadcast",
    transcript:
      "If the weather stays as it does, we think it will be these tyres to the end.",
    toneLabel: "CALM",
    toneScore: 0.865,
  },
  {
    id: "elevated",
    src: "/audio/live_demo/abudhabi2018-stovan01.mp3",
    label: "Most confidently ELEVATED_AROUSAL in the corpus",
    source: "2018 Abu Dhabi Grand Prix, real broadcast",
    transcript: "These tires are not doing well! Copy",
    toneLabel: "ELEVATED_AROUSAL",
    toneScore: 0.664,
  },
];

export function ToneComparison() {
  return (
    <div className="mt-6 border border-rule bg-bg p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[9px] uppercase tracking-[0.26em] text-dim">
          Tone model &middot; real broadcast audio, real output, not a fixture
        </p>
        <p className="text-[9px] uppercase tracking-[0.16em] text-red">
          Real VoiceCLAP output
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {CLIPS.map((clip) => (
          <div key={clip.id} className="border border-rule bg-bg2 p-4">
            <p className="mb-1 text-[10px] uppercase tracking-[0.14em] text-ink">
              {clip.label}
            </p>
            <p className="mb-2 text-[9px] text-dim">{clip.source}</p>
            <p className="mb-3 text-[11px] italic leading-relaxed text-dim">
              &ldquo;{clip.transcript}&rdquo;
            </p>
            <audio
              controls
              preload="metadata"
              className="h-8 w-full"
              src={clip.src}
              aria-label={`Play ${clip.label} clip`}
            />
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] tabular text-dim">
              <span>
                label <span className="text-ink">{clip.toneLabel}</span>
              </span>
              <span>
                confidence{" "}
                <span className="text-ink">{Math.round(clip.toneScore * 100)}%</span>
              </span>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-4 border-t border-rule pt-3 text-[11px] leading-relaxed text-dim">
        Two real drivers, two real broadcasts, six years apart &mdash; the
        model wasn&rsquo;t tuned on either. Same threshold used in
        production (<code className="text-teal">AROUSAL_ELEVATED_THRESHOLD</code>{" "}
        = 2.565, calibrated on 20 real human-labeled F1 radio clips) decides
        both. Run it yourself:{" "}
        <code className="text-teal">services/radio_ai/tone_test/run_live_pipeline_demo.py</code>.
      </p>
    </div>
  );
}
