const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Pin the workspace root explicitly: a stray package-lock.json one level
  // up (outside this git repo) otherwise makes Turbopack guess wrong.
  turbopack: {
    root: path.join(__dirname),
  },
  // Hugging Face's single-container image serves a static export from the
  // fixture-backed FastAPI process. Local/Vercel builds keep normal Next mode.
  ...(process.env.NEXT_OUTPUT === "export" ? { output: "export" } : {}),
};

module.exports = nextConfig;
