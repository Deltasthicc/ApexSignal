"use client";

// Demo-only client-side gate: no backend auth, any credentials proceed.
// Deliberately not dressed up as real security -- says so on the page,
// same "don't claim what isn't there" rule the rest of this project
// holds itself to. Sets a sessionStorage flag the dashboard checks for.

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    sessionStorage.setItem("apexsignal_engineer_session", "1");
    setTimeout(() => router.push("/dashboard"), 500);
  }

  return (
    <main
      className="flex min-h-screen items-center justify-center bg-bg px-6"
      style={{
        backgroundImage:
          "radial-gradient(circle at 1px 1px, rgba(240,240,240,0.06) 1px, transparent 0)",
        backgroundSize: "34px 34px",
      }}
    >
      <div className="w-full max-w-sm border border-rule bg-bg2/80 p-8 backdrop-blur">
        <p className="mb-1 text-center text-[10px] uppercase tracking-[0.2em] text-red">
          <span className="mr-1">&#9612;</span>ApexSignal
        </p>
        <h1 className="mb-1 text-center text-lg font-medium uppercase tracking-[0.03em] text-ink">
          Pit Wall Access
        </h1>
        <p className="mb-8 text-center text-[11px] text-dim">
          Race Engineer Console &middot; REFERENCE_REPLAY_2026
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-[9px] uppercase tracking-[0.16em] text-dim">
              Engineer ID
            </span>
            <input
              type="text"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="engineer@podiumfinish.team"
              className="border border-rule bg-bg px-3 py-2.5 text-[13px] text-ink outline-none transition focus:border-red/50"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-[9px] uppercase tracking-[0.16em] text-dim">
              Access code
            </span>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••"
              className="border border-rule bg-bg px-3 py-2.5 text-[13px] text-ink outline-none transition focus:border-red/50"
            />
          </label>

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 border border-red bg-red px-4 py-2.5 text-[11px] uppercase tracking-[0.14em] text-ink transition hover:bg-red-bright disabled:opacity-60"
          >
            {submitting ? "Authenticating…" : "Sign In to Console"}
          </button>
        </form>

        <p className="mt-6 border-t border-rule pt-4 text-center text-[9.5px] leading-relaxed text-dim">
          Demo console &mdash; any credentials proceed. No backend
          authentication runs here; this gate exists for the presentation
          flow, not as a security claim.
        </p>
      </div>
    </main>
  );
}
