"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-bg px-6 text-center">
      <p className="label-red">Error</p>
      <h1 className="text-xl font-medium uppercase tracking-[0.03em] text-ink">
        The pit wall lost signal
      </h1>
      <p className="max-w-md text-[12.5px] leading-relaxed text-dim">
        Something broke rendering this page. The replay data itself is
        unaffected; try reloading the inspector.
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-2 border border-rule px-4 py-2 text-[11px] uppercase tracking-[0.14em] text-ink transition-colors hover:border-red hover:text-red"
      >
        Retry
      </button>
    </main>
  );
}
