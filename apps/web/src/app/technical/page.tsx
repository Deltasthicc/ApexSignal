import Link from "next/link";
import type { Metadata } from "next";
import { TopBar } from "@/components/TopBar";
import { PipelineDiagram } from "@/components/dashboard/PipelineDiagram";
import { SystemDesignDiagram } from "@/components/dashboard/SystemDesignDiagram";
import { WorkflowCodeMap } from "@/components/dashboard/WorkflowCodeMap";

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
          <WorkflowCodeMap />
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
