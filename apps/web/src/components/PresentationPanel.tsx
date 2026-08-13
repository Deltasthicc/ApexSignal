import type { HealthStatus } from "@/lib/coreApi";

const FLOW = [
  "Play the lap replay",
  "Open the Lap 14 warning",
  "Compare the Lap 17 recurrence",
  "Toggle Pit Wall View",
];

export function PresentationPanel({ health }: { health: HealthStatus }) {
  const apiConnected =
    health.evaluate_mode === "replay" ||
    health.evaluate_mode === "fixture" ||
    health.evaluate_mode === "live";

  return (
    <aside className="border border-rule bg-bg2 p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="label-red">Presentation Flow</p>
        <span
          className={`border px-2 py-1 text-[9px] uppercase tracking-[0.12em] ${
            apiConnected
              ? "border-teal/40 bg-teal/5 text-teal"
              : "border-gold/40 bg-gold/5 text-gold"
          }`}
        >
          {apiConnected ? "API connected" : "resilient fallback"}
        </span>
      </div>
      <ol className="mt-4 space-y-2">
        {FLOW.map((step, index) => (
          <li key={step} className="flex gap-3 text-[10.5px] leading-relaxed text-dim">
            <span className="tabular text-red">0{index + 1}</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>
      <p className="mt-4 border-t border-rule pt-3 text-[9.5px] leading-relaxed text-dim">
        Contract-validated deterministic replay. If the public API is waking up,
        the identical embedded record keeps the presentation usable.
      </p>
    </aside>
  );
}
