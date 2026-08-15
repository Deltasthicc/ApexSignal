"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { CategoryBadge, ConfidencePill, ToneBadge } from "@/components/Badge";
import { fetchLivePipelineDemo, type LivePipelineClip } from "@/lib/coreApi";
import {
  ConfidenceMetersChart,
  RetrievalGateChart,
  TyreTempChart,
  SpeedTraceChart,
  IncidentTimelineChart,
} from "@/components/dashboard/DashboardCharts";
import { PipelineDiagram } from "@/components/dashboard/PipelineDiagram";
import { SystemDesignDiagram } from "@/components/dashboard/SystemDesignDiagram";

type Stage = 0 | 1 | 2 | 3 | 4 | 5;
const STAGE_DELAY_MS = 750;
type Tab = "console" | "architecture";

export default function DashboardPage() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  const [tab, setTab] = useState<Tab>("console");
  const [clips, setClips] = useState<LivePipelineClip[] | "loading" | "error">("loading");
  const [selected, setSelected] = useState<LivePipelineClip | null>(null);
  const [stage, setStage] = useState<Stage>(0);
  const [running, setRunning] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    queueMicrotask(() => {
      if (!sessionStorage.getItem("apexsignal_engineer_session")) {
        router.replace("/login");
      } else {
        setAuthChecked(true);
      }
    });
  }, [router]);

  useEffect(() => {
    fetchLivePipelineDemo()
      .then((data) => {
        setClips(data);
        setSelected(data[0] ?? null);
      })
      .catch(() => setClips("error"));
  }, []);

  function signOut() {
    sessionStorage.removeItem("apexsignal_engineer_session");
    router.push("/login");
  }

  function selectClip(clip: LivePipelineClip) {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setSelected(clip);
    setStage(0);
    setRunning(false);
  }

  function playAlone() {
    setStage(0);
    audioRef.current?.play().catch(() => {});
  }

  function runPipeline() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setStage(0);
    setRunning(true);
    audioRef.current?.play().catch(() => {});

    ([1, 2, 3, 4, 5] as Stage[]).forEach((s, i) => {
      const t = setTimeout(() => {
        setStage(s);
        if (s === 5) setRunning(false);
      }, STAGE_DELAY_MS * (i + 1));
      timers.current.push(t);
    });
  }

  const toneActive = stage >= 2;
  const categoryActive = stage >= 3;
  const telemetryActive = stage >= 3;
  const retrievalActive = stage >= 4;
  const verdictActive = stage >= 5;

  if (!authChecked) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-bg text-[11px] uppercase tracking-[0.16em] text-dim">
        Checking session…
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-bg pb-24">
      <header className="sticky top-0 z-40 border-b border-rule bg-bg/95 backdrop-blur">
        <div className="flex items-center justify-between px-6 py-3.5">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink">
              <span className="mr-1 text-red">&#9612;</span>ApexSignal Pit Wall Console
            </p>
            <p className="text-[9.5px] text-dim">Race Engineer &middot; REFERENCE_REPLAY_2026</p>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/" className="text-[10px] uppercase tracking-[0.14em] text-dim transition hover:text-red">
              Public site
            </Link>
            <button
              onClick={signOut}
              className="border border-rule px-3 py-1.5 text-[10px] uppercase tracking-[0.14em] text-dim transition hover:border-red/50 hover:text-red"
            >
              Sign out
            </button>
          </div>
        </div>
        <div className="flex gap-1 px-6">
          {(
            [
              { id: "console", label: "Live Console" },
              { id: "architecture", label: "Architecture" },
            ] as { id: Tab; label: string }[]
          ).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`border-b-2 px-4 py-2.5 text-[10.5px] uppercase tracking-[0.12em] transition ${
                tab === t.id ? "border-red text-ink" : "border-transparent text-dim hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      {tab === "architecture" ? (
        <div className="mx-auto max-w-7xl px-6 pt-8">
          <p className="label-red mb-2">Reference</p>
          <h1 className="mb-6 text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            How this actually works
          </h1>
          <div className="flex flex-col gap-6">
            <PipelineDiagram />
            <SystemDesignDiagram />
          </div>
        </div>
      ) : clips === "loading" || !selected ? (
        <div className="mx-auto max-w-7xl px-6 pt-16 text-[11px] uppercase tracking-[0.16em] text-dim">
          Loading live-pipeline data from the API…
        </div>
      ) : clips === "error" ? (
        <div className="mx-auto max-w-7xl px-6 pt-16 text-[11px] uppercase tracking-[0.16em] text-red">
          Could not reach the API — check mock_server/core_api are running on the configured port.
        </div>
      ) : (
        <div className="mx-auto max-w-7xl px-6 pt-8">
          <p className="label-red mb-2">Live Console</p>
          <h1 className="mb-2 text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            A radio call just came in
          </h1>
          <p className="mb-6 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            On its own, a radio call is noise next to a wall of telemetry.
            Play it, then run the pipeline — watch the same dashboard the
            engineer already stares at all day light up with context,
            memory, and a call to action.
          </p>

          <div className="flex flex-wrap gap-2">
            {clips.map((clip) => (
              <button
                key={clip.id}
                type="button"
                onClick={() => selectClip(clip)}
                className={`border px-3 py-2 text-[10px] uppercase tracking-[0.1em] transition ${
                  selected.id === clip.id
                    ? "border-red bg-red text-ink"
                    : "border-rule text-dim hover:border-red/50 hover:text-ink"
                }`}
              >
                {clip.buttonLabel}
              </button>
            ))}
          </div>

          <div className="mt-6 border border-rule bg-bg2 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-[9px] uppercase tracking-[0.16em] text-red">Incoming radio call</p>
                <p className="text-[10px] text-dim">{selected.source}</p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={playAlone}
                  className="border border-rule px-3 py-2 text-[10px] uppercase tracking-[0.12em] text-dim transition hover:border-ink/40 hover:text-ink"
                >
                  ▶ Play audio only
                </button>
                <button
                  type="button"
                  onClick={runPipeline}
                  disabled={running}
                  className="border border-red bg-red px-3 py-2 text-[10px] uppercase tracking-[0.12em] text-ink transition hover:bg-red-bright disabled:opacity-50"
                >
                  {running ? "Running pipeline…" : "▶ Run live pipeline"}
                </button>
              </div>
            </div>
            <audio
              ref={audioRef}
              key={selected.id}
              controls
              preload="metadata"
              className="mt-3 h-8 w-full"
              src={selected.src}
              aria-label="Play the real radio call"
            />
            {stage === 0 && (
              <p className="mt-3 text-[11px] italic text-dim">
                No transcript, no tone, no category, no context yet — this is all an engineer has from the radio alone.
              </p>
            )}
          </div>

          {/* Pipeline reveal */}
          <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-[1fr_auto_1fr]">
            <div className="flex h-full flex-col border border-rule bg-bg p-5">
              <p className="mb-3 text-[9px] uppercase tracking-[0.16em] text-dim">Pipeline stages</p>
              <div className="flex flex-col gap-3">
                <PipelineStage num="01" label="ASR transcript (faster-whisper)" active={stage >= 1}>
                  <p className="text-[12px] italic text-ink">&ldquo;{selected.transcript}&rdquo;</p>
                </PipelineStage>
                <PipelineStage num="02" label="Acoustic tone (VoiceCLAP)" active={toneActive}>
                  <div className="flex items-center gap-2">
                    <ToneBadge tone={selected.toneLabel} />
                    <ConfidencePill value={selected.toneScore} />
                  </div>
                </PipelineStage>
                <PipelineStage num="03" label="Complaint category (classifier)" active={categoryActive}>
                  <div className="flex items-center gap-2">
                    <CategoryBadge category={selected.category} />
                    <ConfidencePill value={selected.categoryConfidence} />
                  </div>
                </PipelineStage>
              </div>
            </div>

            <div className="flex items-center justify-center py-4 text-red lg:flex-col lg:py-0">
              <span className="text-lg">&rarr;</span>
              <span className="mt-1 text-center text-[9px] uppercase leading-tight tracking-[0.12em] text-dim">
                retrieval gate
              </span>
            </div>

            <div
              className={`flex h-full flex-col border p-5 transition ${
                retrievalActive ? (selected.match ? "border-teal/40 bg-teal/5" : "border-rule bg-bg") : "border-rule bg-bg opacity-40"
              }`}
            >
              {!retrievalActive ? (
                <p className="text-[10px] uppercase tracking-[0.16em] text-dim">04 &middot; Historical match — run the pipeline</p>
              ) : selected.match ? (
                <>
                  <p className="mb-1 text-[9px] uppercase tracking-[0.16em] text-teal">04 &middot; Historical match found</p>
                  <p className="mb-2 text-[10px] text-dim">{selected.match.source}</p>
                  <p className="text-[12px] italic text-ink">&ldquo;{selected.match.transcript}&rdquo;</p>
                  <p className="mt-3 border-t border-rule pt-2 text-[10px] tabular text-dim">
                    Semantic similarity <span className="text-teal">{Math.round(selected.match.similarity * 100)}%</span>
                  </p>
                </>
              ) : (
                <p className="text-[11px] leading-relaxed text-dim">No historical match — nothing cleared the retrieval gate. Reported honestly.</p>
              )}
            </div>
          </div>

          {/* Verdict */}
          <div
            className={`mt-6 border p-5 transition-all duration-500 ${
              verdictActive ? "border-gold/50 bg-gold/5 opacity-100" : "border-rule bg-bg2 opacity-40"
            }`}
          >
            <p className="mb-2 text-[9px] uppercase tracking-[0.16em] text-gold">05 &middot; Verdict</p>
            <p className="text-[13px] leading-relaxed text-ink">
              {verdictActive ? selected.verdict : "Run the pipeline to generate a recommendation from the evidence above."}
            </p>
          </div>

          {/* Telemetry dashboard */}
          <div className="mt-10">
            <p className="label-red mb-2">Engineer&rsquo;s Existing Telemetry</p>
            <h2 className="mb-1 text-xl font-medium uppercase tracking-[0.03em] text-ink">
              {stage >= 3 ? "Now with context" : "Just data, on its own"}
            </h2>
            <p className="mb-5 max-w-2xl text-[11.5px] leading-relaxed text-dim">
              Each panel activates as its own pipeline stage completes, not
              all at once — this is ApexSignal running on top of telemetry
              the team already has, not replacing it. Two panels are real
              production output for this exact call; two are illustrative
              (MikCil broadcast clips carry no telemetry export), clearly
              marked either way.
            </p>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              <ConfidenceMetersChart active={toneActive} clip={selected} />
              <RetrievalGateChart active={retrievalActive} clip={selected} />
              <TyreTempChart active={telemetryActive} clip={selected} />
              <SpeedTraceChart active={telemetryActive} clip={selected} />
              <IncidentTimelineChart active={retrievalActive} clip={selected} />
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function PipelineStage({
  num,
  label,
  active,
  children,
}: {
  num: string;
  label: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={`transition-opacity duration-300 ${active ? "opacity-100" : "opacity-25"}`}>
      <p className="mb-1.5 text-[9px] uppercase tracking-[0.16em] text-dim">
        <span className="text-red">{num}</span> &middot; {label}
      </p>
      {active ? children : <p className="text-[11px] text-dim">waiting&hellip;</p>}
    </div>
  );
}
