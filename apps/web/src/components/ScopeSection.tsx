import { Reveal } from "@/components/Reveal";

const CLAIMS = [
  {
    label: "No lie detection",
    body: "Tone/arousal is an acoustic model score, labeled as such. Never framed as detecting deception.",
  },
  {
    label: "No diagnosis",
    body: "\"Reported phenomenon,\" never \"diagnosed fault.\" ApexSignal never claims a confirmed mechanical cause.",
  },
  {
    label: "No composite risk score",
    body: "Every component — semantic similarity, telemetry similarity, tone confidence — stays visible and separate. Nothing gets collapsed into one number.",
  },
  {
    label: "No recurrence prediction",
    body: "ApexSignal flags a recurrence only after the driver reports it again by radio. It does not proactively watch telemetry in the background for a repeat before that happens.",
  },
];

const CUT = [
  {
    title: "Recurrence monitor",
    body: "A standing background process that watches telemetry independent of radio events was in the original concept. Cut for the MVP — recurrence is only assessed reactively, when a new radio report arrives.",
  },
  {
    title: "ECHO LAP at scale",
    body: "The presentation replay uses three contract-validated reference incidents. The same interface (semantic + telemetry similarity, category gate) can scale to a FAISS index over a full-season corpus.",
  },
  {
    title: "The Mask",
    body: "text_tone_disagreement (text vs. acoustic tone mismatch) is schema-supported but disabled by default pending real-clip validation gates — see services/radio_ai/VALIDATION_GATES.md.",
  },
  {
    title: "Field Context",
    body: "Cross-driver / cross-team context correlation is a roadmap idea from the project charter, intentionally out of scope for a one-driver, one-session MVP.",
  },
];

export function ScopeSection() {
  return (
    <section id="scope" className="border-t border-rule bg-bg px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Scope, Stated Honestly</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            What ApexSignal does not claim
          </h2>
          <p className="mt-3 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            A smaller, honest system beats a larger one that overclaims. Both
            lists below are enforced in code, not just in copy —
            <code className="ml-1 text-teal">test_contract_conformance.py</code>{" "}
            checks the risk-score rule directly.
          </p>
        </Reveal>

        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {CLAIMS.map((c, i) => (
            <Reveal key={c.label} delayMs={i * 80}>
              <div className="h-full border border-rule bg-bg2 p-5">
                <p className="mb-2 text-sm text-ink">{c.label}</p>
                <p className="text-[11.5px] leading-relaxed text-dim">{c.body}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delayMs={150}>
          <p className="mb-4 mt-14 text-[9px] uppercase tracking-[0.24em] text-dim">
            Deferred to the roadmap, not this build
          </p>
        </Reveal>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {CUT.map((c, i) => (
            <Reveal key={c.title} delayMs={i * 80}>
              <div className="h-full border border-rule bg-bg2 p-5">
                <p className="mb-2 text-[11px] uppercase tracking-[0.1em] text-red">
                  {c.title}
                </p>
                <p className="text-[11px] leading-relaxed text-dim">{c.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
