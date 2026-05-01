import { defineStore } from "pinia";

export type Theme = "dark-blue" | "dark-purple" | "light";

const KEY = "agentos:theme";
const DEFAULT: Theme = "dark-blue";

function readInitial(): Theme {
  if (typeof window === "undefined") return DEFAULT;
  const stored = window.localStorage.getItem(KEY);
  return stored === "dark-blue" || stored === "dark-purple" || stored === "light" ? stored : DEFAULT;
}

export const useThemeStore = defineStore("theme", {
  state: () => ({ current: DEFAULT as Theme }),
  actions: {
    init() {
      if (typeof document === "undefined") return;
      const initial = readInitial();
      document.documentElement.setAttribute("data-theme", initial);
      this.current = initial;
    },
    set(value: Theme) {
      if (typeof document !== "undefined") {
        document.documentElement.setAttribute("data-theme", value);
        window.localStorage.setItem(KEY, value);
      }
      this.current = value;
    },
  },
});
