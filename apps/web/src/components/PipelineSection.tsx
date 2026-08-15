import { Reveal } from "@/components/Reveal";
import { ToneComparison } from "@/components/ToneComparison";

const CARDS = [
  {
    num: "01",
    title: "Radio Capture & Perception",
    body: "Team radio is transcribed with Whisper ASR and scored for acoustic tone/arousal independently of the words used. Every call becomes a structured record, not a raw clip.",
    bullets: [
      "Whisper ASR transcript",
      "Acoustic tone/arousal model",
      "CALM / ELEVATED_AROUSAL / FATIGUED",
      "Fixed 5-category complaint taxonomy",
    ],
    api: "POST /v1/radio/analyze",
  },
  {
    num: "02",
    title: "Evidence Fusion",
    body: "The reported complaint is checked against the driver's own recent laps at that segment, and against prior incidents in memory — never against a population average or a fabricated risk score.",
    bullets: [
      "Own-baseline throttle & sector delta",
      "ECHO LAP historical retrieval",
      "Separate semantic + telemetry similarity",
      "Driver-warning lead time, measured",
    ],
    api: "POST /v1/incidents/evaluate",
  },
  {
    num: "03",
    title: "Incident Card",
    body: "One screen: transcript, tone, complaint category, baseline evidence, historical match, and lead time — worded in interpretation-safe language, with an honest null state whenever the evidence isn't there.",
    bullets: [
      "\"Reported phenomenon,\" never diagnosis",
      "No composite risk score, ever",
      "Explicit null: \"No measurable lead-time\"",
      "Pit-Wall toggle shows the before state",
    ],
    api: "GET /v1/incidents/{id}",
  },
];

const TAXONOMY = [
  "EXIT_TRACTION_REAR",
  "FRONT_TURNIN_BRAKE",
  "TYRE_GRIP_DEGRADATION",
  "VISIBILITY_TRACK_CONDITION",
  "MECHANICAL_OTHER",
];

export function PipelineSection() {
  return (
    <section id="pipeline" className="border-t border-rule bg-bg2 px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Architecture</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            Radio in, evidence out
          </h2>
          <p className="mt-3 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            Three stages, each independently testable, connected only by the
            frozen JSON contracts in <code className="text-teal">contracts/</code>.
          </p>
        </Reveal>

        <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3">
          {CARDS.map((card, i) => (
            <Reveal key={card.num} delayMs={i * 100}>
              <article className="h-full border border-rule bg-bg p-6 transition hover:border-red/30">
                <p className="label-red mb-4">{card.num}</p>
                <h3 className="mb-3 text-sm font-medium uppercase tracking-[0.08em] text-ink">
                  {card.title}
                </h3>
                <p className="mb-4 text-[11.5px] leading-relaxed text-dim">
                  {card.body}
                </p>
                <ul className="mb-4 flex flex-col gap-1.5">
                  {card.bullets.map((b) => (
                    <li key={b} className="pl-3 text-[11px] text-dim">
                      <span className="mr-2 text-red">&middot;</span>
                      {b}
                    </li>
                  ))}
                </ul>
                <p className="border-t border-rule pt-3 text-[10px] text-dim">
                  <code className="text-teal">{card.api}</code>
                </p>
              </article>
            </Reveal>
          ))}
        </div>

        <Reveal delayMs={200}>
          <div className="mt-6 border border-rule bg-bg p-5">
            <p className="mb-3 text-[9px] uppercase tracking-[0.26em] text-dim">
              Fixed complaint taxonomy &middot; five categories, frozen
            </p>
            <div className="flex flex-wrap gap-2">
              {TAXONOMY.map((t) => (
                <span
                  key={t}
                  className="border border-rule px-3 py-1.5 text-[10px] tracking-[0.06em] text-ink"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </Reveal>

        <Reveal delayMs={260}>
          <ToneComparison />
        </Reveal>
      </div>
    </section>
  );
}
