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
  drivers: RaceReplayDriver[];
  orders: string[][];
};

export const RACE_REPLAYS = replayData as RaceReplay[];
