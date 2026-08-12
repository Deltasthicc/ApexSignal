import {
  CORE_API_BASE_URL,
  type IncidentAssessment,
  type ManifestEntry,
  type RadioAnalysisOutput,
} from "@/lib/coreApi";
import { AudioPlayer } from "@/components/AudioPlayer";
import {
  CategoryBadge,
  ConfidencePill,
  RecurrenceBadge,
  ToneBadge,
} from "@/components/Badge";

type Props = {
  entry: ManifestEntry;
  radio: RadioAnalysisOutput | "loading" | "error";
  assessment: IncidentAssessment | "loading" | "error";
  pitWallMode: boolean;
};

export function IncidentPanel({ entry, radio, assessment, pitWallMode }: Props) {
  const audioSrc = `${CORE_API_BASE_URL}/static/${entry.audio_path}`;

  if (pitWallMode) {
    return (
      <article className="border border-rule bg-bg2 p-6">
        <p className="label-red mb-1">Pit Wall View · Radio &amp; Lap Timer Only</p>
        <h2 className="text-lg font-medium text-ink">
          Lap {entry.lap} &mdash; {entry.sector_or_corner.replace(/_/g, " ")}
        </h2>
        <p className="mt-4 text-sm text-dim">Raw radio log</p>
        <p className="mt-1 border-l-2 border-rule pl-3 text-sm italic text-ink">
          &ldquo;{entry.verified_transcript}&rdquo;
        </p>
        <div className="mt-5">
          <AudioPlayer src={audioSrc} transcript={entry.verified_transcript} />
        </div>
        <p className="mt-6 border-t border-rule pt-4 text-[11px] leading-relaxed text-dim">
          This is what the pit wall had before ApexSignal: the radio call and
          the lap clock. No tone analysis, no complaint classification, no
          baseline comparison, no historical match. Toggle Pit Wall off to see
          what ApexSignal adds.
        </p>
      </article>
    );
  }

  return (
    <article className="border border-rule bg-bg2 p-6">
      <div className="mb-1 flex items-center justify-between">
        <p className="label-red">Incident {entry.incident_id}</p>
        {typeof assessment === "object" && (
          <RecurrenceBadge state={assessment.recurrence_state} />
        )}
      </div>
      <h2 className="text-lg font-medium text-ink">
        Lap {entry.lap} &mdash; {entry.sector_or_corner.replace(/_/g, " ")}
      </h2>

      <div className="mt-5">
        <p className="label mb-2">Radio</p>
        <AudioPlayer src={audioSrc} transcript={entry.verified_transcript} />
        {radio === "loading" && (
          <p className="mt-3 text-xs text-dim">Analyzing transcript&hellip;</p>
        )}
        {radio === "error" && (
          <p className="mt-3 text-xs text-red">
            radio_ai output unavailable for this incident.
          </p>
        )}
        {typeof radio === "object" && (
          <>
            <p className="mt-3 text-sm text-ink">&ldquo;{radio.transcript}&rdquo;</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <ToneBadge tone={radio.tone_label} />
              <ConfidencePill value={radio.tone_confidence} />
              <span className="text-dim">·</span>
              <CategoryBadge category={radio.complaint_category} />
              {radio.category_confidence !== null && (
                <ConfidencePill value={radio.category_confidence} />
              )}
            </div>
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6 border-t border-rule pt-5 text-sm">
        <div>
          <p className="label mb-2">Baseline Evidence</p>
          {assessment === "loading" && <p className="text-xs text-dim">Loading&hellip;</p>}
          {assessment === "error" && (
            <p className="text-xs text-red">Assessment unavailable.</p>
          )}
          {typeof assessment === "object" && (
            <>
              <p className="text-ink">
                {assessment.baseline_evidence.status.replace(/_/g, " ")}
              </p>
              {assessment.baseline_evidence.status !== "INSUFFICIENT_DATA" ? (
                <p className="mt-1 tabular text-xs text-dim">
                  Throttle pickup{" "}
                  <span className="text-ink">
                    {assessment.baseline_evidence.throttle_pickup_delta_pct.toFixed(1)}%
                  </span>{" "}
                  · Sector{" "}
                  <span className="text-ink">
                    {assessment.baseline_evidence.sector_delta_s >= 0 ? "+" : ""}
                    {assessment.baseline_evidence.sector_delta_s.toFixed(2)}s
                  </span>{" "}
                  vs. own baseline
                </p>
              ) : (
                <p className="mt-1 text-xs text-dim">
                  Not enough baseline laps at this segment yet.
                </p>
              )}
            </>
          )}
        </div>
        <div>
          <p className="label mb-2">Lead Time</p>
          {typeof assessment === "object" && (
            <p className="tabular text-ink">
              {assessment.driver_warning_lead_time_s === null
                ? "No measurable lead-time established"
                : `${assessment.driver_warning_lead_time_s.toFixed(1)}s`}
            </p>
          )}
        </div>
      </div>

      <div className="mt-5 border-t border-rule pt-5 text-sm">
        <p className="label mb-2">Historical Match</p>
        {typeof assessment === "object" &&
          (assessment.echo_match ? (
            <div className="border border-rule bg-bg p-3">
              <p className="text-ink">
                Resembles {assessment.echo_match.incident_id} &middot;{" "}
                {assessment.echo_match.label.replace(/_/g, " ")}
              </p>
              <p className="mt-1 text-xs text-dim">
                Complaint similarity{" "}
                <span className="text-ink tabular">
                  {Math.round(assessment.echo_match.semantic_similarity * 100)}%
                </span>{" "}
                ·{" "}
                {assessment.echo_match.same_segment
                  ? "same segment"
                  : "different segment"}{" "}
                · telemetry pattern match{" "}
                <span className="text-ink tabular">
                  {Math.round(assessment.echo_match.telemetry_similarity * 100)}%
                </span>
              </p>
            </div>
          ) : (
            <p className="text-xs text-dim">No historical match above threshold.</p>
          ))}
      </div>

      {typeof assessment === "object" && (
        <p className="mt-5 border-t border-rule pt-4 text-xs leading-relaxed text-dim">
          {assessment.human_message}
        </p>
      )}
    </article>
  );
}
