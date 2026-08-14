import type { IncidentAssessment, ManifestEntry } from "@/lib/coreApi";

/**
 * The charter's "gold incident" beat, kept as two separate, honestly-scoped
 * facts rather than one chained story:
 *
 * 1. Recurrence -- the driver reported the same thing twice. Both lap
 *    numbers come straight from the manifest entries, so this row is exact.
 * 2. Lead time -- for THIS incident's own radio call, how long before a
 *    measurable telemetry change followed it. The contract does not expose
 *    which lap that change landed on (only the elapsed seconds), so the
 *    card does not invent one.
 */
export function GoldIncidentCard({
  assessment,
  entries,
}: {
  assessment: IncidentAssessment;
  entries: ManifestEntry[];
}) {
  if (!assessment.echo_match) {
    return null;
  }

  const warningEntry = entries.find(
    (e) => e.incident_id === assessment.echo_match!.incident_id
  );
  const lapDelta = warningEntry ? assessment.lap - warningEntry.lap : null;

  return (
    <div className="border border-red/40 bg-red/5 p-5">
      <p className="label-red mb-3">Gold Incident &middot; Recurrence &amp; Lead-Time Evidence</p>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="border border-rule bg-bg px-3 py-1.5 tabular text-ink">
          First report: Lap {warningEntry?.lap ?? "?"}
        </span>
        <span className="text-red">&rarr;</span>
        <span className="border border-rule bg-bg px-3 py-1.5 tabular text-ink">
          Same complaint recurs: Lap {assessment.lap}
          {lapDelta !== null && ` (Δ${lapDelta} laps)`}
        </span>
      </div>
      {assessment.driver_warning_lead_time_s !== null && (
        <p className="mt-3 text-xs text-dim">
          For this call specifically, a measurable telemetry change at this
          segment followed it by{" "}
          <span className="tabular text-red">
            {assessment.driver_warning_lead_time_s.toFixed(1)}s
          </span>
          .
        </p>
      )}
    </div>
  );
}
