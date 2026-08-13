import type { IncidentAssessment, ManifestEntry, RadioAnalysisOutput } from "@/lib/coreApi";
import { Reveal } from "@/components/Reveal";
import { CategoryBadge, ToneBadge } from "@/components/Badge";

type Loadable<T> = T | "loading" | "error";

export function SessionGrid({
  entries,
  radioCache,
  assessmentCache,
  onSelect,
}: {
  entries: ManifestEntry[];
  radioCache: Record<string, Loadable<RadioAnalysisOutput>>;
  assessmentCache: Record<string, Loadable<IncidentAssessment>>;
  onSelect: (id: string) => void;
}) {
  return (
    <section id="sessions" className="border-t border-rule bg-bg px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Validated Reference Replay</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            Three evidence cases, one recurrence story
          </h2>
          <p className="mt-3 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            {entries[0]?.session_id ?? "Reference replay"} &middot;{" "}
            {entries[0]?.driver ?? "—"}. These deterministic records cover an
            initial warning, a telemetry-supported recurrence, and a negative
            control. Click one to inspect every evidence field.
          </p>
        </Reveal>

        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-3">
          {entries.map((entry, i) => {
            const radio = radioCache[entry.incident_id];
            const assessment = assessmentCache[entry.incident_id];
            const hasEcho =
              typeof assessment === "object" && assessment.echo_match !== null;
            return (
              <Reveal key={entry.incident_id} delayMs={i * 100}>
                <button
                  onClick={() => onSelect(entry.incident_id)}
                  className="w-full border border-rule bg-bg2 p-5 text-left transition hover:border-red/40"
                >
                  <div className="flex items-center justify-between">
                    <p className="label-red">{entry.incident_id}</p>
                    {hasEcho && (
                      <span className="border border-gold/40 bg-gold/5 px-2 py-0.5 text-[9px] uppercase tracking-[0.14em] text-gold">
                        Gold
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-ink">
                    Lap {entry.lap} &mdash; {entry.sector_or_corner.replace(/_/g, " ")}
                  </p>
                  <p className="mt-3 line-clamp-2 text-[11.5px] italic text-dim">
                    &ldquo;{entry.verified_transcript}&rdquo;
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {typeof radio === "object" && <ToneBadge tone={radio.tone_label} />}
                    <CategoryBadge category={entry.complaint_label} />
                  </div>
                </button>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
