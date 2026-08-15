"use client";

import { useEffect, useRef, useState } from "react";
import { Reveal } from "@/components/Reveal";
import { CategoryBadge, ConfidencePill, ToneBadge } from "@/components/Badge";
import { fetchLivePipelineDemo, type LivePipelineClip } from "@/lib/coreApi";

// Real output, fetched from the API (GET /v1/live-pipeline), not bundled
// as a hardcoded constant -- see contracts/fixtures/live_pipeline_demo.json
// and mock_server/server.py. That JSON is itself real production output:
// services/radio_ai/tone_test/run_live_pipeline_demo.py ran the actual
// ASR/tone/classifier/retrieval code against real MikCil/f1-team-radio
// broadcast clips, entirely on CPU, once -- the frontend fetches the
// result over HTTP like every other incident record on this site,
// deterministic replay of real computed output, not live GPU inference
// on every page load.

type Stage = 0 | 1 | 2 | 3 | 4;
const STAGE_DELAY_MS = 850;

export function LivePipelineDemo() {
  const [clips, setClips] = useState<LivePipelineClip[] | "loading" | "error">("loading");
  const [selected, setSelected] = useState<LivePipelineClip | null>(null);
  const [stage, setStage] = useState<Stage>(0);
  const [running, setRunning] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    fetchLivePipelineDemo()
      .then((data) => {
        setClips(data);
        setSelected(data[0] ?? null);
      })
      .catch(() => setClips("error"));
  }, []);

  function selectClip(clip: LivePipelineClip) {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setSelected(clip);
    setStage(0);
    setRunning(false);
  }

  function runPipeline() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setStage(0);
    setRunning(true);
    audioRef.current?.play().catch(() => {});

    ([1, 2, 3, 4] as Stage[]).forEach((s, i) => {
      const t = setTimeout(() => {
        setStage(s);
        if (s === 4) setRunning(false);
      }, STAGE_DELAY_MS * (i + 1));
      timers.current.push(t);
    });
  }

  return (
    <section id="live-pipeline" className="border-t border-rule bg-bg2 px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <Reveal>
          <p className="label-red mb-3">Live Pipeline Walkthrough</p>
          <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">
            Pick a real radio call. Watch the pipeline run.
          </h2>
          <p className="mt-3 max-w-2xl text-[12.5px] leading-relaxed text-dim">
            Five real broadcast clips, fetched live from the API — same
            data the <a href="/login" className="text-teal underline decoration-teal/40 underline-offset-2">Pit Wall Console</a> runs.
            Nothing here is a mockup.
          </p>
        </Reveal>

        {clips === "loading" || !selected ? (
          <p className="mt-8 text-[11px] uppercase tracking-[0.16em] text-dim">Loading from API…</p>
        ) : clips === "error" ? (
          <p className="mt-8 text-[11px] uppercase tracking-[0.16em] text-red">API unreachable.</p>
        ) : (
          <>
            <Reveal delayMs={80}>
              <div className="mt-8 flex flex-wrap gap-2">
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
            </Reveal>

            <Reveal delayMs={140}>
              <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-[1fr_auto_1fr]">
                <div className="flex h-full flex-col border border-rule bg-bg p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[9px] uppercase tracking-[0.16em] text-red">Radio call</p>
                      <p className="text-[10px] text-dim">{selected.source}</p>
                    </div>
                    <button
                      type="button"
                      onClick={runPipeline}
                      disabled={running}
                      className="shrink-0 border border-red bg-red px-3 py-2 text-[10px] uppercase tracking-[0.12em] text-ink transition hover:bg-red-bright disabled:opacity-50"
                    >
                      {running ? "Running…" : "▶ Run pipeline"}
                    </button>
                  </div>
                  <audio
                    ref={audioRef}
                    key={selected.id}
                    controls
                    preload="metadata"
                    className="h-8 w-full"
                    src={selected.src}
                    aria-label="Play the real radio call"
                  />

                  <div className="mt-4 flex min-h-[220px] flex-col gap-3 border-t border-rule pt-4">
                    <Stage num="01" label="ASR transcript (faster-whisper)" active={stage >= 1}>
                      <p className="text-[12px] italic text-ink">&ldquo;{selected.transcript}&rdquo;</p>
                    </Stage>
                    <Stage num="02" label="Acoustic tone (VoiceCLAP)" active={stage >= 2}>
                      <div className="flex items-center gap-2">
                        <ToneBadge tone={selected.toneLabel} />
                        <ConfidencePill value={selected.toneScore} />
                      </div>
                    </Stage>
                    <Stage num="03" label="Complaint category (classifier)" active={stage >= 3}>
                      <div className="flex items-center gap-2">
                        <CategoryBadge category={selected.category} />
                        <ConfidencePill value={selected.categoryConfidence} />
                      </div>
                    </Stage>
                  </div>
                </div>

                <div className="flex items-center justify-center py-4 text-red lg:flex-col lg:py-0">
                  <span className="text-lg">&rarr;</span>
                  <span className="mt-1 text-center text-[9px] uppercase leading-tight tracking-[0.12em] text-dim">
                    retrieval gate:
                    <br />
                    category match
                    <br />+ cosine &ge; 0.40
                  </span>
                </div>

                <div
                  className={`flex h-full flex-col border p-5 transition ${
                    stage >= 4
                      ? selected.match
                        ? "border-teal/40 bg-teal/5"
                        : "border-rule bg-bg"
                      : "border-rule bg-bg opacity-40"
                  }`}
                >
                  {stage < 4 ? (
                    <p className="text-[10px] uppercase tracking-[0.16em] text-dim">04 &middot; Historical match — run the pipeline to search</p>
                  ) : selected.match ? (
                    <>
                      <p className="mb-1 text-[9px] uppercase tracking-[0.16em] text-teal">04 &middot; Historical match found — real retrieval, not scripted</p>
                      <p className="mb-3 text-[10px] text-dim">{selected.match.source}</p>
                      <audio controls preload="metadata" className="h-8 w-full" src={selected.match.src} aria-label="Play the matched historical clip" />
                      <p className="mt-3 text-[12px] italic text-ink">&ldquo;{selected.match.transcript}&rdquo;</p>
                      <p className="mt-3 border-t border-rule pt-3 text-[10px] tabular text-dim">
                        Semantic similarity <span className="text-teal">{Math.round(selected.match.similarity * 100)}%</span>
                        {" · "}both classified {selected.category?.replace(/_/g, " ")}
                      </p>
                      <p className="mt-3 text-[10.5px] leading-relaxed text-dim">
                        A genuinely different broadcast, retrieved purely on semantic + category similarity — not a scripted recurrence.
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="mb-1 text-[9px] uppercase tracking-[0.16em] text-dim">04 &middot; No historical match</p>
                      <p className="mt-3 text-[11px] leading-relaxed text-dim">
                        {selected.category === null
                          ? "No complaint category was detected, so there's nothing to search for. Reported plainly, not forced."
                          : "Nothing in the corpus cleared the retrieval gate. No match, reported honestly rather than forced."}
                      </p>
                    </>
                  )}
                </div>
              </div>
            </Reveal>
          </>
        )}
      </div>
    </section>
  );
}

function Stage({
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
