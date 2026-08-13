import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://apex-signal-sigma.vercel.app"),
  title: "ApexSignal — Pit-Wall Incident Inspector",
  description:
    "Evidence-driven incident memory for the F1 pit wall: race radio, driver tone, and telemetry baseline in one screen.",
  openGraph: {
    title: "ApexSignal — The Silent Co-Driver",
    description:
      "A public, interactive incident replay connecting driver radio to telemetry evidence and historical memory.",
    type: "website",
    url: "/",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
