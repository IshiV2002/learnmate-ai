import assert from "node:assert/strict";
import test from "node:test";

import {
  formatTime,
  getDifficultyMeta,
  getQuizStats,
  getScoreTier,
  validateQuizConfig,
} from "./quizUtils.js";

test("formats seconds into MM:SS format correctly", () => {
  assert.equal(formatTime(0), "00:00");
  assert.equal(formatTime(45), "00:45");
  assert.equal(formatTime(65), "01:05");
  assert.equal(formatTime(3600), "60:00");
  assert.equal(formatTime(-5), "00:00");
  assert.equal(formatTime(null), "00:00");
});

test("computes quiz library statistics accurately", () => {
  const sampleQuizzes = [
    { total_questions: 5, topic: "Vector Space Model" },
    { total_questions: 8, topic: "Inverted Index" },
    { total_questions: 5, topic: "Vector Space Model" },
  ];
  const sampleDocs = [{ document_id: "doc-1" }, { document_id: "doc-2" }];

  const stats = getQuizStats(sampleQuizzes, sampleDocs);
  assert.equal(stats.quizzes, 3);
  assert.equal(stats.documents, 2);
  assert.equal(stats.questions, 18);
  assert.equal(stats.topics, 2);
});

test("resolves difficulty tier metadata and styling classes", () => {
  assert.equal(getDifficultyMeta("easy").shortLabel, "Easy");
  assert.equal(getDifficultyMeta("medium").shortLabel, "Medium");
  assert.equal(getDifficultyMeta("hard").shortLabel, "Hard");
  assert.equal(getDifficultyMeta("mixed").shortLabel, "Mixed");
  assert.equal(getDifficultyMeta("unknown").shortLabel, "Mixed");
});

test("classifies student score tiers properly", () => {
  assert.equal(getScoreTier(90).tier, "mastered");
  assert.equal(getScoreTier(75).tier, "review");
  assert.equal(getScoreTier(40).tier, "critical");
});

test("validates quiz generation form configurations", () => {
  assert.equal(validateQuizConfig("", "mcq"), "Please select a target lecture PDF.");
  assert.equal(
    validateQuizConfig("doc-1", ""),
    "Select a question format (MCQ, True/False, or Short Answer).",
  );
  assert.equal(validateQuizConfig("doc-1", "invalid_type"), "Select a question format (MCQ, True/False, or Short Answer).");
  assert.equal(validateQuizConfig("doc-1", "mcq"), null);
  assert.equal(validateQuizConfig("doc-1", ["true_false"]), null);
});
