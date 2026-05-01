type Theme = "dark-blue" | "dark-purple" | "light";

const KEY = "agentos:theme";
const DEFAULT: Theme = "dark-blue";

function readInitial(): Theme {
  if (typeof window === "undefined") return DEFAULT;
  const stored = window.localStorage.getItem(KEY);
  if (stored === "dark-blue" || stored === "dark-purple" || stored === "light") {
    return stored;
  }
  return DEFAULT;
}

class ThemeStore {
  current = $state<Theme>(DEFAULT);

  init(): void {
    if (typeof document === "undefined") return;
    this.current = readInitial();
    document.documentElement.setAttribute("data-theme", this.current);
  }

  set(value: Theme): void {
    this.current = value;
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", value);
      window.localStorage.setItem(KEY, value);
    }
  }
}

export const theme = new ThemeStore();
export type { Theme };
