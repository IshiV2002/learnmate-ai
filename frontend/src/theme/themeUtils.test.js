import assert from "node:assert/strict";
import test from "node:test";

import { getNextTheme, normalizeTheme } from "./themeUtils.js";

test("light is the safe default theme", () => {
  assert.equal(normalizeTheme(null), "light");
  assert.equal(normalizeTheme("unexpected"), "light");
});

test("theme toggle switches between light and dark", () => {
  assert.equal(getNextTheme("light"), "dark");
  assert.equal(getNextTheme("dark"), "light");
});
