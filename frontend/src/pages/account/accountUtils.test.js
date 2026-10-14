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
    completedQuizzes: 2,
    incompleteQuizzes: 0,
    pendingQuizzes: 1,
    averageScore: 70,
    tutorSessions: 1,
    recommendations: 2,
  });
});

test("deduplicates redundant quiz attempts and only counts fully completed quizzes", () => {
  const attempts = [
    // Duplicate pair of completed quiz
    { attempt_id: "att_1", quiz_id: "quiz_a", score: 3, total_questions: 3, is_completed: true, created_at: "2026-10-10T12:00:00.000Z" },
    { attempt_id: "att_2", quiz_id: "quiz_a", score: 3, total_questions: 3, is_completed: true, created_at: "2026-10-10T12:00:00.050Z" },
    // Incomplete quiz (answered 2 of 5 questions)
    { attempt_id: "att_3", quiz_id: "quiz_b", score: 1, total_questions: 5, questions_answered: 2, is_completed: false, created_at: "2026-10-10T13:00:00.000Z" },
  ];

  const stats = getAccountStats({
    quizzes: [{ quiz_id: "quiz_a" }, { quiz_id: "quiz_b" }, { quiz_id: "quiz_c" }],
    attempts,
  });

  // Only 1 completed quiz should be counted in quizzesTaken
  assert.equal(stats.quizzesTaken, 1);
  assert.equal(stats.completedQuizzes, 1);
  assert.equal(stats.incompleteQuizzes, 1);
  assert.equal(stats.pendingQuizzes, 2);
  assert.equal(stats.generatedQuizzes, 3);
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
