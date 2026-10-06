import { useEffect, useState } from "react";

import {
  getNextTheme,
  normalizeTheme,
  THEME_STORAGE_KEY,
} from "./themeUtils.js";

function readSavedTheme() {
  try {
    return normalizeTheme(window.localStorage.getItem(THEME_STORAGE_KEY));
  } catch {
    return "light";
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(readSavedTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;

    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // The selected theme still applies when storage is unavailable.
    }
  }, [theme]);

  return {
    theme,
    toggleTheme: () => setTheme((currentTheme) => getNextTheme(currentTheme)),
  };
}
