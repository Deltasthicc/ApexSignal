"use client";

import type {
  HealthStatus,
  IncidentAssessment,
  ManifestEntry,
  RadioAnalysisOutput,
  ToneLabel,
} from "@/lib/coreApi";
import { Reveal } from "@/components/Reveal";
import { ReplayTimeline } from "@/components/ReplayTimeline";
import { IncidentPanel } from "@/components/IncidentPanel";
import { GoldIncidentCard } from "@/components/GoldIncidentCard";
import { UploadPanel } from "@/components/UploadPanel";

type Loadable<T> = T | "loading" | "error";

export function LiveInspector({
  health,
  entries,
  selectedId,
  onSelect,
  pitWallMode,
  onTogglePitWall,
  radioCache,
  assessmentCache,
  toneByIncident,
  totalLaps,
}: {
  health: HealthStatus | "loading" | "offline";
  entries: ManifestEntry[] | "loading" | "error";
  selectedId: string | null;
  onSelect: (id: string) => void;
  pitWallMode: boolean;
  onTogglePitWall: () => void;
  radioCache: Record<string, Loadable<RadioAnalysisOutput>>;
  assessmentCache: Record<string, Loadable<IncidentAssessment>>;
  toneByIncident: Record<string, ToneLabel | undefined>;
  totalLaps: number;
}) {
  const statusText =
    health === "loading"
      ? "CONNECTING"
      : health === "offline"
        ? "OFFLINE"
        : (health.evaluate_mode ?? "fixture").toUpperCase();
  const statusColor =
    health === "loading"
      ? "text-dim border-rule"
      : health === "offline"
        ? "text-red border-red/40 bg-red/5"
        : "text-teal border-teal/40 bg-teal/5";

  const selectedEntry = Array.isArray(entries)
    ? entries.find((e) => e.incident_id === selectedId) ?? null
    : null;
  const selectedAssessment = selectedId ? assessmentCache[selectedId] : undefined;
  const selectedRadio = selectedId ? radioCache[selectedId] : undefined;

  return (
    <section id="live" className="border-t border-rule bg-bg2 px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Try It Live</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            The pit-wall incident inspector
          </h2>
          <p className="mt-3 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            Real requests against{" "}
            <code className="text-teal">{process.env.NEXT_PUBLIC_CORE_API_BASE_URL}</code>{" "}
            — click a pin, read the evidence, toggle Pit Wall View to see what
            changes.
          </p>
        </Reveal>

        <Reveal delayMs={100}>
          <div className="mt-10 border border-rule bg-bg p-6">
            <div className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-rule pb-4">
              <p className="label-red">Live Inspector Widget</p>
              <div className="flex items-center gap-3 text-[10px] uppercase tracking-[0.12em]">
                <span className={`border px-2 py-1 tabular ${statusColor}`}>
                  &#9679; {statusText}
                </span>
                <button
                  onClick={onTogglePitWall}
                  className={`border px-3 py-1 transition ${
                    pitWallMode
                      ? "border-red bg-red text-ink"
                      : "border-rule text-dim hover:border-red/50 hover:text-ink"
                  }`}
                >
                  Pit Wall View {pitWallMode ? "ON" : "OFF"}
                </button>
              </div>
            </div>

            {entries === "loading" && (
              <div className="p-6 text-sm text-dim">Loading session replay&hellip;</div>
            )}
            {entries === "error" && (
              <div className="border border-red/40 bg-red/5 p-6 text-sm text-red">
                Could not reach the backend at{" "}
                <code>{process.env.NEXT_PUBLIC_CORE_API_BASE_URL}</code>. Start
                mock_server (or services/core_api) and reload.
              </div>
            )}

            {Array.isArray(entries) && entries.length > 0 && (
              <>
                <ReplayTimeline
                  entries={entries}
                  toneByIncident={toneByIncident}
                  selectedId={selectedId}
                  onSelect={onSelect}
                  pitWallMode={pitWallMode}
                  totalLaps={totalLaps}
                />

                {!pitWallMode && typeof selectedAssessment === "object" && (
                  <div className="mt-6">
                    <GoldIncidentCard assessment={selectedAssessment} entries={entries} />
                  </div>
                )}

                <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_300px]">
                  {selectedEntry ? (
                    <IncidentPanel
                      entry={selectedEntry}
                      radio={selectedRadio ?? "loading"}
                      assessment={selectedAssessment ?? "loading"}
                      pitWallMode={pitWallMode}
                    />
                  ) : (
                    <div className="border border-rule bg-bg2 p-6 text-sm text-dim">
                      Select a radio pin on the timeline to inspect it.
                    </div>
                  )}

                  <div className="flex flex-col gap-6">
                    <div className="border border-rule bg-bg2 p-5">
                      <p className="label-red mb-3">Session Incidents</p>
                      <ul className="flex flex-col gap-2">
                        {entries.map((entry) => (
                          <li key={entry.incident_id}>
                            <button
                              onClick={() => onSelect(entry.incident_id)}
                              className={`w-full border px-3 py-2 text-left text-xs transition ${
                                entry.incident_id === selectedId
                                  ? "border-red/50 bg-red/5 text-ink"
                                  : "border-rule text-dim hover:border-ink/30 hover:text-ink"
                              }`}
                            >
                              <span className="tabular text-red">L{entry.lap}</span>{" "}
                              {entry.sector_or_corner.replace(/_/g, " ")}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {!pitWallMode && <UploadPanel />}
                  </div>
                </div>
              </>
            )}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
