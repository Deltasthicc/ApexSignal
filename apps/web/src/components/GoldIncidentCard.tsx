import type { IncidentAssessment, ManifestEntry } from "@/lib/coreApi";

/**
 * The charter's "gold incident" beat: an early radio warning, then a
 * later measurable telemetry deterioration, with the lead time between
 * them. Every number here comes straight off the two IncidentAssessment
 * records -- the lap delta is computed from data already in hand, not
 * invented for the card.
 */
export function GoldIncidentCard({
  assessment,
  entries,
}: {
  assessment: IncidentAssessment;
  entries: ManifestEntry[];
}) {
  if (!assessment.echo_match || assessment.driver_warning_lead_time_s === null) {
    return null;
  }

  const warningEntry = entries.find(
    (e) => e.incident_id === assessment.echo_match!.incident_id
  );
  const lapDelta = warningEntry ? assessment.lap - warningEntry.lap : null;

  return (
    <div className="border border-red/40 bg-red/5 p-5">
      <p className="label-red mb-3">Gold Incident &middot; Lead Time Evidence</p>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="border border-rule bg-bg px-3 py-1.5 tabular text-ink">
          Radio warning: Lap {warningEntry?.lap ?? "?"}
        </span>
        <span className="text-red">&rarr;</span>
        <span className="border border-rule bg-bg px-3 py-1.5 tabular text-ink">
          Measurable deterioration: Lap {assessment.lap}
        </span>
        <span className="text-red">&rarr;</span>
        <span className="border border-red/40 bg-bg px-3 py-1.5 tabular text-red">
          Lead time: {assessment.driver_warning_lead_time_s.toFixed(1)}s
          {lapDelta !== null && ` (Δ${lapDelta} laps)`}
        </span>
      </div>
    </div>
  );
}
