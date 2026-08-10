import type { IncidentAssessment } from "@/lib/coreApi";

/**
 * The single unified incident view. Every field here traces to a
 * contracts/schemas/incident_assessment.schema.json field, not to an
 * invented UI number. Keep it that way.
 */
export function IncidentCard({
  assessment,
}: {
  assessment: IncidentAssessment;
}) {
  const leadTime =
    assessment.driver_warning_lead_time_s === null
      ? "No measurable lead-time established"
      : `${assessment.driver_warning_lead_time_s}s`;

  return (
    <article className="max-w-xl rounded-lg border border-slate-800 bg-slate-900 p-6 text-slate-100">
      <p className="text-sm uppercase tracking-wide text-slate-400">
        {assessment.recurrence_state.replace(/_/g, " ")}
      </p>
      <h2 className="mt-1 text-lg font-medium">
        Lap {assessment.lap} — {assessment.segment}
      </h2>
      <p className="mt-2 text-slate-300">
        Reported phenomenon: {assessment.reported_phenomenon.replace(/_/g, " ")}
      </p>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-slate-400">Baseline evidence</p>
          <p>{assessment.baseline_evidence.status.replace(/_/g, " ")}</p>
        </div>
        <div>
          <p className="text-slate-400">Lead time</p>
          <p>{leadTime}</p>
        </div>
      </div>

      {assessment.echo_match ? (
        <div className="mt-4 rounded border border-slate-800 p-3 text-sm">
          <p className="text-slate-400">Historical match — {assessment.echo_match.label}</p>
          <p>
            Semantic {Math.round(assessment.echo_match.semantic_similarity * 100)}% ·
            Telemetry {Math.round(assessment.echo_match.telemetry_similarity * 100)}%
          </p>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">No historical match above threshold.</p>
      )}

      <p className="mt-4 text-sm text-slate-300">{assessment.human_message}</p>
    </article>
  );
}
