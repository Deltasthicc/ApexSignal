import { fetchIncidentAssessment } from "@/lib/coreApi";
import { IncidentCard } from "@/components/IncidentCard";

export default async function PitWallPage() {
  const assessment = await fetchIncidentAssessment("INC-031");

  return (
    <main className="min-h-screen bg-slate-950 p-8">
      <h1 className="mb-6 text-2xl font-semibold text-slate-100">
        Pit-Wall Incident Inspector
      </h1>
      <IncidentCard assessment={assessment} />
    </main>
  );
}
