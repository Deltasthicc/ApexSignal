# ApexSignal presentation runbook

## Open these before presenting

1. Public site: https://apex-signal-sigma.vercel.app
2. API health: https://apexsignal-mock-server.onrender.com/health
3. GitHub: https://github.com/Deltasthicc/ApexSignal

The web app has an embedded copy of the same replay records, so the judge flow
continues even while Render's free service wakes. The status chip says
`API REPLAY` when connected and `LOCAL REPLAY` when using that fallback.

## 90-second flow

1. **Problem (15s).** “The car has telemetry; the driver has feel. ApexSignal
   turns subjective radio into a structured incident and checks it against the
   driver's own telemetry baseline.”
2. **Architecture (15s).** Point to Radio Capture, Evidence Fusion, and the
   unified Incident Card. Emphasize separate evidence components rather than a
   magic risk score.
3. **Reference replay (35s).** Press **Play Replay**, open Lap 14, then Lap 17.
   Show the historical match, -9.4% throttle-pickup delta, +0.24s sector delta,
   and 189.4s measured lead time.
4. **Before/after (15s).** Toggle **Pit Wall View**. Explain that the raw view
   has radio plus lap timing; ApexSignal adds tone, taxonomy, baseline evidence,
   historical retrieval, and uncertainty-aware wording.
5. **Negative control (10s).** Open Lap 45. It returns `NO_DEVIATION`, no match,
   and no lead time instead of forcing an alert.

## Claims to use

- “Contract-validated deterministic reference replay.”
- “Twenty-five source-derived circuit centerlines.”
- “The production interface and API contract are deployed publicly.”
- “The real model services are implemented and benchmarked separately; the
  public judge path is replayed for reliability and reproducibility.”

## Claims not to use

- Do not call prototype similarity a probability of mechanical failure.
- Do not claim lie detection, diagnosis, autonomous strategy, or proactive
  recurrence detection before a new radio report.
- Do not describe the transcript voice preview as a real incident broadcast.
- Do not claim the public Render service runs Whisper/FAISS; it serves the
  validated replay contract.

## Five-minute preflight

- Load the public site in a private window.
- Confirm the status chip is `API REPLAY` or `LOCAL REPLAY`.
- Press **Play Replay** and select all three incident pins.
- Toggle **Pit Wall View** twice.
- Confirm the circuit backdrop changes after a lap/refresh.
- Keep the GitHub and API health URLs open as evidence.
