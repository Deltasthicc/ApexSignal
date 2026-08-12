/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Hugging Face's single-container image serves a static export from the
  // fixture-backed FastAPI process. Local/Vercel builds keep normal Next mode.
  ...(process.env.NEXT_OUTPUT === "export" ? { output: "export" } : {}),
};

module.exports = nextConfig;
