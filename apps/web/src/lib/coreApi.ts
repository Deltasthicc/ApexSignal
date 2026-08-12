// Thin client for services/core_api (or mock_server during early development).
// Response shapes must match contracts/schemas/*.schema.json exactly --
// nothing here invents a field the backend doesn't send.

export type BaselineEvidence = {
  throttle_pickup_delta_pct: number;
  sector_delta_s: number;
  status: "BEHAVIOR_CONSISTENT" | "NO_DEVIATION" | "INSUFFICIENT_DATA";
};

export type EchoMatch = {
  incident_id: string;
  semantic_similarity: number;
  telemetry_similarity: number;
  same_segment: boolean;
  label: string;
} | null;

export type RecurrenceState = "NONE" | "POSSIBLE_RECURRENCE" | "CONFIRMED_BY_RADIO";

export type IncidentAssessment = {
  incident_id: string;
  lap: number;
  segment: string;
  reported_phenomenon: string;
  baseline_evidence: BaselineEvidence;
  echo_match: EchoMatch;
  driver_warning_lead_time_s: number | null;
  recurrence_state: RecurrenceState;
  human_message: string;
};

export type ToneLabel = "CALM" | "ELEVATED_AROUSAL" | "FATIGUED";

export type RadioAnalysisOutput = {
  incident_id: string;
  transcript: string;
  tone_label: ToneLabel;
  tone_score: number;
  tone_confidence: number;
  complaint_category: string | null;
  category_confidence: number | null;
  text_tone_disagreement: "LOW" | "MODERATE" | "HIGH" | null;
};

// One entry from the Workstream A incident manifest -- the ground-truth
// replay source (contracts/fixtures/incident_manifest.sample.json in
// fixture mode). Not an AI output: audio/lap/segment refs only.
export type ManifestEntry = {
  incident_id: string;
  session_id: string;
  driver: string;
  event_time_ms: number;
  lap: number;
  sector_or_corner: string;
  audio_path: string;
  verified_transcript: string;
  complaint_label: string;
  telemetry_window_path: string;
  tyre_compound: string | null;
  tyre_age_laps: number | null;
  lap_delta_s: number | null;
  verification_notes: string;
};

export type HealthStatus = {
  status: string;
  evaluate_mode?: "fixture" | "live";
  service?: string;
};

// services/core_api owns /v1/incidents/* and /v1/replay/*.
const BASE_URL =
  process.env.NEXT_PUBLIC_CORE_API_BASE_URL ?? "http://localhost:8000";

// services/radio_ai owns /v1/radio/analyze. In the fast local-dev path
// (mock_server) one process serves both roles, so this defaults to the
// same base; docker-compose points it separately when core_api and
// radio_ai run as distinct containers.
const RADIO_BASE_URL = process.env.NEXT_PUBLIC_RADIO_AI_BASE_URL ?? BASE_URL;

async function getJson<T>(base: string, path: string): Promise<T> {
  const response = await fetch(`${base}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} -> ${response.status}`);
  }
  return response.json();
}

async function postJson<T>(base: string, path: string): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    method: "POST",
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`${path} -> ${response.status}`);
  }
  return response.json();
}

export function checkHealth(): Promise<HealthStatus> {
  return getJson<HealthStatus>(BASE_URL, "/health");
}

export function fetchReplayManifest(): Promise<ManifestEntry[]> {
  return getJson<ManifestEntry[]>(BASE_URL, "/v1/replay/manifest");
}

export function fetchIncidentAssessment(
  incidentId: string
): Promise<IncidentAssessment> {
  return getJson<IncidentAssessment>(BASE_URL, `/v1/incidents/${incidentId}`);
}

export function analyzeRadio(incidentId: string): Promise<RadioAnalysisOutput> {
  return postJson<RadioAnalysisOutput>(
    RADIO_BASE_URL,
    `/v1/radio/analyze?incident_id=${encodeURIComponent(incidentId)}`
  );
}

export { BASE_URL as CORE_API_BASE_URL, RADIO_BASE_URL as RADIO_AI_BASE_URL };
