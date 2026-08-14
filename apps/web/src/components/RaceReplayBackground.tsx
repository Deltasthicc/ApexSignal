"use client";

import { useEffect, useMemo, useState } from "react";
import { CIRCUITS, type CircuitShape } from "@/data/circuits";
import {
  RACE_REPLAYS,
  type RaceReplay,
  type RaceReplayDriver,
} from "@/data/raceReplays";

const RACE_DURATION_MS = 104000;
const TRANSITION_MS = 3200;
const LAST_REPLAY_KEY = "apexsignal.last-race-replay";

type Point = { x: number; y: number };
type Pose = Point & { angle: number };

function circuitPath(circuit: CircuitShape, width: number, height: number, padding: number) {
  return circuit.points
    .map(([x, y], index) => {
      const px = padding + x * (width - padding * 2);
      const py = padding + y * (height - padding * 2);
      return `${index === 0 ? "M" : "L"}${px.toFixed(1)} ${py.toFixed(1)}`;
    })
    .join(" ");
}

function poseAt(circuit: CircuitShape, fraction: number, width = 1000, height = 700, padding = 70): Pose {
  const points = circuit.points.map(([x, y]) => ({
    x: padding + x * (width - padding * 2),
    y: padding + y * (height - padding * 2),
  }));
  const segments = points.slice(1).map((point, index) => ({
    from: points[index],
    to: point,
    length: Math.hypot(point.x - points[index].x, point.y - points[index].y),
  }));
  const totalLength = segments.reduce((sum, segment) => sum + segment.length, 0);
  let remaining = (((fraction % 1) + 1) % 1) * totalLength;
  for (const segment of segments) {
    if (remaining <= segment.length) {
      const part = segment.length === 0 ? 0 : remaining / segment.length;
      return {
        x: segment.from.x + (segment.to.x - segment.from.x) * part,
        y: segment.from.y + (segment.to.y - segment.from.y) * part,
        angle: (Math.atan2(segment.to.y - segment.from.y, segment.to.x - segment.from.x) * 180) / Math.PI,
      };
    }
    remaining -= segment.length;
  }
  return { ...points[points.length - 1], angle: 0 };
}

function chooseReplay(previousKey: string | null) {
  if (RACE_REPLAYS.length <= 1) return 0;
  const previous = RACE_REPLAYS.findIndex((replay) => replay.circuitKey === previousKey);
  const randomValue = crypto.getRandomValues(new Uint32Array(1))[0];
  if (previous < 0) return randomValue % RACE_REPLAYS.length;
  const candidate = randomValue % (RACE_REPLAYS.length - 1);
  return candidate >= previous ? candidate + 1 : candidate;
}

function rememberReplay(replay: RaceReplay) {
  try {
    sessionStorage.setItem(LAST_REPLAY_KEY, replay.circuitKey);
  } catch {
    // Rotation remains random when storage is unavailable.
  }
}

function currentOrder(replay: RaceReplay, lap: number) {
  const recorded = replay.orders[Math.min(lap, replay.orders.length - 1)] ?? [];
  const missing = replay.drivers
    .map((driver) => driver.id)
    .filter((driverId) => !recorded.includes(driverId));
  return [...recorded, ...missing];
}

function displayStatus(driver: RaceReplayDriver, lap: number) {
  if (driver.lapsCompleted === 0) {
    return driver.status === "Withdrew" ? "WD" : "DNS";
  }
  if (lap > driver.lapsCompleted) {
    const lapsDown = driver.status.match(/^\+(\d+) Laps?$/);
    return lapsDown ? `+${lapsDown[1]}L` : "OUT";
  }
  return `#${driver.number}`;
}

function RaceLayer({ replay, elapsedMs }: { replay: RaceReplay; elapsedMs: number }) {
  const circuit = CIRCUITS.find((item) => item.key === replay.circuitKey) ?? CIRCUITS[0];
  const raceProgress = Math.min(elapsedMs / RACE_DURATION_MS, 1);
  const exactLap = raceProgress * replay.totalLaps;
  const lap = Math.min(Math.floor(exactLap), replay.totalLaps);
  const lapFraction = exactLap - Math.floor(exactLap);
  const order = currentOrder(replay, lap);
  const drivers = useMemo(
    () => new Map(replay.drivers.map((driver) => [driver.id, driver])),
    [replay]
  );
  const path = useMemo(() => circuitPath(circuit, 1000, 700, 70), [circuit]);

  return (
    <div className="race-replay-layer absolute inset-0 grid grid-cols-1 gap-3 px-4 pb-6 pt-20 sm:grid-cols-[minmax(0,1fr)_220px] sm:px-7">
      <div className="relative min-w-0">
        <svg viewBox="0 0 1000 700" preserveAspectRatio="xMidYMid meet" className="h-full w-full">
          <path d={path} fill="none" stroke="#f0f0f0" strokeOpacity="0.15" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" />
          <path d={path} fill="none" stroke="#e10600" strokeOpacity="0.2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="7 11" />
          {order.map((driverId, position) => {
            const driver = drivers.get(driverId);
            if (!driver) return null;
            const active = lap <= driver.lapsCompleted && driver.lapsCompleted > 0;
            if (!active) return null;
            const spread = Math.min(0.92, position * 0.028);
            const pose = poseAt(circuit, lapFraction - spread);
            return (
              <g
                key={driver.id}
                transform={`translate(${pose.x} ${pose.y})`}
                opacity={0.56}
                data-driver={driver.code}
              >
                <circle r={position < 3 ? 7 : 5.5} fill={driver.color} stroke="#f0f0f0" strokeWidth="1.4" />
                {position < 8 ? (
                  <text x="9" y="3" fill="#f0f0f0" fontSize="10" fontWeight="700" paintOrder="stroke" stroke="#0a0a0a" strokeWidth="3">
                    {driver.code}
                  </text>
                ) : null}
              </g>
            );
          })}
        </svg>
        <div className="absolute left-1 top-1 hidden border-l border-red/70 pl-3 uppercase sm:block">
          <p className="text-[8px] tracking-[0.22em] text-red">Historical race replay · {replay.season}</p>
          <p className="mt-1 text-[13px] tracking-[0.08em] text-ink">{circuit.name}</p>
          <p className="mt-1 text-[8px] tracking-[0.1em] text-dim">{circuit.location} · {replay.eventName}</p>
          <p className="mt-2 max-w-sm text-[8px] normal-case leading-relaxed text-dim">{replay.note}</p>
        </div>
        <div className="absolute bottom-0 left-1 hidden items-baseline gap-2 border-l border-red/70 pl-3 uppercase sm:flex">
          <span className="text-[8px] tracking-[0.18em] text-dim">race lap</span>
          <span className="tabular text-lg text-ink">{Math.min(lap + 1, replay.totalLaps)}</span>
          <span className="text-[9px] text-dim">/ {replay.totalLaps}</span>
        </div>
      </div>

      <aside className="hidden self-start border border-rule/70 bg-bg/45 p-2 backdrop-blur-[2px] sm:block">
        <div className="mb-2 flex items-center justify-between border-b border-rule pb-2 text-[7px] uppercase tracking-[0.16em] text-dim">
          <span>Live order</span>
          <span>{replay.drivers.length} entries</span>
        </div>
        <ol className="space-y-[2px]">
          {order.map((driverId, position) => {
            const driver = drivers.get(driverId);
            if (!driver) return null;
            return (
              <li key={driver.id} className="grid grid-cols-[18px_8px_31px_minmax(0,1fr)_25px] items-center gap-1 text-[7px] leading-[1.35] text-dim">
                <span className="tabular text-right text-ink">{position + 1}</span>
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: driver.color, opacity: 0.72 }} />
                <span className="font-semibold text-ink">{driver.code}</span>
                <span className="truncate" title={`${driver.name} · ${driver.team}`}>{driver.team}</span>
                <span className={driver.lapsCompleted === 0 || lap > driver.lapsCompleted ? "text-red" : "text-dim"}>{displayStatus(driver, lap)}</span>
              </li>
            );
          })}
        </ol>
        <p className="mt-2 border-t border-rule pt-2 text-[6px] leading-relaxed text-dim">
          Recorded lap order · Jolpica/Ergast archive · full distance compressed
          to 104s · between-lap motion interpolated, not GPS telemetry
        </p>
      </aside>
    </div>
  );
}

export function RaceReplayBackground() {
  const [replayIndex, setReplayIndex] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [visible, setVisible] = useState(false);
  const [cycle, setCycle] = useState(0);

  useEffect(() => {
    let previous: string | null = null;
    try {
      previous = sessionStorage.getItem(LAST_REPLAY_KEY);
    } catch {
      // No persisted previous replay.
    }
    const next = chooseReplay(previous);
    rememberReplay(RACE_REPLAYS[next]);
    // queueMicrotask, not requestAnimationFrame: rAF is suspended for
    // hidden/non-composited documents (backgrounded tab, occluded window),
    // which would otherwise leave this background stuck unmounted forever.
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      setReplayIndex(next);
      setVisible(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (replayIndex === null) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      // Hold on a single static frame instead of driving the per-frame
      // timer; .race-replay-shell also disables the CSS animations.
      let cancelled = false;
      queueMicrotask(() => {
        if (!cancelled) setElapsedMs(RACE_DURATION_MS / 2);
      });
      return () => {
        cancelled = true;
      };
    }
    let frame = 0;
    let lastPaintAt = 0;
    let transitionTimer = 0;
    const startedAt = performance.now();
    const tick = (now: number) => {
      const elapsed = now - startedAt;
      if (now - lastPaintAt >= 1000 / 15) {
        setElapsedMs(Math.min(elapsed, RACE_DURATION_MS));
        lastPaintAt = now;
      }
      if (elapsed >= RACE_DURATION_MS) {
        setVisible(false);
        transitionTimer = window.setTimeout(() => {
          const currentKey = RACE_REPLAYS[replayIndex].circuitKey;
          const next = chooseReplay(currentKey);
          rememberReplay(RACE_REPLAYS[next]);
          setElapsedMs(0);
          setReplayIndex(next);
          setCycle((value) => value + 1);
        }, TRANSITION_MS);
        return;
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(frame);
      window.clearTimeout(transitionTimer);
    };
  }, [cycle, replayIndex]);

  useEffect(() => {
    if (replayIndex === null || elapsedMs !== 0) return;
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) setVisible(true);
    });
    return () => {
      cancelled = true;
    };
  }, [cycle, elapsedMs, replayIndex]);

  if (replayIndex === null) return null;
  return (
    <div aria-hidden className={`race-replay-shell pointer-events-none fixed inset-0 z-0 overflow-hidden mix-blend-screen ${visible ? "is-visible" : ""}`}>
      <RaceLayer replay={RACE_REPLAYS[replayIndex]} elapsedMs={elapsedMs} />
    </div>
  );
}
