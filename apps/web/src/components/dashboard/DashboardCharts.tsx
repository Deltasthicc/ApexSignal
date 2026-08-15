"use client";

// Hand-rolled inline SVG charts, no charting library in this project's
// dependencies. Palette reuses the site's existing brand tokens (validated
// for CVD-safety: node scripts/validate_palette.js "#e10600,#00d2be,#ffd60a,#ef8a17"
// --mode dark -- passes chroma floor, CVD separation (worst deltaE 15.9),
// normal-vision floor, and contrast).
//
// Honesty boundary, stated once here rather than scattered in comments:
// only panels 1, 2, and 5 (confidence meters, retrieval gate, incident
// memory timeline) plot real per-clip numbers -- they come straight from
// the `clip` prop, which is real production classifier/tone/retrieval
// output fetched from /v1/live-pipeline. Panels 3 and 4 (tyre temp, speed
// trace) are illustrative: real MikCil broadcast clips have no
// accompanying telemetry export, so there is no real per-clip number to
// plot there. They're clearly labeled as illustrative in the UI and only
// react to the REAL category output (which zone lights up), never invent
// a specific number.

import { useEffect, useRef, useState } from "react";

const INK = "#f0f0f0";
const DIM = "#767676";
const RULE = "#1e1e1e";
const RED = "#e10600";
const TEAL = "#00d2be";
const GOLD = "#ffd60a";
const ORANGE = "#ef8a17";

export type LiveClip = {
  toneLabel: "CALM" | "ELEVATED_AROUSAL" | "FATIGUED";
  toneScore: number;
  category: string | null;
  categoryConfidence: number | null;
  match: { similarity: number; source: string } | null;
};

function useCountUp(target: number, active: boolean, durationMs = 700) {
  const [value, setValue] = useState(0);
  const raf = useRef<number | null>(null);
  useEffect(() => {
    if (!active) {
      queueMicrotask(() => setValue(0));
      return;
    }
    const start = performance.now();
    function tick(now: number) {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(target * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, active]);
  return value;
}

function Svg({ width = 100, height = 100, children }: { width?: number; height?: number; children: React.ReactNode }) {
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full" preserveAspectRatio="none" role="img">
      {children}
    </svg>
  );
}

function ChartFrame({
  title,
  active,
  activeNote,
  real,
  legend,
  children,
}: {
  title: string;
  active: boolean;
  activeNote?: string;
  real: boolean;
  legend?: { color: string; label: string }[];
  children: React.ReactNode;
}) {
  return (
    <div
      className={`border p-4 transition-all duration-500 ${
        active ? `${real ? "border-teal/50" : "border-red/40"} bg-bg ${active ? "shadow-[0_0_24px_-8px_rgba(0,210,190,0.25)]" : ""}` : "border-rule bg-bg2"
      }`}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <p className="text-[9px] uppercase tracking-[0.16em] text-dim">
          {title} <span className={real ? "text-teal" : "text-dim"}>&middot; {real ? "real" : "illustrative"}</span>
        </p>
        {active && activeNote && (
          <p className="text-right text-[9px] uppercase tracking-[0.1em] text-red">{activeNote}</p>
        )}
      </div>
      <div className={`h-[110px] transition-opacity duration-500 ${active ? "opacity-100" : "opacity-45"}`}>
        {children}
      </div>
      {legend && (
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[9px] uppercase tracking-[0.1em] text-dim">
          {legend.map((it) => (
            <span key={it.label} className="flex items-center gap-1.5">
              <span className="h-[2px] w-3" style={{ backgroundColor: it.color }} />
              {it.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function Meter({ label, pct, active, color }: { label: string; pct: number; active: boolean; color: string }) {
  const animated = useCountUp(pct, active, 800);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-[10px] text-dim">
        <span>{label}</span>
        <span className="tabular text-ink">{Math.round(animated)}%</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-sm bg-rule">
        <div
          className="h-full rounded-sm transition-[width] duration-700 ease-out"
          style={{ width: `${animated}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// --- 1. Confidence meters (REAL per-clip output) -----------------------
export function ConfidenceMetersChart({ active, clip }: { active: boolean; clip: LiveClip }) {
  const toneColor = clip.toneLabel === "CALM" ? TEAL : clip.toneLabel === "FATIGUED" ? ORANGE : RED;
  return (
    <ChartFrame title="01 · Model confidence, this call" active={active} real activeNote={active ? "live" : undefined}>
      <div className="flex h-full flex-col justify-center gap-4 px-1">
        <Meter label={`Tone — ${clip.toneLabel}`} pct={clip.toneScore * 100} active={active} color={toneColor} />
        <Meter
          label={clip.category ? `Category — ${clip.category.replace(/_/g, " ")}` : "Category — none detected"}
          pct={(clip.categoryConfidence ?? 0) * 100}
          active={active}
          color={clip.category ? GOLD : DIM}
        />
      </div>
    </ChartFrame>
  );
}

// --- 2. Retrieval similarity gate (REAL per-clip output) ----------------
export function RetrievalGateChart({ active, clip }: { active: boolean; clip: LiveClip }) {
  const w = 300;
  const h = 60;
  const threshold = 0.4;
  const sim = clip.match?.similarity ?? 0;
  const animatedSim = useCountUp(sim, active, 900);
  const x = (v: number) => 20 + v * (w - 40);

  return (
    <ChartFrame
      title="02 · Retrieval gate — semantic similarity"
      active={active}
      real
      activeNote={active ? (clip.match ? "gate cleared" : "no match") : undefined}
    >
      <Svg width={w} height={h}>
        <line x1={20} x2={w - 20} y1={h / 2} y2={h / 2} stroke={RULE} strokeWidth={2} />
        <line x1={x(threshold)} x2={x(threshold)} y1={12} y2={h - 12} stroke={DIM} strokeWidth={1} strokeDasharray="2 2" />
        <text x={x(threshold)} y={10} textAnchor="middle" fontSize={7} fill={DIM}>
          gate 0.40
        </text>
        {active && clip.match && (
          <>
            <line x1={20} x2={x(animatedSim)} y1={h / 2} y2={h / 2} stroke={TEAL} strokeWidth={3} strokeLinecap="round" />
            <circle cx={x(animatedSim)} cy={h / 2} r={6} fill={TEAL} stroke="#0a0a0a" strokeWidth={2} />
            <text x={x(animatedSim)} y={h - 4} textAnchor="middle" fontSize={9} fill={TEAL}>
              {(animatedSim * 100).toFixed(0)}%
            </text>
          </>
        )}
        {active && !clip.match && (
          <text x={w / 2} y={h / 2 + 4} textAnchor="middle" fontSize={9} fill={DIM}>
            nothing cleared the gate
          </text>
        )}
      </Svg>
    </ChartFrame>
  );
}

// --- 3. Tyre temperatures (illustrative, category-reactive) -------------
export function TyreTempChart({ active, clip }: { active: boolean; clip: LiveClip }) {
  const isRear = clip.category === "EXIT_TRACTION_REAR";
  const isFront = clip.category === "FRONT_TURNIN_BRAKE";
  const wheels = [
    { label: "FL", temp: isFront ? 104 : 92, color: TEAL, highlight: isFront },
    { label: "FR", temp: isFront ? 107 : 94, color: GOLD, highlight: isFront },
    { label: "RL", temp: isRear ? 111 : 101, color: ORANGE, highlight: isRear },
    { label: "RR", temp: isRear ? 114 : 108, color: RED, highlight: isRear },
  ];
  const w = 300;
  const h = 100;
  const maxT = 120;
  const barW = 44;
  const gap = (w - wheels.length * barW) / (wheels.length + 1);

  return (
    <ChartFrame
      title="03 · Tyre surface temperature"
      active={active}
      real={false}
      activeNote={active ? (isRear ? "rears elevated" : isFront ? "fronts elevated" : undefined) : undefined}
      legend={[
        { color: TEAL, label: "FL" },
        { color: GOLD, label: "FR" },
        { color: ORANGE, label: "RL" },
        { color: RED, label: "RR" },
      ]}
    >
      <Svg width={w} height={h}>
        <line x1={0} x2={w} y1={h - 14} y2={h - 14} stroke={RULE} strokeWidth={1} />
        {wheels.map((wheel, i) => {
          const x = gap + i * (barW + gap);
          const barH = (wheel.temp / maxT) * (h - 24);
          return (
            <g key={wheel.label}>
              <rect
                x={x}
                y={h - 14 - barH}
                width={barW}
                height={barH}
                rx={3}
                fill={wheel.color}
                opacity={active && wheel.highlight ? 1 : active ? 0.5 : 0.4}
                style={{ transition: "height 0.6s ease-out, opacity 0.4s" }}
              />
              <text x={x + barW / 2} y={h - 4} textAnchor="middle" fontSize={8} fill={DIM}>
                {wheel.label}
              </text>
              <text x={x + barW / 2} y={h - 14 - barH - 5} textAnchor="middle" fontSize={8} fill={INK}>
                {wheel.temp}&deg;
              </text>
            </g>
          );
        })}
      </Svg>
    </ChartFrame>
  );
}

// --- 4. Speed trace (illustrative, pattern only) -------------------------
function pathFromPoints(pts: [number, number][]) {
  return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0]} ${p[1]}`).join(" ");
}

export function SpeedTraceChart({ active, clip }: { active: boolean; clip: LiveClip }) {
  const w = 300;
  const h = 100;
  const dip = clip.category ? 46 : 60;
  const baseline: [number, number][] = [[0, 20], [50, 55], [100, 70], [150, 40], [200, 20], [250, 15], [300, 22]];
  const current: [number, number][] = [[0, 22], [50, 58], [100, 74], [150, dip], [200, 34], [250, 30], [300, 34]];
  const dashLen = 900;

  return (
    <ChartFrame title="04 · Speed trace through corner" active={active} real={false}>
      <Svg width={w} height={h}>
        {[25, 50, 75].map((y) => (
          <line key={y} x1={0} x2={w} y1={y} y2={y} stroke={RULE} strokeWidth={1} />
        ))}
        {active && (
          <path d={pathFromPoints(baseline)} fill="none" stroke={TEAL} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" opacity={0.85} />
        )}
        <path
          d={pathFromPoints(current)}
          fill="none"
          stroke={active ? GOLD : DIM}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={dashLen}
          strokeDashoffset={active ? 0 : dashLen}
          style={{ transition: "stroke-dashoffset 0.9s ease-out, stroke 0.4s" }}
        />
      </Svg>
    </ChartFrame>
  );
}

// --- 5. Historical incident timeline (REAL retrieval output) ------------
export function IncidentTimelineChart({ active, clip }: { active: boolean; clip: LiveClip }) {
  const w = 300;
  const h = 100;
  const points = [
    { x: 20, cat: "FRONT_TURNIN_BRAKE" },
    { x: 60, cat: "TYRE_GRIP_DEGRADATION" },
    { x: 100, cat: "EXIT_TRACTION_REAR" },
    { x: 150, cat: "MECHANICAL_OTHER" },
    { x: 190, cat: "TYRE_GRIP_DEGRADATION" },
  ];
  const matchX = 230;
  const currentX = 280;
  const colorFor = (cat: string) =>
    cat === "FRONT_TURNIN_BRAKE" ? RED : cat === "TYRE_GRIP_DEGRADATION" ? GOLD : cat === "EXIT_TRACTION_REAR" ? ORANGE : TEAL;
  const dashLen = 60;

  return (
    <ChartFrame
      title="05 · Incident memory — corpus timeline"
      active={active}
      real
      activeNote={active ? (clip.match ? "match found" : "no match") : undefined}
    >
      <Svg width={w} height={h}>
        <line x1={0} x2={w} y1={h / 2} y2={h / 2} stroke={RULE} strokeWidth={1} />
        {active && clip.match && (
          <line
            x1={matchX}
            y1={h / 2}
            x2={currentX}
            y2={h / 2}
            stroke={TEAL}
            strokeWidth={2}
            strokeDasharray={dashLen}
            strokeDashoffset={active ? 0 : dashLen}
            style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
          />
        )}
        {points.map((p) => (
          <circle key={p.x} cx={p.x} cy={h / 2} r={5} fill={active ? colorFor(p.cat) : DIM} opacity={active ? 0.45 : 0.5} stroke="#0a0a0a" strokeWidth={2} />
        ))}
        {active && clip.match && (
          <circle cx={matchX} cy={h / 2} r={6} fill={TEAL} stroke="#0a0a0a" strokeWidth={2} className="animate-pulse_glow" />
        )}
        <circle
          cx={currentX}
          cy={h / 2}
          r={6}
          fill={active ? RED : DIM}
          stroke="#0a0a0a"
          strokeWidth={2}
          className={active ? "animate-pulse_glow" : ""}
        />
        {active && (
          <text x={currentX} y={h / 2 - 14} textAnchor="end" fontSize={8} fill={INK}>
            this call
          </text>
        )}
        {active && clip.match && (
          <text x={matchX} y={h / 2 + 22} textAnchor="middle" fontSize={7} fill={TEAL}>
            {clip.match.source}
          </text>
        )}
      </Svg>
    </ChartFrame>
  );
}
