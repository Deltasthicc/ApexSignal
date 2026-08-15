import Link from "next/link";
import type { Metadata } from "next";
import { TopBar } from "@/components/TopBar";
import { SystemDesignFlowchart } from "@/components/dashboard/SystemDesignFlowchart";
import { WorkflowCodeMap } from "@/components/dashboard/WorkflowCodeMap";

export const metadata: Metadata = {
  title: "ApexSignal — System Design Workflow",
  description:
    "The full radio-to-verdict pipeline as a flowchart, with each stage mapped to its exact model, parameters, and source file.",
};

export default function SystemDesignWorkflowPage() {
  return (
    <main className="min-h-screen bg-bg pb-24 pt-20">
      <TopBar />
      <div className="mx-auto max-w-7xl px-6 pt-10">
        <p className="text-[10.5px] uppercase tracking-[0.14em]">
          <Link href="/technical" className="text-teal transition hover:text-red">
            &larr; technical walkthrough
          </Link>
        </p>

        <p className="label-red mb-2 mt-4">System design</p>
        <h1 className="mb-3 text-2xl font-medium uppercase tracking-[0.03em] text-ink">
          System Design Workflow
        </h1>
        <p className="mb-8 max-w-2xl text-[12.5px] leading-relaxed text-dim">
          The diagram is the fast reference for explaining the product out
          loud or to a driver-facing engineer. The breakdown underneath it is
          the same workflow with the exact file, function, and parameter
          behind every box, for anyone who wants to check the code directly.
        </p>

        <div className="flex flex-col gap-6">
          <SystemDesignFlowchart />
          <WorkflowCodeMap />
        </div>
      </div>
    </main>
  );
}
