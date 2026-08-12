"use client";

import { useState } from "react";
import { analyzeRadio, type RadioAnalysisOutput } from "@/lib/coreApi";
import { CategoryBadge, ConfidencePill, ToneBadge } from "@/components/Badge";

export function UploadPanel() {
  const embeddedDemo = process.env.NEXT_PUBLIC_DATA_MODE === "embedded";
  const [fileName, setFileName] = useState<string | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [result, setResult] = useState<RadioAnalysisOutput | null>(null);

  async function handleFile(file: File) {
    setFileName(file.name);
    setState("loading");
    setResult(null);
    try {
      const clipId = `UPLOAD-${Date.now()}`;
      const analysis = await analyzeRadio(clipId);
      setResult(analysis);
      setState("idle");
    } catch {
      setState("error");
    }
  }

  return (
    <div className="border border-rule bg-bg2 p-5">
      <p className="label-red mb-3">Upload A Radio Clip</p>
      <label className="flex cursor-pointer items-center justify-between gap-4 border border-dashed border-rule px-4 py-3 text-xs text-dim transition hover:border-red/50 hover:text-ink">
        <span>{fileName ?? "Choose an audio file (.wav, .mp3)"}</span>
        <span className="shrink-0 border border-rule px-2 py-1 text-[10px] uppercase tracking-[0.1em]">
          Browse
        </span>
        <input
          type="file"
          accept="audio/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </label>

      <p className="mt-3 text-[10px] leading-relaxed text-dim">
        {embeddedDemo ? (
          <>Static judge mode: selecting a file exercises the complete UI with a representative contract-fixture response. The browser does not upload your file or claim to transcribe it.</>
        ) : (
          <>Demo mode: the connected backend returns a representative radio_ai-shaped analysis rather than transcribing the uploaded audio. Point <code className="text-teal">NEXT_PUBLIC_CORE_API_BASE_URL</code> at a live services/radio_ai instance for real transcription.</>
        )}
      </p>

      {state === "loading" && (
        <p className="mt-3 text-xs text-dim">Analyzing&hellip;</p>
      )}
      {state === "error" && (
        <p className="mt-3 text-xs text-red">
          Could not reach the radio analysis endpoint.
        </p>
      )}
      {result && (
        <div className="mt-4 border-t border-rule pt-4">
          <p className="text-sm text-ink">&ldquo;{result.transcript}&rdquo;</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <ToneBadge tone={result.tone_label} />
            <ConfidencePill value={result.tone_confidence} />
            <span className="text-dim">·</span>
            <CategoryBadge category={result.complaint_category} />
          </div>
        </div>
      )}
    </div>
  );
}
