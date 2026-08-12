"use client";

import { useEffect, useState } from "react";

/**
 * Radio clips are not bundled in this environment (data/audio/ ships only
 * a .gitkeep -- see contracts/api_contract.md). Rather than fake a
 * playback bar over silence, this plays the transcript through the
 * browser's own speech synthesis and says so plainly. If a real .wav for
 * this incident ever shows up at `src`, that plays instead, unlabeled.
 */
export function AudioPlayer({
  src,
  transcript,
}: {
  src: string;
  transcript: string;
}) {
  const [hasRealAudio, setHasRealAudio] = useState<boolean | null>(null);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setHasRealAudio(null);
    fetch(src, { method: "HEAD" })
      .then((res) => !cancelled && setHasRealAudio(res.ok))
      .catch(() => !cancelled && setHasRealAudio(false));
    return () => {
      cancelled = true;
    };
  }, [src]);

  function speak() {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(transcript);
    utter.rate = 1.02;
    utter.onstart = () => setSpeaking(true);
    utter.onend = () => setSpeaking(false);
    utter.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utter);
  }

  function stop() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }

  if (hasRealAudio) {
    return (
      <audio controls className="h-8 w-full" src={src}>
        <track kind="captions" />
      </audio>
    );
  }

  return (
    <div className="flex items-center gap-3 border border-rule bg-bg2 px-3 py-2">
      <button
        onClick={speaking ? stop : speak}
        className="flex h-7 w-7 shrink-0 items-center justify-center border border-red/50 text-red transition hover:bg-red hover:text-ink"
        aria-label={speaking ? "Stop" : "Play"}
      >
        {speaking ? "■" : "▶"}
      </button>
      <p className="text-[10px] leading-relaxed text-dim">
        No broadcast clip bundled in this environment.{" "}
        <span className="text-ink">Synthesized playback of the transcript.</span>
      </p>
    </div>
  );
}
