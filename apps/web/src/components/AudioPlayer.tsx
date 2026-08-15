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
          Synthesized race-radio reference
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
        Synthesized voice reading this incident&rsquo;s own transcript
        &mdash; this card is tied to an authored, fictional lap/telemetry
        narrative with no real broadcast counterpart, so real audio would
        say different words than shown above. Real broadcast clips are
        used elsewhere on this site (see the Live Pipeline Walkthrough);
        see THIRD_PARTY_NOTICES.md for the full picture.
      </p>
    </div>
  );
}
