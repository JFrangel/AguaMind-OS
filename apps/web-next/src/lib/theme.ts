"use client";

import { create } from "zustand";

export type Theme = "dark-blue" | "dark-purple" | "light";

const KEY = "agentos:theme";
const DEFAULT: Theme = "dark-blue";

function readInitial(): Theme {
  if (typeof window === "undefined") return DEFAULT;
  const stored = window.localStorage.getItem(KEY);
  return stored === "dark-blue" || stored === "dark-purple" || stored === "light" ? stored : DEFAULT;
}

interface ThemeState {
  current: Theme;
  init: () => void;
  set: (value: Theme) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  current: DEFAULT,
  init: () => {
    if (typeof document === "undefined") return;
    const initial = readInitial();
    document.documentElement.setAttribute("data-theme", initial);
    set({ current: initial });
  },
  set: (value) => {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", value);
      window.localStorage.setItem(KEY, value);
    }
    set({ current: value });
  },
}));
