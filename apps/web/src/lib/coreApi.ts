// Thin client for services/core_api (or mock_server during early development).
// Response shape must match contracts/schemas/incident_assessment.schema.json.

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

export type IncidentAssessment = {
  incident_id: string;
  lap: number;
  segment: string;
  reported_phenomenon: string;
  baseline_evidence: BaselineEvidence;
  echo_match: EchoMatch;
  driver_warning_lead_time_s: number | null;
  recurrence_state: "NONE" | "POSSIBLE_RECURRENCE" | "CONFIRMED_BY_RADIO";
  human_message: string;
};

const BASE_URL =
  process.env.NEXT_PUBLIC_CORE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchIncidentAssessment(
  incidentId: string
): Promise<IncidentAssessment> {
  const response = await fetch(
    `${BASE_URL}/v1/incidents/${incidentId}`,
    { cache: "no-store" }
  );
  if (!response.ok) {
    throw new Error(`core_api returned ${response.status} for ${incidentId}`);
  }
  return response.json();
}
