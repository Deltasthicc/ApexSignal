import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

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
    <html lang="en" className={jetbrainsMono.variable}>
      <body>{children}</body>
    </html>
  );
}
