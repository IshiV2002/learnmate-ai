import assert from "node:assert/strict";
import test from "node:test";

import {
  getNavigationDirection,
  getNavigationItem,
  getNavigationTransition,
  navigationItems,
} from "./navigation.js";

test("Home is the first and fallback destination", () => {
  assert.equal(navigationItems[0].id, "home");
  assert.equal(getNavigationItem("unknown-page").id, "home");
});

test("book transitions are limited to movement between study pages", () => {
  assert.equal(getNavigationTransition("materials", "tutor"), "book");
  assert.equal(getNavigationTransition("quiz", "recommendations"), "book");
  assert.equal(getNavigationTransition("home", "materials"), "soft");
});

test("navigation direction follows the study workflow order", () => {
  assert.equal(getNavigationDirection("materials", "quiz"), "forward");
  assert.equal(getNavigationDirection("recommendations", "tutor"), "backward");
  assert.equal(getNavigationDirection("home", "unknown-page"), "forward");
});
