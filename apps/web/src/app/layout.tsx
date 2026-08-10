import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ApexSignal — Pit-Wall Incident Inspector",
  description: "Evidence-driven incident memory for the F1 pit wall.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
