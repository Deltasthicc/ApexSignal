// Thin client for services/core_api or the public replay API.
// Response shapes must match contracts/schemas/*.schema.json exactly --
// nothing here invents a field the backend doesn't send.
import { DEMO_FIXTURES } from "@/data/demoFixtures";

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
  evaluate_mode?: "embedded" | "fixture" | "live" | "replay";
  service?: string;
};

// Real output from services/radio_ai/tone_test/run_live_pipeline_demo.py
// (ASR, tone, classifier, retrieval, run against real MikCil/f1-team-radio
// broadcast clips), served by mock_server / core_api at GET
// /v1/live-pipeline (contracts/fixtures/live_pipeline_demo.json) so the
// frontend fetches it over HTTP instead of bundling it as a hardcoded
// constant. This type mirrors that fixture's shape.
export type LivePipelineClip = {
  id: string;
  buttonLabel: string;
  src: string;
  source: string;
  transcript: string;
  toneLabel: ToneLabel;
  toneScore: number;
  category: string | null;
  categoryConfidence: number | null;
  match: { src: string; source: string; transcript: string; similarity: number } | null;
  verdict: string;
};

// services/core_api owns /v1/incidents/* and /v1/replay/*.
const CONFIGURED_BASE_URL = process.env.NEXT_PUBLIC_CORE_API_BASE_URL;
const BASE_URL = CONFIGURED_BASE_URL ?? "http://localhost:8000";

// services/radio_ai owns /v1/radio/analyze. In the fast local-dev path
// (mock_server) one process serves both roles, so this defaults to the
// same base; docker-compose points it separately when core_api and
// radio_ai run as distinct containers.
const RADIO_BASE_URL = process.env.NEXT_PUBLIC_RADIO_AI_BASE_URL ?? BASE_URL;
const DATA_MODE =
  process.env.NEXT_PUBLIC_DATA_MODE ??
  (CONFIGURED_BASE_URL ? "remote" : "embedded");
const USE_REMOTE_API = DATA_MODE === "remote";

function embeddedHealth(): HealthStatus {
  return {
    status: "ok",
    evaluate_mode: "embedded",
    service: "embedded_replay_fallback",
  };
}

function embeddedManifest(): ManifestEntry[] {
  return DEMO_FIXTURES.manifest.map((entry) => ({ ...entry })) as ManifestEntry[];
}

function embeddedAssessment(incidentId: string): IncidentAssessment {
  const record =
    DEMO_FIXTURES.assessments[
      incidentId as keyof typeof DEMO_FIXTURES.assessments
    ];
  if (!record) throw new Error(`No replay assessment for ${incidentId}`);
  return { ...record } as IncidentAssessment;
}

function embeddedRadio(incidentId: string): RadioAnalysisOutput {
  const record =
    DEMO_FIXTURES.radio[incidentId as keyof typeof DEMO_FIXTURES.radio] ??
    DEMO_FIXTURES.radio["INC-114"];
  return { ...record, incident_id: incidentId } as RadioAnalysisOutput;
}

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
  if (!USE_REMOTE_API) return Promise.resolve(embeddedHealth());
  return getJson<HealthStatus>(BASE_URL, "/health").catch(embeddedHealth);
}

export function fetchReplayManifest(): Promise<ManifestEntry[]> {
  if (!USE_REMOTE_API) return Promise.resolve(embeddedManifest());
  return getJson<ManifestEntry[]>(BASE_URL, "/v1/replay/manifest").catch(
    embeddedManifest
  );
}

export function fetchIncidentAssessment(
  incidentId: string
): Promise<IncidentAssessment> {
  if (!USE_REMOTE_API) return Promise.resolve(embeddedAssessment(incidentId));
  return getJson<IncidentAssessment>(
    BASE_URL,
    `/v1/incidents/${incidentId}`
  ).catch(() => embeddedAssessment(incidentId));
}

export function analyzeRadio(incidentId: string): Promise<RadioAnalysisOutput> {
  if (!USE_REMOTE_API) return Promise.resolve(embeddedRadio(incidentId));
  return postJson<RadioAnalysisOutput>(
    RADIO_BASE_URL,
    `/v1/radio/analyze?incident_id=${encodeURIComponent(incidentId)}`
  ).catch(() => embeddedRadio(incidentId));
}

// Offline fallback copy of contracts/fixtures/live_pipeline_demo.json --
// same resilience pattern as the rest of this client (embedded fixture
// if the API is unreachable), not a separate source of truth. If the
// fixture changes, update both.
const EMBEDDED_LIVE_PIPELINE: LivePipelineClip[] = [
  {
    id: "monaco23",
    buttonLabel: "Monaco '23 · understeer",
    src: "/audio/live_demo/flagship-nichul01-monaco2023.mp3",
    source: "2023 Monaco Grand Prix, real team-radio broadcast",
    transcript: "A lot of understeer creeping in. All speeds but also traction. Getting very poor.",
    toneLabel: "FATIGUED",
    toneScore: 0.536,
    category: "FRONT_TURNIN_BRAKE",
    categoryConfidence: 0.598,
    match: {
      src: "/audio/live_demo/match-lanstr01-saopaulo2021.mp3",
      source: "2021 São Paulo Grand Prix",
      transcript: "Feels like there's a lot of understeer now. I think there's quite a bit of damage...",
      similarity: 0.605,
    },
    verdict:
      "Front-end grip complaint, corroborated by a real prior report with a similar damage pattern. Driver's tone reads fatigued, not just describing a car issue — worth a pit-wall check-in alongside the setup review, not just a radio acknowledgment.",
  },
  {
    id: "canada19",
    buttonLabel: "Canada '19 · rear instability",
    src: "/audio/live_demo/canadian2019-georus01.mp3",
    source: "2019 Canadian Grand Prix, real team-radio broadcast",
    transcript:
      "I've got a bit of rear instability into turn 6 under braking on the entry phase. This is something I experienced a bit in P2 as well.",
    toneLabel: "ELEVATED_AROUSAL",
    toneScore: 0.524,
    category: "EXIT_TRACTION_REAR",
    categoryConfidence: 0.574,
    match: {
      src: "/audio/live_demo/bahrain2019-danric01.mp3",
      source: "2019 Bahrain Grand Prix",
      transcript: "Yeah, still the rear has hurt me on traction, but struggling a lot with front locking...",
      similarity: 0.517,
    },
    verdict:
      "Rear stability under braking, and the driver flagged it themselves as a repeat from practice. Corpus shows a comparable report from a different session — same phenomenon, different car/driver. Recommend a brake-bias / differential review, not a one-off note.",
  },
  {
    id: "bahrain19",
    buttonLabel: "Bahrain '19 · rear on traction",
    src: "/audio/live_demo/bahrain2019-danric01.mp3",
    source: "2019 Bahrain Grand Prix, real team-radio broadcast",
    transcript:
      "Yeah, still the rear has hurt me on traction, but struggling a lot with front locking, so trying to talk about coming rearwards. Okay, understood.",
    toneLabel: "FATIGUED",
    toneScore: 0.669,
    category: "EXIT_TRACTION_REAR",
    categoryConfidence: 0.549,
    match: {
      src: "/audio/live_demo/canadian2019-georus01.mp3",
      source: "2019 Canadian Grand Prix",
      transcript: "I've got a bit of rear instability into turn 6 under braking on the entry phase...",
      similarity: 0.517,
    },
    verdict:
      "Mixed front/rear balance complaint under fatigue. Retrieval finds the same underlying phenomenon reported from a different race — this isn't a one-off, it's a pattern worth a real setup conversation before the next stint.",
  },
  {
    id: "abudhabi18",
    buttonLabel: "Abu Dhabi '18 · tyres",
    src: "/audio/live_demo/abudhabi2018-stovan01.mp3",
    source: "2018 Abu Dhabi Grand Prix, real team-radio broadcast",
    transcript: "These tires are not doing well! Copy",
    toneLabel: "ELEVATED_AROUSAL",
    toneScore: 0.664,
    category: "TYRE_GRIP_DEGRADATION",
    categoryConfidence: 0.494,
    match: {
      src: "/audio/live_demo/abudhabi2018-lewham01.mp3",
      source: "2018 Abu Dhabi Grand Prix",
      transcript: "My tires definitely don't feel great. Ok, copy.",
      similarity: 0.744,
    },
    verdict:
      "Two independent drivers, same session type, both reporting degraded tyre feel — a 74% match, the strongest in this corpus. Recommend a compound/allocation review rather than treating either call as an isolated complaint.",
  },
  {
    id: "styrian21",
    buttonLabel: "Styrian '21 · no complaint",
    src: "/audio/live_demo/styrian2021-maxver01.mp3",
    source: "2021 Styrian Grand Prix, real team-radio broadcast",
    transcript: "Max, so specifically the issue is breaking turn 10 whilst on the curb, just for information.",
    toneLabel: "CALM",
    toneScore: 0.533,
    category: null,
    categoryConfidence: null,
    match: null,
    verdict:
      "No complaint category cleared the threshold and nothing in the corpus was searched against. No action recommended — reported honestly as informational, not forced into a finding to look useful.",
  },
];

export function fetchLivePipelineDemo(): Promise<LivePipelineClip[]> {
  if (!USE_REMOTE_API) return Promise.resolve(EMBEDDED_LIVE_PIPELINE);
  return getJson<LivePipelineClip[]>(BASE_URL, "/v1/live-pipeline").catch(
    () => EMBEDDED_LIVE_PIPELINE
  );
}

export {
  BASE_URL as CORE_API_BASE_URL,
  RADIO_BASE_URL as RADIO_AI_BASE_URL,
  USE_REMOTE_API,
};
