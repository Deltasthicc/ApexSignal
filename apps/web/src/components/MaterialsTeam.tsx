import { Reveal } from "@/components/Reveal";

const REPO = "https://github.com/Deltasthicc/ApexSignal";

const MATERIALS = [
  {
    title: "Project Charter",
    desc: "Full ambition, design rationale, and the language rules the product follows.",
    href: `${REPO}/blob/main/docs/PROJECT_CHARTER.md`,
  },
  {
    title: "API Contract",
    desc: "The frozen JSON contracts every workstream builds against — RadioAnalysisOutput, IncidentAssessment, the incident manifest.",
    href: `${REPO}/blob/main/contracts/api_contract.md`,
  },
  {
    title: "Architecture",
    desc: "Request flow, service boundaries, and the design decisions behind them.",
    href: `${REPO}/blob/main/ARCHITECTURE.md`,
  },
  {
    title: "Presentation Runbook",
    desc: "The rehearsed 90-second judge flow, exact claims, and five-minute preflight.",
    href: `${REPO}/blob/main/docs/PRESENTATION_RUNBOOK.md`,
  },
  {
    title: "Project Status",
    desc: "A precise shipped-versus-roadmap capability matrix with no hidden placeholders.",
    href: `${REPO}/blob/main/docs/PROJECT_STATUS.md`,
  },
];

const TEAM = [
  { role: "Workstream A", focus: "Data, telemetry, deterministic replay", name: "Jagrav" },
  { role: "Workstream B", focus: "Radio & language intelligence — ASR, tone, complaint classification", name: "Shashwat" },
  { role: "Workstream C", focus: "Incident memory, evidence engine, core API", name: "Tanish" },
  { role: "Workstream D", focus: "Product UI, visualization, deployment", name: "Mohit" },
];

export function MaterialsSection() {
  return (
    <section id="materials" className="border-t border-rule bg-bg2 px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Materials</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            Read the source
          </h2>
        </Reveal>
        <div className="mt-10 grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-5">
          {MATERIALS.map((m, i) => (
            <Reveal key={m.title} delayMs={i * 90}>
              <a
                href={m.href}
                target="_blank"
                rel="noreferrer"
                className="flex h-full flex-col border border-rule bg-bg p-6 transition hover:border-red/40"
              >
                <p className="mb-2 text-sm text-ink">{m.title}</p>
                <p className="mb-5 flex-1 text-[11.5px] leading-relaxed text-dim">
                  {m.desc}
                </p>
                <span className="text-[10.5px] uppercase tracking-[0.12em] text-red">
                  Read &rarr;
                </span>
              </a>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function TeamSection() {
  return (
    <section id="team" className="border-t border-rule bg-bg px-6 py-24">
      <div className="mx-auto max-w-6xl text-center">
        <Reveal>
          <p className="label-red mb-3">Team</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            Podium Finish
          </h2>
          <p className="mt-3 text-[12px] text-dim">
            AI Race Month &middot; GrandPrix Hackathon @ Paytm &middot; Problem
            Statement 1: The Silent Co-Driver
          </p>
        </Reveal>

        <div className="mx-auto mt-10 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
          {TEAM.map((t, i) => (
            <Reveal key={t.role} delayMs={i * 80}>
              <div className="border border-rule bg-bg2 p-5 text-left">
                <p className="label-red mb-1">{t.role}</p>
                <p className="mb-1 text-sm text-ink">{t.name}</p>
                <p className="text-[11px] text-dim">{t.focus}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <p className="mt-16 border-t border-rule pt-6 text-[10px] uppercase tracking-[0.18em] text-dim">
          <span className="mr-1 text-red">&#9612;</span>ApexSignal by Podium
          Finish &middot; MIT License &middot;{" "}
          <a
            href={REPO}
            target="_blank"
            rel="noreferrer"
            className="text-red transition hover:text-red-bright"
          >
            GitHub
          </a>
        </p>
      </div>
    </section>
  );
}
