import replayData from "./raceReplays.json";

export type RaceReplayDriver = {
  id: string;
  code: string;
  number: string;
  name: string;
  team: string;
  teamId: string;
  color: string;
  grid: number;
  finish: number;
  lapsCompleted: number;
  status: string;
};

export type RaceReplay = {
  circuitKey: string;
  season: number;
  round: number;
  eventName: string;
  date: string;
  totalLaps: number;
  note: string;
  sourceUrl: string;
  articleUrl: string;
  // Real average lap time (winner's total race time / totalLaps), used to
  // convert a real gap-to-leader in seconds (see `gaps`) into a fraction of
  // the track loop. Source: Jolpica/Ergast per-lap driver timing, not an
  // assumed constant.
  avgLapTimeS: number;
  drivers: RaceReplayDriver[];
  orders: string[][];
  // gaps[lapIndex] is a real gap-to-leader in seconds, parallel to
  // orders[lapIndex] (same driver at the same array position in both).
  gaps: number[][];
};

export const RACE_REPLAYS = replayData as RaceReplay[];
