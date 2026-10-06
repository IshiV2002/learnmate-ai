export const THEME_STORAGE_KEY = "learnmate_theme";

export function normalizeTheme(value) {
  return value === "dark" ? "dark" : "light";
}

export function getNextTheme(theme) {
  return normalizeTheme(theme) === "dark" ? "light" : "dark";
}
