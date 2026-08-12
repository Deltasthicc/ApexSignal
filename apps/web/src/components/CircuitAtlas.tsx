"use client";

import { useMemo, useState } from "react";
import { CIRCUITS, type CircuitShape } from "@/data/circuits";
import { Reveal } from "@/components/Reveal";

function circuitPath(
  circuit: CircuitShape,
  width: number,
  height: number,
  padding: number
) {
  return circuit.points
    .map(([x, y], index) => {
      const px = padding + x * (width - padding * 2);
      const py = padding + y * (height - padding * 2);
      return `${index === 0 ? "M" : "L"}${px.toFixed(1)} ${py.toFixed(1)}`;
    })
    .join(" ");
}

function pointAt(circuit: CircuitShape, fraction: number, width: number, height: number, padding: number) {
  const index = Math.min(circuit.points.length - 1, Math.round((circuit.points.length - 1) * fraction));
  const [x, y] = circuit.points[index];
  return {
    x: padding + x * (width - padding * 2),
    y: padding + y * (height - padding * 2),
  };
}

export function CircuitBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden opacity-[0.055]">
      <div className="grid h-full grid-cols-3 gap-12 p-8 md:grid-cols-5">
        {CIRCUITS.slice(0, 15).map((circuit, index) => (
          <svg
            key={circuit.key}
            viewBox="0 0 160 100"
            className={`h-full min-h-20 w-full ${index % 2 ? "translate-y-8" : "-translate-y-2"}`}
          >
            <path
              d={circuitPath(circuit, 160, 100, 8)}
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
          </svg>
        ))}
      </div>
    </div>
  );
}

export function CircuitSignalGraphic({ playing = false }: { playing?: boolean }) {
  const circuit = CIRCUITS.find((item) => item.key === "Melbourne") ?? CIRCUITS[0];
  const path = useMemo(() => circuitPath(circuit, 520, 320, 42), [circuit]);
  const radioPoint = pointAt(circuit, 0.56, 520, 320, 42);

  return (
    <svg
      viewBox="0 0 520 320"
      className="w-full"
      role="img"
      aria-label="Accurate Albert Park centerline with an animated ApexSignal radio-to-evidence incident marker"
    >
      <defs>
        <filter id="map-glow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <linearGradient id="track-gradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f0f0f0" stopOpacity="0.38" />
          <stop offset="0.62" stopColor="#f0f0f0" stopOpacity="0.88" />
          <stop offset="1" stopColor="#e10600" stopOpacity="0.9" />
        </linearGradient>
      </defs>

      <g className="fill-dim" style={{ fontSize: "8px", letterSpacing: "0.16em" }}>
        <text x="20" y="22">SESSION MAP / SOURCE CENTERLINE</text>
        <text x="500" y="22" textAnchor="end">AUS · {circuit.lengthKm.toFixed(3)} KM</text>
      </g>

      <path d={path} fill="none" stroke="#161616" strokeWidth="14" strokeLinejoin="round" strokeLinecap="round" />
      <path
        d={path}
        fill="none"
        stroke="url(#track-gradient)"
        strokeWidth="1.7"
        strokeLinejoin="round"
        strokeLinecap="round"
        pathLength="1000"
        className="circuit-draw"
      />

      <circle r="3.4" fill="#e10600" filter="url(#map-glow)">
        <animateMotion dur={playing ? "5s" : "9s"} repeatCount="indefinite" path={path} />
      </circle>

      <g transform={`translate(${radioPoint.x} ${radioPoint.y})`}>
        <circle r="4.5" fill="#ffd60a" />
        <circle r="8" fill="none" stroke="#e10600" strokeWidth="1" className="radar-ping" />
        <path d="M 8 -2 L 55 -35" fill="none" stroke="#e10600" strokeWidth="1" strokeDasharray="2 4" />
        <text x="61" y="-39" className="fill-red" style={{ fontSize: "8px", letterSpacing: "0.12em" }}>RADIO · L14</text>
        <text x="61" y="-25" className="fill-ink" style={{ fontSize: "9px", letterSpacing: "0.1em" }}>EVIDENCE · L17</text>
        <text x="61" y="-12" className="fill-dim" style={{ fontSize: "8px", letterSpacing: "0.1em" }}>189.4S LEAD TIME</text>
      </g>

      <g transform="translate(24 281)">
        <text x="0" y="0" className="fill-ink" style={{ fontSize: "10px", letterSpacing: "0.12em" }}>ALBERT PARK</text>
        <text x="0" y="15" className="fill-dim" style={{ fontSize: "8px", letterSpacing: "0.1em" }}>MAP GEOMETRY: TUMFTM RACETRACK-DATABASE</text>
      </g>

      <g transform="translate(386 285)">
        {[6, 11, 18, 9, 25, 14, 20, 8].map((height, index) => (
          <rect
            key={index}
            x={index * 12}
            y={-height / 2}
            width="4"
            height={height}
            rx="2"
            fill={index === 4 ? "#e10600" : "#e1060080"}
            className="audio-bar"
            style={{ animationDelay: `${index * 70}ms`, animationDuration: playing ? "0.45s" : "1.1s" }}
          />
        ))}
      </g>
    </svg>
  );
}

function CircuitCard({ circuit, selected, onSelect }: { circuit: CircuitShape; selected: boolean; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      aria-pressed={selected}
      className={`group relative overflow-hidden border bg-bg2 text-left transition duration-300 hover:-translate-y-1 hover:border-red/60 focus:outline-none focus-visible:border-red ${selected ? "border-red/70 shadow-[0_16px_45px_rgba(0,0,0,0.45)]" : "border-rule"}`}
    >
      <div className="flex items-center justify-between px-3 pt-3 text-[8px] uppercase tracking-[0.16em] text-dim">
        <span>{circuit.code}</span>
        <span>{circuit.lengthKm.toFixed(3)} km</span>
      </div>
      <svg viewBox="0 0 220 135" className="h-32 w-full p-2 text-ink" aria-hidden>
        <path d={circuitPath(circuit, 220, 135, 12)} fill="none" stroke="#222" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
        <path
          d={circuitPath(circuit, 220, 135, 12)}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength="1000"
          className="circuit-card-line"
        />
      </svg>
      <div className="border-t border-rule px-3 py-3">
        <p className="truncate text-[10px] font-medium uppercase tracking-[0.08em] text-ink">{circuit.name}</p>
        <p className="mt-1 truncate text-[9px] text-dim">{circuit.location}</p>
      </div>
      <span className={`absolute inset-y-0 left-0 w-0.5 origin-bottom bg-red transition-transform ${selected ? "scale-y-100" : "scale-y-0 group-hover:scale-y-100"}`} />
    </button>
  );
}

export function CircuitAtlasSection() {
  const [selectedKey, setSelectedKey] = useState("Melbourne");
  const selected = CIRCUITS.find((circuit) => circuit.key === selectedKey) ?? CIRCUITS[0];

  return (
    <section id="circuits" className="relative overflow-hidden border-t border-rule bg-bg px-6 py-24">
      <div className="pointer-events-none absolute -right-28 -top-28 h-80 w-80 rounded-full bg-red/[0.035] blur-3xl" />
      <div className="relative mx-auto max-w-6xl">
        <Reveal>
          <div className="grid gap-8 lg:grid-cols-[1fr_340px] lg:items-end">
            <div>
              <p className="label-red mb-3">Circuit context · source geometry</p>
              <h2 className="text-2xl font-medium uppercase tracking-[0.03em] text-ink">Recognisable at a glance</h2>
              <p className="mt-4 max-w-2xl text-[12.5px] leading-relaxed text-dim">
                Twenty-five circuit centerlines sampled from an open motorsport geometry database—not invented SVG loops. Uniform scaling preserves every silhouette. These maps provide visual circuit context; the current judged replay remains the fixture-backed demo session.
              </p>
            </div>
            <div className="border-l border-red pl-5">
              <p className="text-4xl font-light tracking-[-0.05em] text-ink">25</p>
              <p className="mt-1 text-[9px] uppercase tracking-[0.18em] text-dim">source centerlines<br />one consistent atlas</p>
            </div>
          </div>
        </Reveal>

        <Reveal delayMs={120}>
          <div className="mt-10 grid gap-4 border border-rule bg-bg2/75 p-5 md:grid-cols-[280px_1fr] md:items-center">
            <svg viewBox="0 0 280 190" className="h-48 w-full" aria-label={`${selected.name} track map`}>
              <path d={circuitPath(selected, 280, 190, 18)} fill="none" stroke="#242424" strokeWidth="13" strokeLinecap="round" strokeLinejoin="round" />
              <path d={circuitPath(selected, 280, 190, 18)} fill="none" stroke="#f0f0f0" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" pathLength="1000" className="circuit-draw" />
              <circle r="3" fill="#e10600">
                <animateMotion dur="7s" repeatCount="indefinite" path={circuitPath(selected, 280, 190, 18)} />
              </circle>
            </svg>
            <div className="border-t border-rule pt-5 md:border-l md:border-t-0 md:pl-7 md:pt-0">
              <p className="label-red">Selected map · {selected.code}</p>
              <h3 className="mt-2 text-lg uppercase tracking-[0.05em] text-ink">{selected.name}</h3>
              <p className="mt-1 text-[10px] uppercase tracking-[0.12em] text-dim">{selected.location} · {selected.lengthKm.toFixed(3)} km centerline</p>
              <p className="mt-4 max-w-xl text-xs leading-relaxed text-dim">{selected.description}</p>
            </div>
          </div>
        </Reveal>

        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {CIRCUITS.map((circuit) => (
            <CircuitCard
              key={circuit.key}
              circuit={circuit}
              selected={circuit.key === selected.key}
              onSelect={() => setSelectedKey(circuit.key)}
            />
          ))}
        </div>

        <p className="mt-5 text-[9px] leading-relaxed tracking-[0.08em] text-dim">
          Geometry derived from TUMFTM/racetrack-database (LGPL-3.0). Centerline lengths are computed from source coordinates and may differ slightly from official homologated lap distances.
        </p>
      </div>
    </section>
  );
}
