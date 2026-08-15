import Link from "next/link";
import type { Metadata } from "next";
import { TopBar } from "@/components/TopBar";
import { PipelineDiagram } from "@/components/dashboard/PipelineDiagram";
import { SystemDesignDiagram } from "@/components/dashboard/SystemDesignDiagram";

export const metadata: Metadata = {
  title: "ApexSignal — Technical Walkthrough",
  description:
    "How ApexSignal actually works: the pipeline stage by stage, the models, the thresholds, and where each lives in the codebase.",
};

export default function TechnicalPage() {
  return (
    <main className="min-h-screen bg-bg pb-24 pt-20">
      <TopBar />
      <div className="mx-auto max-w-7xl px-6 pt-10">
        <p className="label-red mb-2">For judges &amp; reviewers</p>
        <h1 className="mb-3 text-2xl font-medium uppercase tracking-[0.03em] text-ink">
          How this actually works
        </h1>
        <p className="mb-8 max-w-2xl text-[12.5px] leading-relaxed text-dim">
          No login required. This is the same technical breakdown the team
          uses to answer engineering questions — what happens at each stage,
          which model or piece of code does it, and which numbers are
          measured rather than guessed.
        </p>

        <div className="flex flex-col gap-6">
          <PipelineDiagram />

          <Link
            href="/technical/system-design-workflow"
            className="group flex items-center justify-between border border-teal/50 bg-teal/5 px-6 py-5 transition hover:bg-teal/10"
          >
            <span>
              <span className="mb-1 block text-[9px] uppercase tracking-[0.16em] text-teal">
                Flowchart + code map
              </span>
              <span className="block text-base font-medium uppercase tracking-[0.03em] text-ink">
                System Design Workflow
              </span>
              <span className="mt-1 block max-w-xl text-[11.5px] leading-relaxed text-dim">
                A visual, top-to-bottom diagram of the whole radio-to-verdict
                pipeline, plus every stage's exact file, function, and
                parameter — the reference to point to when explaining the
                product or answering a technical question.
              </span>
            </span>
            <span className="ml-4 shrink-0 text-teal transition group-hover:translate-x-1">
              &rarr;
            </span>
          </Link>

          <SystemDesignDiagram />
        </div>

        <p className="mt-8 text-[10.5px] uppercase tracking-[0.14em] text-dim">
          <Link href="/" className="text-teal transition hover:text-red">
            &larr; back to the live replay
          </Link>
        </p>
      </div>
    </main>
  );
}
