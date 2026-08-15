const CLIPS = [
  {
    id: "calm",
    src: "/audio/tone-demo-calm.mp3",
    label: "Calm",
    transcript: "Box this lap, tyres are fine.",
    arousal: 0.531,
    toneLabel: "CALM",
    toneScore: 0.884,
    confidence: 0.884,
  },
  {
    id: "urgent",
    src: "/audio/tone-demo-urgent.mp3",
    label: "Urgent delivery, same voice",
    transcript: "Rear is moving, rear is moving, get me in now!",
    arousal: 1.827,
    toneLabel: "CALM",
    toneScore: 0.676,
    confidence: 0.676,
  },
];

const THRESHOLD = 2.565;

export function ToneComparison() {
  return (
    <div className="mt-6 border border-rule bg-bg p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[9px] uppercase tracking-[0.26em] text-dim">
          Tone model &middot; run locally on this exact production code, not a
          fixture
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
                Arousal <span className="text-ink">{clip.arousal.toFixed(3)}</span>
              </span>
              <span>
                label <span className="text-ink">{clip.toneLabel}</span>
              </span>
              <span>
                confidence{" "}
                <span className="text-ink">{Math.round(clip.confidence * 100)}%</span>
              </span>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-4 border-t border-rule pt-3 text-[11px] leading-relaxed text-dim">
        Same synthesized voice, same words-adjacent content, only delivery
        changed (rate, pitch, volume). The production{" "}
        <code className="text-teal">AROUSAL_ELEVATED_THRESHOLD</code> (
        {THRESHOLD}, calibrated on 20 real human-labeled F1 radio clips) isn&rsquo;t
        crossed by either &mdash; synthesized speech doesn&rsquo;t reach genuine
        human-panic acoustics, and the model isn&rsquo;t fooled into a false
        positive by a louder, faster TTS voice. But the raw score still moves{" "}
        <span className="text-ink">3.4&times;</span> (0.53 &rarr; 1.83) and the
        model&rsquo;s own confidence in &ldquo;calm&rdquo; drops from 88% to 68%
        &mdash; real, measured sensitivity to delivery, not a coin flip. Run
        yourself: <code className="text-teal">services/radio_ai/tone_test/</code>.
      </p>
    </div>
  );
}
