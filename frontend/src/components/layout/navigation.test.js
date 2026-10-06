import assert from "node:assert/strict";
import test from "node:test";

import { getNavigationItem, navigationItems } from "./navigation.js";

test("Home is the first and fallback destination", () => {
  assert.equal(navigationItems[0].id, "home");
  assert.equal(getNavigationItem("unknown-page").id, "home");
});
