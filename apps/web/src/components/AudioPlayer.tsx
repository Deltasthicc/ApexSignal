export function AudioPlayer({
  src,
  clipLabel,
}: {
  src: string;
  clipLabel: string;
}) {
  return (
    <div className="border border-rule bg-bg2 px-3 py-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[9px] uppercase tracking-[0.16em] text-red">
          Authentic race-radio reference
        </p>
        <p className="text-[9px] text-dim">{clipLabel}</p>
      </div>
      <audio
        controls
        preload="metadata"
        className="h-8 w-full"
        src={src}
        aria-label={`Play ${clipLabel}`}
      />
      <p className="mt-2 text-[9px] leading-relaxed text-dim">
        Reference team-radio audio, no synthesized voice. This clip
        demonstrates the audio input; it is not presented as the recording
        for this contract replay incident. See THIRD_PARTY_NOTICES.md for
        its sourcing.
      </p>
    </div>
  );
}
