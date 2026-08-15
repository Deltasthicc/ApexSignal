type NodeKind = "input" | "model" | "engine" | "output";

const KIND_STYLE: Record<NodeKind, { border: string; bg: string; accent: string }> = {
  input: { border: "border-dim2", bg: "bg-bg2", accent: "text-dim" },
  model: { border: "border-red/60", bg: "bg-red/5", accent: "text-red" },
  engine: { border: "border-teal/60", bg: "bg-teal/5", accent: "text-teal" },
  output: { border: "border-gold/60", bg: "bg-gold/5", accent: "text-gold" },
};

type FlowNode = {
  id: string;
  kind: NodeKind;
  x: number;
  y: number;
  w: number;
  h: number;
  title: string;
  subtitle: string;
  tag?: string;
};

const NODES: FlowNode[] = [
  {
    id: "input",
    kind: "input",
    x: 440,
    y: 20,
    w: 280,
    h: 70,
    title: "Driver Radio Call",
    subtitle: "raw audio in",
  },
  {
    id: "asr",
    kind: "model",
    x: 60,
    y: 150,
    w: 320,
    h: 84,
    title: "Speech-to-Text",
    subtitle: "distil-whisper (ASR)",
    tag: "AI model",
  },
  {
    id: "tone",
    kind: "model",
    x: 780,
    y: 150,
    w: 320,
    h: 84,
    title: "Tone / Voice Scoring",
    subtitle: "VoiceCLAP encoder",
    tag: "AI model",
  },
  {
    id: "classifier",
    kind: "model",
    x: 60,
    y: 292,
    w: 320,
    h: 84,
    title: "Complaint Classifier",
    subtitle: "embedding similarity",
    tag: "AI model",
  },
  {
    id: "merge",
    kind: "output",
    x: 440,
    y: 434,
    w: 280,
    h: 84,
    title: "Radio Analysis Output",
    subtitle: "transcript + tone + category (JSON)",
    tag: "data contract",
  },
  {
    id: "baseline",
    kind: "engine",
    x: 10,
    y: 616,
    w: 275,
    h: 92,
    title: "Own-Baseline Check",
    subtitle: "this lap vs. driver's own last 5",
  },
  {
    id: "retrieval",
    kind: "engine",
    x: 305,
    y: 616,
    w: 275,
    h: 92,
    title: "Historical Memory Match",
    subtitle: "similar past incidents",
  },
  {
    id: "leadtime",
    kind: "engine",
    x: 600,
    y: 616,
    w: 275,
    h: 92,
    title: "Lead-Time Measurement",
    subtitle: "seconds of driver warning",
  },
  {
    id: "recurrence",
    kind: "engine",
    x: 895,
    y: 616,
    w: 275,
    h: 92,
    title: "Recurrence Check",
    subtitle: '"again" / "still" wording',
  },
  {
    id: "assessment",
    kind: "output",
    x: 440,
    y: 782,
    w: 280,
    h: 84,
    title: "Incident Assessment",
    subtitle: "one verdict, evidence attached",
    tag: "data contract",
  },
  {
    id: "dashboard",
    kind: "input",
    x: 440,
    y: 924,
    w: 280,
    h: 70,
    title: "Engineer's Screen",
    subtitle: "Pit-Wall Incident Inspector",
  },
];

function center(node: FlowNode) {
  return { x: node.x + node.w / 2, y: node.y + node.h / 2 };
}
function top(node: FlowNode) {
  return { x: node.x + node.w / 2, y: node.y };
}
function bottom(node: FlowNode) {
  return { x: node.x + node.w / 2, y: node.y + node.h };
}

const byId = Object.fromEntries(NODES.map((n) => [n.id, n]));

type Edge = { from: { x: number; y: number }; to: { x: number; y: number }; label?: string };

const EDGES: Edge[] = [
  { from: bottom(byId.input), to: top(byId.asr), label: "same clip" },
  { from: bottom(byId.input), to: top(byId.tone), label: "same clip" },
  { from: bottom(byId.asr), to: top(byId.classifier), label: "transcript" },
  { from: bottom(byId.classifier), to: top(byId.merge) },
  { from: bottom(byId.tone), to: top(byId.merge) },
  { from: bottom(byId.merge), to: top(byId.baseline) },
  { from: bottom(byId.merge), to: top(byId.retrieval) },
  { from: bottom(byId.merge), to: top(byId.leadtime) },
  { from: bottom(byId.merge), to: top(byId.recurrence) },
  { from: bottom(byId.baseline), to: top(byId.assessment) },
  { from: bottom(byId.retrieval), to: top(byId.assessment) },
  { from: bottom(byId.leadtime), to: top(byId.assessment) },
  { from: bottom(byId.recurrence), to: top(byId.assessment) },
  { from: bottom(byId.assessment), to: top(byId.dashboard) },
];

function elbowPath(from: { x: number; y: number }, to: { x: number; y: number }) {
  if (Math.abs(from.x - to.x) < 2) {
    return `M ${from.x} ${from.y} L ${to.x} ${to.y}`;
  }
  const midY = from.y + (to.y - from.y) / 2;
  return `M ${from.x} ${from.y} L ${from.x} ${midY} L ${to.x} ${midY} L ${to.x} ${to.y}`;
}

const CANVAS_W = 1200;
const CANVAS_H = 1020;

export function SystemDesignFlowchart() {
  return (
    <div className="border border-rule bg-bg p-6">
      <p className="mb-1 text-[9px] uppercase tracking-[0.16em] text-red">
        Visual reference
      </p>
      <h2 className="mb-1 text-lg font-medium uppercase tracking-[0.03em] text-ink">
        Radio call &rarr; verdict, top to bottom
      </h2>
      <p className="mb-5 max-w-2xl text-[11.5px] leading-relaxed text-dim">
        One audio clip splits into two model paths, merges into a single
        structured record, runs through four independent evidence checks in
        parallel, and converges into one verdict. Nothing here is a single
        black-box score — every arrow is a real function call, mapped out in
        detail underneath the diagram.
      </p>

      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${CANVAS_W} ${CANVAS_H}`}
          className="h-auto w-full min-w-[860px]"
          role="img"
          aria-label="ApexSignal system design flowchart: radio audio flows through ASR, tone, and classifier models into a Radio Analysis Output record, which feeds four evidence-engine checks that converge into a final Incident Assessment shown on the engineer's screen."
        >
          <defs>
            <marker
              id="flow-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M0,0 L10,5 L0,10 z" fill="#4a4a4a" />
            </marker>
          </defs>

          {EDGES.map((edge, i) => (
            <g key={i}>
              <path
                d={elbowPath(edge.from, edge.to)}
                fill="none"
                stroke="#4a4a4a"
                strokeWidth="1.5"
                markerEnd="url(#flow-arrow)"
              />
              {edge.label && (
                <text
                  x={(edge.from.x + edge.to.x) / 2 + 8}
                  y={edge.from.y + (edge.to.y - edge.from.y) / 2 - 6}
                  fontSize="10"
                  fill="#767676"
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {edge.label}
                </text>
              )}
            </g>
          ))}

          {/* Evidence-engine grouping label */}
          <text
            x={600}
            y={598}
            textAnchor="middle"
            fontSize="10.5"
            letterSpacing="1.5"
            fill="#00d2be"
            fontFamily="'JetBrains Mono', monospace"
          >
            EVIDENCE ENGINE &mdash; PLAIN MATH, NOT AI, ALL FOUR RUN INDEPENDENTLY
          </text>
          <rect
            x={0}
            y={608}
            width={CANVAS_W}
            height={110}
            fill="none"
            stroke="#00d2be"
            strokeOpacity="0.25"
            strokeDasharray="4 4"
          />

          {NODES.map((node) => {
            const style = KIND_STYLE[node.kind];
            return (
              <g key={node.id}>
                <rect
                  x={node.x}
                  y={node.y}
                  width={node.w}
                  height={node.h}
                  rx={2}
                  className={`${style.bg} ${style.border}`}
                  fill="currentColor"
                  fillOpacity="0.04"
                  stroke="currentColor"
                  strokeWidth="1.25"
                  style={{
                    color:
                      node.kind === "model"
                        ? "#e10600"
                        : node.kind === "engine"
                        ? "#00d2be"
                        : node.kind === "output"
                        ? "#ffd60a"
                        : "#4a4a4a",
                  }}
                />
                <foreignObject x={node.x} y={node.y} width={node.w} height={node.h}>
                  <div className="flex h-full w-full flex-col items-center justify-center px-3 text-center">
                    {node.tag && (
                      <span className={`mb-1 text-[8px] uppercase tracking-[0.14em] ${style.accent}`}>
                        {node.tag}
                      </span>
                    )}
                    <span className="text-[12px] font-medium uppercase tracking-[0.03em] text-ink">
                      {node.title}
                    </span>
                    <span className="mt-0.5 text-[10px] text-dim">{node.subtitle}</span>
                  </div>
                </foreignObject>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="mt-5 flex flex-wrap gap-4 border-t border-rule pt-4">
        <LegendSwatch colorClass="border-dim2" label="input / screen" />
        <LegendSwatch colorClass="border-red/60" label="AI model (learned)" />
        <LegendSwatch colorClass="border-teal/60" label="evidence engine (classical math)" />
        <LegendSwatch colorClass="border-gold/60" label="data contract (JSON handoff)" />
      </div>
    </div>
  );
}

function LegendSwatch({ colorClass, label }: { colorClass: string; label: string }) {
  return (
    <span className="flex items-center gap-2 text-[10px] uppercase tracking-[0.1em] text-dim">
      <span className={`h-2.5 w-2.5 border ${colorClass}`} />
      {label}
    </span>
  );
}
