"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

const PRIMARY_LINKS = [
  { href: "#pipeline", label: "how it works" },
  { href: "#live-pipeline", label: "live pipeline" },
  { href: "#live", label: "inspector" },
  { href: "#evidence", label: "evidence" },
  { href: "#human-loop", label: "human-in-the-loop" },
];

const TECHNICAL_LINK = { href: "/technical", label: "technical walkthrough" };

const MORE_LINKS = [
  { href: "#circuits", label: "circuits" },
  { href: "#sessions", label: "replay cases" },
  { href: "#scope", label: "scope" },
  { href: "#materials", label: "materials" },
  { href: "#team", label: "team" },
];

export function TopBar() {
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    }
    document.addEventListener("click", onClickOutside);
    return () => document.removeEventListener("click", onClickOutside);
  }, []);

  return (
    <header className="fixed inset-x-0 top-0 z-50 flex items-center justify-between border-b border-rule bg-bg/92 px-6 py-3.5 text-[10.5px] uppercase tracking-[0.16em] backdrop-blur">
      <a href="#hero" className="font-semibold text-ink">
        <span className="mr-1 text-red">&#9612;</span>ApexSignal
      </a>
      <nav className="hidden items-center gap-5 md:flex">
        {PRIMARY_LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="text-dim transition hover:text-red"
          >
            {link.label}
          </a>
        ))}

        <Link
          href={TECHNICAL_LINK.href}
          className="border border-teal/50 bg-teal/5 px-2.5 py-1 text-teal transition hover:bg-teal hover:text-bg"
        >
          {TECHNICAL_LINK.label}
        </Link>

        <div ref={moreRef} className="relative">
          <button
            type="button"
            onClick={() => setMoreOpen((v) => !v)}
            aria-expanded={moreOpen}
            className={`flex items-center gap-1 transition ${
              moreOpen ? "text-red" : "text-dim hover:text-red"
            }`}
          >
            more
            <svg
              width="8"
              height="8"
              viewBox="0 0 10 6"
              fill="none"
              className={`transition-transform ${moreOpen ? "rotate-180" : ""}`}
            >
              <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </button>
          {moreOpen && (
            <div className="absolute right-0 top-full mt-3 flex w-40 flex-col border border-rule bg-bg py-1.5 shadow-lg">
              {MORE_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMoreOpen(false)}
                  className="px-4 py-2 text-dim transition hover:bg-bg2 hover:text-red"
                >
                  {link.label}
                </a>
              ))}
            </div>
          )}
        </div>

        <a
          href="https://github.com/Deltasthicc/ApexSignal"
          target="_blank"
          rel="noreferrer"
          className="border border-rule px-2.5 py-1 text-dim transition hover:border-red/50 hover:text-red"
        >
          github
        </a>

        <Link
          href="/login"
          className="border border-gold/50 bg-gold/5 px-2.5 py-1 text-gold transition hover:bg-gold hover:text-bg"
        >
          engineer console
        </Link>
      </nav>
      <Link
        href="/login"
        className="border border-gold/50 px-3 py-1.5 text-gold transition hover:bg-gold hover:text-bg md:hidden"
      >
        Console
      </Link>
    </header>
  );
}
