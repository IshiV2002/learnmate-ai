import assert from "node:assert/strict";
import test from "node:test";

import {
  formatAccountDate,
  getAccountStats,
  getAccountSuggestions,
  getAttemptPercentage,
  getInitials,
} from "./accountUtils.js";

test("summarises real account activity", () => {
  const stats = getAccountStats({
    documents: [{ page_count: 12 }, { page_count: 8 }],
    quizzes: [{}, {}, {}],
    attempts: [
      { score: 4, total_questions: 5 },
      { score: 3, total_questions: 5 },
    ],
    tutorSessions: [{}],
    recommendations: [{}, {}],
  });

  assert.deepEqual(stats, {
    materials: 2,
    pages: 20,
    generatedQuizzes: 3,
    quizzesTaken: 2,
    averageScore: 70,
    tutorSessions: 1,
    recommendations: 2,
  });
});

test("handles missing scores and creates useful new-student suggestions", () => {
  assert.equal(getAttemptPercentage({ score: 1, total_questions: 0 }), null);

  const suggestions = getAccountSuggestions(
    getAccountStats({ documents: [], attempts: [] }),
  );

  assert.equal(suggestions[0].destination, "materials");
  assert.equal(suggestions[0].action, "Add material");
});

test("formats profile display values safely", () => {
  assert.equal(getInitials("Ishini Vidanapathirana"), "IV");
  assert.equal(getInitials(""), "S");
  assert.equal(formatAccountDate(""), "Not available");
  assert.match(formatAccountDate("2026-10-09T10:00:00Z"), /2026/);
});
