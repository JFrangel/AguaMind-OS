import type { Config } from "tailwindcss";

/**
 * Legacy Tailwind 3 preset retained for any consumer still passing it via
 * tailwind.config.*. Tailwind v4 apps consume the design tokens directly via
 * `@import "@agentos/ui/tokens.css";` — see packages/ui/tokens.css for the
 * single source of truth (dark palette + Space Grotesk/Inter/JetBrains Mono).
 */
const preset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0a0e1a",
          secondary: "#0f1629",
          card: "#111827",
          elevated: "#1e293b",
        },
        accent: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
        },
        status: {
          green: "#10b981",
          yellow: "#f59e0b",
          red: "#ef4444",
          gray: "#64748b",
        },
        text: {
          primary: "#f8fafc",
          secondary: "#94a3b8",
          muted: "#475569",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
};

export default preset;
