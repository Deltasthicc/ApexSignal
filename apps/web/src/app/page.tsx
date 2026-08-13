"use client";

import { useEffect, useMemo, useState } from "react";
import {
  analyzeRadio,
  checkHealth,
  fetchIncidentAssessment,
  fetchReplayManifest,
  type HealthStatus,
  type IncidentAssessment,
  type ManifestEntry,
  type RadioAnalysisOutput,
  type ToneLabel,
} from "@/lib/coreApi";
import { TopBar } from "@/components/TopBar";
import { Hero } from "@/components/Hero";
import { PipelineSection } from "@/components/PipelineSection";
import { SessionGrid } from "@/components/SessionGrid";
import { LiveInspector } from "@/components/LiveInspector";
import { EvidenceStory } from "@/components/EvidenceStory";
import { ScopeSection } from "@/components/ScopeSection";
import { MaterialsSection, TeamSection } from "@/components/MaterialsTeam";
import {
  CircuitAtlasSection,
} from "@/components/CircuitAtlas";
import { RaceReplayBackground } from "@/components/RaceReplayBackground";

type Loadable<T> = T | "loading" | "error";

function presentationMode(health: HealthStatus | "loading" | "offline") {
  if (health === "loading") return "connecting";
  if (health === "offline") return "offline";
  if (health.evaluate_mode === "live") return "live pipeline";
  if (health.evaluate_mode === "replay" || health.evaluate_mode === "fixture") {
    return "API replay";
  }
  if (health.evaluate_mode === "embedded") return "local replay";
  return "validated replay";
}

export default function PitWallPage() {
  const [health, setHealth] = useState<HealthStatus | "loading" | "offline">(
    "loading"
  );
  const [entries, setEntries] = useState<ManifestEntry[] | "loading" | "error">(
    "loading"
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pitWallMode, setPitWallMode] = useState(false);
  const [radioCache, setRadioCache] = useState<
    Record<string, Loadable<RadioAnalysisOutput>>
  >({});
  const [assessmentCache, setAssessmentCache] = useState<
    Record<string, Loadable<IncidentAssessment>>
  >({});

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    fetchReplayManifest()
      .then((manifest) => {
        setEntries(manifest);
        if (manifest.length > 0) setSelectedId(manifest[0].incident_id);
      })
      .catch(() => setEntries("error"));
  }, []);

  // Prefetch radio + assessment for every entry so the grid/timeline can
  // color pins by tone and the evidence sections resolve immediately.
  useEffect(() => {
    if (!Array.isArray(entries)) return;
    for (const entry of entries) {
      const id = entry.incident_id;
      setRadioCache((prev) => (prev[id] ? prev : { ...prev, [id]: "loading" }));
      analyzeRadio(id)
        .then((data) => setRadioCache((prev) => ({ ...prev, [id]: data })))
        .catch(() => setRadioCache((prev) => ({ ...prev, [id]: "error" })));

      setAssessmentCache((prev) => (prev[id] ? prev : { ...prev, [id]: "loading" }));
      fetchIncidentAssessment(id)
        .then((data) => setAssessmentCache((prev) => ({ ...prev, [id]: data })))
        .catch(() => setAssessmentCache((prev) => ({ ...prev, [id]: "error" })));
    }
  }, [entries]);

  const toneByIncident = useMemo(() => {
    const map: Record<string, ToneLabel | undefined> = {};
    for (const [id, value] of Object.entries(radioCache)) {
      if (typeof value === "object") map[id] = value.tone_label;
    }
    return map;
  }, [radioCache]);

  const totalLaps = useMemo(() => {
    if (!Array.isArray(entries) || entries.length === 0) return 58;
    const maxLap = Math.max(...entries.map((e) => e.lap));
    return Math.max(58, Math.ceil((maxLap + 8) / 10) * 10);
  }, [entries]);

  function selectAndScrollToLive(id: string) {
    setSelectedId(id);
    document.getElementById("live")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <main className="bg-bg">
      <TopBar />
      <RaceReplayBackground />

      <Hero
        sessionId={Array.isArray(entries) && entries[0] ? entries[0].session_id : "—"}
        driver={Array.isArray(entries) && entries[0] ? entries[0].driver : "—"}
        incidentCount={Array.isArray(entries) ? entries.length : null}
        modeLabel={presentationMode(health)}
      />

      <PipelineSection />

      <CircuitAtlasSection />

      {Array.isArray(entries) && entries.length > 0 && (
        <SessionGrid
          entries={entries}
          radioCache={radioCache}
          assessmentCache={assessmentCache}
          onSelect={selectAndScrollToLive}
        />
      )}

      <LiveInspector
        health={health}
        entries={entries}
        selectedId={selectedId}
        onSelect={setSelectedId}
        pitWallMode={pitWallMode}
        onTogglePitWall={() => setPitWallMode((v) => !v)}
        radioCache={radioCache}
        assessmentCache={assessmentCache}
        toneByIncident={toneByIncident}
        totalLaps={totalLaps}
      />

      {Array.isArray(entries) && entries.length > 0 && (
        <EvidenceStory entries={entries} assessmentCache={assessmentCache} />
      )}

      <ScopeSection />
      <MaterialsSection />
      <TeamSection />
    </main>
  );
}
