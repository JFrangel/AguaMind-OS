"use client";

import { useEffect } from "react";

import { useThemeStore, type Theme } from "@/lib/theme";

const OPTIONS: { value: Theme; label: string; dot: string }[] = [
  { value: "dark-blue",   label: "Slate",  dot: "#2563eb" },
  { value: "dark-purple", label: "Indigo", dot: "#7f5af0" },
  { value: "light",       label: "Ivory",  dot: "#6246ea" },
];

export function ThemeSwitch() {
  const current = useThemeStore((s) => s.current);
  const set = useThemeStore((s) => s.set);
  const init = useThemeStore((s) => s.init);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <div className="flex items-center gap-1 rounded-md border border-bg-elevated bg-bg-card p-0.5">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          aria-pressed={current === opt.value}
          title={`Tema: ${opt.label}`}
          onClick={() => set(opt.value)}
          className={`flex items-center gap-1.5 rounded px-2 py-1 text-[11px] font-medium transition-colors ${
            current === opt.value
              ? "bg-bg-elevated text-text-primary"
              : "text-text-secondary hover:text-text-primary"
          }`}
        >
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: opt.dot }} />
          <span className="hidden sm:inline">{opt.label}</span>
        </button>
      ))}
    </div>
  );
}
