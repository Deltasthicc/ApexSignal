/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0a0a",
        bg2: "#0f0f0f",
        bg3: "#121212",
        ink: "#f0f0f0",
        dim: "#767676",
        dim2: "#4a4a4a",
        rule: "#1e1e1e",
        red: {
          DEFAULT: "#e10600",
          bright: "#ff2010",
          dim: "rgba(225,6,0,0.3)",
        },
        gold: "#ffd60a",
        teal: "#00d2be",
        orange: "#ef8a17",
        green: "#1a8754",
      },
      fontFamily: {
        mono: [
          "'JetBrains Mono'",
          "'IBM Plex Mono'",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      keyframes: {
        blink: { "50%": { opacity: 0 } },
        pulse_glow: {
          "0%, 100%": { opacity: 0.4, transform: "scale(1)" },
          "50%": { opacity: 1, transform: "scale(1.15)" },
        },
      },
      animation: {
        blink: "blink 900ms steps(1) infinite",
        pulse_glow: "pulse_glow 1.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
