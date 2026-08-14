import type { IncidentAssessment, ManifestEntry } from "@/lib/coreApi";
import { Reveal } from "@/components/Reveal";
import { RecurrenceBadge } from "@/components/Badge";

type Loadable<T> = T | "loading" | "error";

export function EvidenceStory({
  entries,
  assessmentCache,
}: {
  entries: ManifestEntry[];
  assessmentCache: Record<string, Loadable<IncidentAssessment>>;
}) {
  const goldAfter = entries.find((e) => {
    const a = assessmentCache[e.incident_id];
    return typeof a === "object" && a.echo_match !== null;
  });
  const goldAfterAssessment =
    goldAfter && (assessmentCache[goldAfter.incident_id] as IncidentAssessment | undefined);
  const goldBefore =
    goldAfterAssessment?.echo_match &&
    entries.find((e) => e.incident_id === goldAfterAssessment.echo_match!.incident_id);

  return (
    <section id="evidence" className="border-t border-rule bg-bg2 px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Evidence</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            Pit wall vs. ApexSignal
          </h2>
          <p className="mt-3 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            The same lap, two views: what the pit wall had from raw radio and
            the lap clock, and what ApexSignal adds once the second call
            arrives.
          </p>
        </Reveal>

        {goldBefore && goldAfter && goldAfterAssessment && (
          <Reveal delayMs={100}>
            <div className="mt-10 border border-rule bg-bg p-6">
              <p className="label-red mb-5">
                Key Moment &middot; Lap {goldBefore.lap} &rarr; Lap {goldAfter.lap}
              </p>
              <div className="grid grid-cols-1 items-center gap-6 md:grid-cols-[1fr_40px_1fr]">
                <div>
                  <p className="mb-3 inline-block border border-rule bg-bg2 px-2 py-1 text-[9px] uppercase tracking-[0.14em] text-dim">
                    Before &middot; Pit Wall Only
                  </p>
                  <p className="tabular text-sm text-ink">
                    L{goldBefore.lap} &mdash; radio call received
                  </p>
                  <p className="mt-1 text-[11.5px] italic text-dim">
                    &ldquo;{goldBefore.verified_transcript}&rdquo;
                  </p>
                  <p className="mt-2 text-[11px] text-dim">
                    No tone read, no category, no baseline check. Logged and
                    moved on.
                  </p>
                </div>
                <div className="flex justify-center text-red">&rarr;</div>
                <div>
                  <p className="mb-3 inline-block border border-teal/40 bg-teal/5 px-2 py-1 text-[9px] uppercase tracking-[0.14em] text-teal">
                    After &middot; ApexSignal
                  </p>
                  <p className="tabular text-sm text-ink">
                    L{goldAfter.lap} &mdash; same complaint, telemetry consistent
                  </p>
                  <p className="mt-1 text-[11.5px] text-dim">
                    Baseline: <span className="text-ink">{goldAfterAssessment.baseline_evidence.status.replace(/_/g, " ")}</span>
                    {" · "}
                    Lead time:{" "}
                    <span className="text-teal">
                      {goldAfterAssessment.driver_warning_lead_time_s?.toFixed(1)}s
                    </span>
                  </p>
                  <div className="mt-2">
                    <RecurrenceBadge state={goldAfterAssessment.recurrence_state} />
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        )}

        <Reveal delayMs={200}>
          <div className="mt-6 overflow-x-auto border border-rule bg-bg">
            <table className="w-full min-w-[560px] text-left text-[11.5px]">
              <thead>
                <tr className="border-b border-rule text-[9px] uppercase tracking-[0.16em] text-dim">
                  <th className="px-4 py-3">Incident</th>
                  <th className="px-4 py-3">Lap</th>
                  <th className="px-4 py-3">Baseline</th>
                  <th className="px-4 py-3">Historical Match</th>
                  <th className="px-4 py-3">Lead Time</th>
                  <th className="px-4 py-3">Recurrence</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const a = assessmentCache[entry.incident_id];
                  return (
                    <tr key={entry.incident_id} className="border-b border-rule last:border-none">
                      <td className="px-4 py-3 text-ink">{entry.incident_id}</td>
                      <td className="tabular px-4 py-3 text-dim">{entry.lap}</td>
                      {typeof a === "object" ? (
                        <>
                          <td className="px-4 py-3 text-dim">
                            {a.baseline_evidence.status.replace(/_/g, " ")}
                          </td>
                          <td className="px-4 py-3 text-dim">
                            {a.echo_match ? a.echo_match.incident_id : "none"}
                          </td>
                          <td className="tabular px-4 py-3 text-dim">
                            {a.driver_warning_lead_time_s === null
                              ? "—"
                              : `${a.driver_warning_lead_time_s.toFixed(1)}s`}
                          </td>
                          <td className="px-4 py-3">
                            <RecurrenceBadge state={a.recurrence_state} />
                          </td>
                        </>
                      ) : (
                        <td className="px-4 py-3 text-dim" colSpan={4}>
                          {a === "error" ? "unavailable" : "loading…"}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
