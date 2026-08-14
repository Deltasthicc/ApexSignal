#!/usr/bin/env node
// Guards against the exact class of bug that shipped the 2021 Hungarian GP
// on the Albert Park map: a replay whose circuitKey has no matching atlas
// entry falls back silently to CIRCUITS[0] at render time (see
// RaceReplayBackground.tsx) instead of failing loudly. Run on every build
// and in CI so a future data-entry mismatch fails fast instead of shipping.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(here, "..", "src", "data");

function readCircuitKeys() {
  const source = readFileSync(path.join(dataDir, "circuits.ts"), "utf-8");
  const match = source.match(/CIRCUITS: CircuitShape\[\] = (\[.*\]);/s);
  if (!match) throw new Error("Could not locate CIRCUITS array in circuits.ts");
  const circuits = JSON.parse(match[1]);
  return new Set(circuits.map((c) => c.key));
}

function readReplays() {
  return JSON.parse(readFileSync(path.join(dataDir, "raceReplays.json"), "utf-8"));
}

const errors = [];

const circuitKeys = readCircuitKeys();
const replays = readReplays();

if (replays.length === 0) {
  errors.push("raceReplays.json is empty");
}

for (const replay of replays) {
  const label = `${replay.circuitKey ?? "?"} (${replay.eventName ?? "unknown event"})`;

  if (!circuitKeys.has(replay.circuitKey)) {
    errors.push(
      `${label}: circuitKey "${replay.circuitKey}" has no entry in circuits.ts -- ` +
        `it will silently render on ${[...circuitKeys][0]} instead.`
    );
    continue;
  }

  const driverIds = new Set(replay.drivers.map((d) => d.id));
  if (driverIds.size !== replay.drivers.length) {
    errors.push(`${label}: duplicate driver id in drivers[]`);
  }

  replay.orders.forEach((order, lapIndex) => {
    for (const driverId of order) {
      if (!driverIds.has(driverId)) {
        errors.push(`${label}: orders[${lapIndex}] references unknown driver id "${driverId}"`);
      }
    }
  });

  if (!Number.isFinite(replay.totalLaps) || replay.totalLaps <= 0) {
    errors.push(`${label}: totalLaps must be a positive number, got ${replay.totalLaps}`);
  }

  // Real gap-to-leader data (see scripts/build_race_replays.ps1): without
  // it the background silently falls back to fixed uniform spacing, which
  // is exactly the "every car equidistant" bug this field exists to fix.
  if (!Number.isFinite(replay.avgLapTimeS) || replay.avgLapTimeS <= 0) {
    errors.push(`${label}: avgLapTimeS must be a positive number, got ${replay.avgLapTimeS}`);
  }
  if (!Array.isArray(replay.gaps) || replay.gaps.length !== replay.orders.length) {
    errors.push(
      `${label}: gaps must be an array parallel to orders (expected length ${replay.orders.length}, got ${Array.isArray(replay.gaps) ? replay.gaps.length : typeof replay.gaps})`
    );
  } else {
    replay.gaps.forEach((lapGaps, lapIndex) => {
      const expectedLength = replay.orders[lapIndex].length;
      if (!Array.isArray(lapGaps) || lapGaps.length !== expectedLength) {
        errors.push(
          `${label}: gaps[${lapIndex}] length ${Array.isArray(lapGaps) ? lapGaps.length : typeof lapGaps} does not match orders[${lapIndex}] length ${expectedLength}`
        );
      }
    });
  }
}

if (errors.length > 0) {
  console.error(`Race replay data validation failed with ${errors.length} problem(s):\n`);
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}

console.log(
  `Race replay data OK: ${replays.length} replays, all circuitKeys resolve in the ${circuitKeys.size}-circuit atlas.`
);
