"use client";

const LINKS = [
  { href: "#pipeline", label: "how it works" },
  { href: "#sessions", label: "demo incidents" },
  { href: "#live", label: "live inspector" },
  { href: "#evidence", label: "evidence" },
  { href: "#scope", label: "scope" },
  { href: "#team", label: "team" },
];

export function TopBar() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 flex items-center justify-between border-b border-rule bg-bg/92 px-6 py-3.5 text-[10.5px] uppercase tracking-[0.16em] backdrop-blur">
      <a href="#hero" className="font-semibold text-ink">
        <span className="mr-1 text-red">&#9612;</span>ApexSignal
      </a>
      <nav className="hidden items-center gap-5 md:flex">
        {LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            className="text-dim transition hover:text-red"
          >
            {link.label}
          </a>
        ))}
        <a
          href="https://github.com/Deltasthicc/ApexSignal"
          target="_blank"
          rel="noreferrer"
          className="border border-rule px-2.5 py-1 text-dim transition hover:border-red/50 hover:text-red"
        >
          github
        </a>
      </nav>
      <a
        href="#live"
        className="border border-red/50 px-3 py-1.5 text-red transition hover:bg-red hover:text-ink md:hidden"
      >
        Live
      </a>
    </header>
  );
}
