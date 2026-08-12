"use client";

import { useEffect, useRef, useState } from "react";
import type { ManifestEntry, ToneLabel } from "@/lib/coreApi";

const TONE_DOT: Record<ToneLabel, string> = {
  CALM: "bg-teal shadow-[0_0_8px_rgba(0,210,190,0.6)]",
  ELEVATED_AROUSAL: "bg-red shadow-[0_0_8px_rgba(225,6,0,0.7)]",
  FATIGUED: "bg-orange shadow-[0_0_8px_rgba(239,138,23,0.6)]",
};

export function ReplayTimeline({
  entries,
  toneByIncident,
  selectedId,
  onSelect,
  pitWallMode,
  totalLaps,
}: {
  entries: ManifestEntry[];
  toneByIncident: Record<string, ToneLabel | undefined>;
  selectedId: string | null;
  onSelect: (id: string) => void;
  pitWallMode: boolean;
  totalLaps: number;
}) {
  const [cursorLap, setCursorLap] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  function play() {
    if (timer.current) clearInterval(timer.current);
    setCursorLap(0);
    setPlaying(true);
    timer.current = setInterval(() => {
      setCursorLap((lap) => {
        const next = lap + 1;
        if (next >= totalLaps) {
          if (timer.current) clearInterval(timer.current);
          setPlaying(false);
          return totalLaps;
        }
        return next;
      });
    }, 90);
  }

  function stop() {
    if (timer.current) clearInterval(timer.current);
    setPlaying(false);
  }

  const pct = (lap: number) => `${(lap / totalLaps) * 100}%`;

  return (
    <div className="border border-rule bg-bg2 p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="label-red">Race Replay · Lap 1&ndash;{totalLaps}</div>
        <div className="flex items-center gap-3">
          <span className="label tabular">
            NOW <span className="text-ink">L{Math.min(cursorLap, totalLaps)}</span>
          </span>
          <button
            onClick={playing ? stop : play}
            className="border border-red/50 px-3 py-1 text-[10px] uppercase tracking-[0.14em] text-red transition hover:bg-red hover:text-ink"
          >
            {playing ? "■ Stop" : "▶ Play Replay"}
          </button>
        </div>
      </div>

      <div className="relative h-16">
        {/* track line */}
        <div className="absolute left-0 right-0 top-8 h-[2px] bg-rule" />
        {/* progress fill */}
        <div
          className="absolute left-0 top-8 h-[2px] bg-red/60 transition-[width] duration-100"
          style={{ width: pct(Math.min(cursorLap, totalLaps)) }}
        />
        {/* replay cursor */}
        <div
          className="absolute top-8 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink shadow-[0_0_10px_rgba(240,240,240,0.7)] transition-[left] duration-100"
          style={{ left: pct(Math.min(cursorLap, totalLaps)) }}
        />

        {entries.map((entry) => {
          const tone = toneByIncident[entry.incident_id];
          const isSelected = entry.incident_id === selectedId;
          const dotClass = pitWallMode
            ? "bg-ink/70"
            : tone
              ? TONE_DOT[tone]
              : "bg-dim";
          return (
            <button
              key={entry.incident_id}
              onClick={() => onSelect(entry.incident_id)}
              className="group absolute top-8 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
              style={{ left: pct(entry.lap) }}
              aria-label={`Radio pin at lap ${entry.lap}`}
            >
              <span
                className={`block h-2.5 w-2.5 rounded-full ${dotClass} ${
                  isSelected ? "ring-2 ring-ink ring-offset-2 ring-offset-bg2" : ""
                } transition group-hover:scale-125`}
              />
              <span
                className={`mt-2 whitespace-nowrap text-[9px] tabular ${
                  isSelected ? "text-ink" : "text-dim"
                }`}
              >
                L{entry.lap}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mt-6 flex items-center gap-5 border-t border-rule pt-3">
        <span className="label">Track Status</span>
        <span className="flex items-center gap-1.5 text-[10px] text-dim">
          <span className="h-1.5 w-1.5 rounded-full bg-teal" /> DRY
        </span>
        <span className="flex items-center gap-1.5 text-[10px] text-dim">
          <span className="h-1.5 w-1.5 rounded-full bg-dim" /> No incidents flagged
          outside the marked laps
        </span>
      </div>
    </div>
  );
}
