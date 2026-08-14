import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-bg px-6 text-center">
      <p className="label-red">404</p>
      <h1 className="text-xl font-medium uppercase tracking-[0.03em] text-ink">
        No incident at this address
      </h1>
      <p className="max-w-md text-[12.5px] leading-relaxed text-dim">
        This route is not part of the ApexSignal pit-wall replay. Head back to
        the incident inspector.
      </p>
      <Link
        href="/"
        className="mt-2 border border-rule px-4 py-2 text-[11px] uppercase tracking-[0.14em] text-ink transition-colors hover:border-red hover:text-red"
      >
        Back to pit wall
      </Link>
    </main>
  );
}
