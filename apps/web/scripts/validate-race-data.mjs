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
}

if (errors.length > 0) {
  console.error(`Race replay data validation failed with ${errors.length} problem(s):\n`);
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}

console.log(
  `Race replay data OK: ${replays.length} replays, all circuitKeys resolve in the ${circuitKeys.size}-circuit atlas.`
);
