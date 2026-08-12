import type { RecurrenceState, ToneLabel } from "@/lib/coreApi";

const TONE_STYLE: Record<ToneLabel, string> = {
  CALM: "text-teal border-teal/40 bg-teal/5",
  ELEVATED_AROUSAL: "text-red border-red/40 bg-red/5",
  FATIGUED: "text-orange border-orange/40 bg-orange/5",
};

export function ToneBadge({ tone }: { tone: ToneLabel }) {
  return (
    <span
      className={`inline-block border px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] ${TONE_STYLE[tone]}`}
    >
      {tone.replace(/_/g, " ")}
    </span>
  );
}

const RECURRENCE_STYLE: Record<RecurrenceState, string> = {
  NONE: "text-dim border-rule",
  POSSIBLE_RECURRENCE: "text-gold border-gold/40 bg-gold/5",
  CONFIRMED_BY_RADIO: "text-red border-red/40 bg-red/5",
};

export function RecurrenceBadge({ state }: { state: RecurrenceState }) {
  return (
    <span
      className={`inline-block border px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] ${RECURRENCE_STYLE[state]}`}
    >
      {state.replace(/_/g, " ")}
    </span>
  );
}

export function CategoryBadge({ category }: { category: string | null }) {
  if (!category) {
    return (
      <span className="inline-block border border-rule px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] text-dim">
        Not a complaint
      </span>
    );
  }
  return (
    <span className="inline-block border border-ink/20 bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] text-ink">
      {category.replace(/_/g, " ")}
    </span>
  );
}

export function ConfidencePill({ value }: { value: number | null }) {
  if (value === null) return null;
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? "text-teal" : pct >= 45 ? "text-gold" : "text-dim";
  return <span className={`tabular text-[10px] ${color}`}>{pct}% conf.</span>;
}
