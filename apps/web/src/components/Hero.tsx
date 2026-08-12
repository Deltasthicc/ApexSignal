"use client";

import { useRef, useState } from "react";
import { Reveal } from "@/components/Reveal";
import { CircuitSignalGraphic } from "@/components/CircuitAtlas";

export function Hero({
  sessionId,
  driver,
  incidentCount,
  modeLabel,
}: {
  sessionId: string;
  driver: string;
  incidentCount: number | null;
  modeLabel: string;
}) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);

  function toggleClip() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
    } else {
      audio.play().catch(() => setPlaying(false));
    }
  }

  return (
    <section
      id="hero"
      className="relative flex min-h-screen flex-col justify-center overflow-hidden bg-bg px-6 pb-16 pt-28"
      style={{
        backgroundImage:
          "radial-gradient(circle at 1px 1px, rgba(240,240,240,0.06) 1px, transparent 0)",
        backgroundSize: "34px 34px",
      }}
    >
      <div className="mx-auto grid w-full max-w-6xl grid-cols-1 items-center gap-14 lg:grid-cols-[1.05fr_1fr]">
        <div>
          <p className="label-red mb-4">
            Problem Statement 1 &middot; The Silent Co-Driver
          </p>
          <h1 className="text-3xl font-medium uppercase leading-tight tracking-[0.03em] text-ink sm:text-4xl">
            The driver is
            <br />
            another sensor
            <span className="caret text-red">&#9612;</span>
          </h1>
          <p className="mt-5 max-w-md text-[13px] leading-relaxed text-dim">
            ApexSignal transcribes team radio, scores acoustic tone, and
            checks every driver complaint against the driver&rsquo;s own
            telemetry baseline &mdash; turning a subjective &ldquo;rear&rsquo;s
            moving&rdquo; into measured evidence, connected lap-by-lap to
            what the car actually did.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#live"
              className="border border-red bg-red px-5 py-2.5 text-[11px] uppercase tracking-[0.12em] text-ink transition hover:bg-red-bright"
            >
              &#9654; Try the live inspector
            </a>
            <a
              href="#evidence"
              className="border border-rule px-5 py-2.5 text-[11px] uppercase tracking-[0.12em] text-dim transition hover:border-red/50 hover:text-ink"
            >
              See the evidence
            </a>
            <a
              href="https://github.com/Deltasthicc/ApexSignal"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 text-[11px] uppercase tracking-[0.12em] text-dim transition hover:text-red"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
              </svg>
              GitHub
            </a>
          </div>

          <div className="mt-10 grid max-w-lg grid-cols-2 gap-x-4 gap-y-5 border-t border-rule pt-5 sm:grid-cols-4">
            <Stat k="Session" v={sessionId} />
            <Stat k="Driver" v={driver} />
            <Stat k="Incidents" v={incidentCount === null ? "—" : String(incidentCount)} />
            <Stat k="Mode" v={modeLabel === "fixture" ? "fixture demo" : modeLabel} accent />
          </div>
        </div>

        <Reveal>
          <div className="relative border border-rule bg-bg2/60 p-5">
            <Corner className="left-0 top-0 border-l border-t" />
            <Corner className="right-0 top-0 border-r border-t" />
            <Corner className="bottom-0 left-0 border-b border-l" />
            <Corner className="bottom-0 right-0 border-b border-r" />

            <button
              onClick={toggleClip}
              className={`absolute right-4 top-4 z-10 flex items-center gap-1.5 border px-2.5 py-1 text-[9px] uppercase tracking-[0.14em] transition ${
                playing
                  ? "border-red bg-red text-ink"
                  : "border-red/40 bg-bg/80 text-red hover:bg-red hover:text-ink"
              }`}
            >
              {playing ? "■ Stop" : "▶"} Team Radio
            </button>
            <audio
              ref={audioRef}
              src="https://raw.githubusercontent.com/Deltasthicc/ApexSignal/main/apps/web/public/audio/lando-norris-fp1-tuscany.mp3"
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={() => setPlaying(false)}
            />

            <CircuitSignalGraphic playing={playing} />

            <div className="mt-3 flex flex-wrap items-center justify-between gap-x-5 gap-y-2 border-t border-rule pt-3 text-[9px] uppercase tracking-[0.14em] text-dim">
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
                <Legend color="bg-red" label="Radio call" />
                <Legend color="bg-ink/60" label="Source centerline" />
                <Legend color="bg-gold" label="Deviation confirmed" />
              </div>
              <span className={playing ? "text-red" : ""}>
                {playing ? "now playing…" : "illustrative radio clip · not fixture evidence"}
              </span>
            </div>
          </div>
        </Reveal>
      </div>

      <a
        href="#pipeline"
        aria-label="Scroll to how it works"
        className="bounce-y absolute bottom-8 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2 text-dim transition hover:text-red"
      >
        <span className="text-[9px] uppercase tracking-[0.24em]">scroll</span>
        <svg width="12" height="18" viewBox="0 0 12 18" fill="none">
          <path
            d="M6 0 L6 14 M2 10 L6 14 L10 10"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </a>
    </section>
  );
}

function Stat({ k, v, accent }: { k: string; v: string; accent?: boolean }) {
  return (
    <div className="min-w-0">
      <p className="text-[9px] uppercase tracking-[0.2em] text-dim">{k}</p>
      <p
        title={v}
        className={`tabular truncate text-xs sm:text-sm ${accent ? "text-teal" : "text-ink"}`}
      >
        {v}
      </p>
    </div>
  );
}

function Corner({ className }: { className: string }) {
  return (
    <span
      aria-hidden
      className={`absolute h-3 w-3 border-red/50 ${className}`}
    />
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={`h-1.5 w-1.5 rounded-full ${color}`} />
      {label}
    </span>
  );
}
