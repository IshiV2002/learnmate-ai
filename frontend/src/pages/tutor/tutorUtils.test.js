import test from "node:test";
import assert from "node:assert/strict";
import {
  getTutorStats,
  getModeMeta,
  formatSessionDate,
  validateSessionConfig,
  TUTOR_MODES,
} from "./tutorUtils.js";

test("computes tutor workspace statistics correctly", () => {
  const pastSessions = [
    {
      session_id: "s1",
      topic_focus: "Vector Space Model",
      messages: [{ role: "student" }, { role: "tutor" }],
    },
    {
      session_id: "s2",
      topic_focus: "Vector Space Model", // duplicate topic
      messages: [{ role: "student" }, { role: "tutor" }, { role: "student" }],
    },
    {
      session_id: "s3",
      topic_focus: "Inverted Index",
      messages: [{ role: "tutor" }],
    },
  ];

  const docs = [
    { document_id: "d1", original_filename: "lec1.pdf" },
    { document_id: "d2", original_filename: "lec2.pdf" },
  ];

  const stats = getTutorStats(pastSessions, docs);
  assert.strictEqual(stats.sessions, 3);
  assert.strictEqual(stats.documents, 2);
  assert.strictEqual(stats.topics, 2); // Vector Space Model + Inverted Index
  assert.strictEqual(stats.exchanges, 6);
});

test("handles empty or malformed inputs gracefully in getTutorStats", () => {
  const stats = getTutorStats(null, undefined);
  assert.strictEqual(stats.sessions, 0);
  assert.strictEqual(stats.documents, 0);
  assert.strictEqual(stats.topics, 0);
  assert.strictEqual(stats.exchanges, 0);
});

test("resolves mode metadata accurately and falls back to socratic", () => {
  const socraticMeta = getModeMeta("socratic");
  assert.strictEqual(socraticMeta.id, "socratic");
  assert.strictEqual(socraticMeta.icon, "brain");
  assert.strictEqual(socraticMeta.label, "Socratic Discovery");

  const stepMeta = getModeMeta("step_by_step");
  assert.strictEqual(stepMeta.id, "step_by_step");
  assert.strictEqual(stepMeta.icon, "ladder");

  const fallback = getModeMeta("unknown_mode");
  assert.strictEqual(fallback.id, "socratic");
});

test("formats relative session dates correctly", () => {
  const now = new Date();
  assert.strictEqual(formatSessionDate(now.toISOString()), "Just now");

  const thirtyMinsAgo = new Date(now.getTime() - 30 * 60 * 1000);
  assert.strictEqual(formatSessionDate(thirtyMinsAgo.toISOString()), "30m ago");

  const threeHoursAgo = new Date(now.getTime() - 3 * 60 * 60 * 1000);
  assert.strictEqual(formatSessionDate(threeHoursAgo.toISOString()), "3h ago");

  const yesterday = new Date(now.getTime() - 25 * 60 * 60 * 1000);
  assert.strictEqual(formatSessionDate(yesterday.toISOString()), "Yesterday");

  assert.strictEqual(formatSessionDate(null), "Recently");
  assert.strictEqual(formatSessionDate("invalid-date"), "Recently");
});

test("validates session configuration rules", () => {
  // Missing document
  const res1 = validateSessionConfig({ documentId: "", mode: "socratic" });
  assert.strictEqual(res1.isValid, false);
  assert.ok(res1.error.includes("select or upload"));

  // Invalid mode
  const res2 = validateSessionConfig({
    documentId: "doc_123",
    mode: "invalid_mode",
  });
  assert.strictEqual(res2.isValid, false);
  assert.ok(res2.error.includes("Invalid teaching mode"));

  // Valid configuration
  const res3 = validateSessionConfig({
    documentId: "doc_123",
    mode: "concept_check",
    topicFocus: "BM25 Ranking",
  });
  assert.strictEqual(res3.isValid, true);
  assert.strictEqual(res3.error, null);
});
