export function formatTime(seconds) {
  if (typeof seconds !== "number" || isNaN(seconds) || seconds < 0) {
    return "00:00";
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export function getQuizStats(quizzes = [], documents = []) {
  const safeQuizzes = Array.isArray(quizzes) ? quizzes : [];
  const safeDocs = Array.isArray(documents) ? documents : [];

  const totalQuestions = safeQuizzes.reduce((sum, q) => {
    const count = Number(q.total_questions || q.questions?.length || 0);
    return sum + (isNaN(count) ? 0 : count);
  }, 0);

  const distinctTopics = new Set(
    safeQuizzes
      .map((q) => (typeof q.topic === "string" ? q.topic.trim() : ""))
      .filter(Boolean),
  );

  return {
    quizzes: safeQuizzes.length,
    documents: safeDocs.length,
    questions: totalQuestions,
    topics: distinctTopics.size,
  };
}

export function getDifficultyMeta(difficulty = "mixed") {
  const diff = String(difficulty || "mixed").toLowerCase();
  switch (diff) {
    case "easy":
      return {
        label: "Easy (Foundational Recall)",
        shortLabel: "Easy",
        className: "quiz-diff-easy",
        badgeColor: "success",
      };
    case "medium":
      return {
        label: "Medium (Understanding)",
        shortLabel: "Medium",
        className: "quiz-diff-medium",
        badgeColor: "accent",
      };
    case "hard":
      return {
        label: "Hard (Application & Analysis)",
        shortLabel: "Hard",
        className: "quiz-diff-hard",
        badgeColor: "danger",
      };
    case "mixed":
    default:
      return {
        label: "Mixed (Adaptive Scope)",
        shortLabel: "Mixed",
        className: "quiz-diff-mixed",
        badgeColor: "violet",
      };
  }
}

export function getScoreTier(scorePercentage) {
  const num = Number(scorePercentage) || 0;
  if (num >= 80) {
    return {
      tier: "mastered",
      badgeClass: "quiz-tier-mastered",
      label: "🌟 High Mastery",
      description: "Strong conceptual understanding grounded in lecture material.",
    };
  }
  if (num >= 50) {
    return {
      tier: "review",
      badgeClass: "quiz-tier-review",
      label: "📖 Review Recommended",
      description: "Good foundation with a few specific knowledge gaps to reinforce.",
    };
  }
  return {
    tier: "critical",
    badgeClass: "quiz-tier-critical",
    label: "⚠️ Foundational Gaps Detected",
    description: "Remedial revision recommended with tutor guidance on cited lecture pages.",
  };
}

export function validateQuizConfig(documentId, questionType, documentIds = []) {
  const hasSingle = Boolean(documentId && typeof documentId === "string" && documentId.trim());
  const hasMultiple = Array.isArray(documentIds) && documentIds.length > 0;
  if (!hasSingle && !hasMultiple) {
    return "Please select a target course material.";
  }
  const validTypes = ["mcq", "true_false", "short_answer"];
  if (Array.isArray(questionType)) {
    if (questionType.length === 0 || !validTypes.includes(questionType[0])) {
      return "Select a question format (MCQ, True/False, or Short Answer).";
    }
  } else if (!questionType || !validTypes.includes(questionType)) {
    return "Select a question format (MCQ, True/False, or Short Answer).";
  }
  return null;
}

export function formatTrueFalseStatement(text) {
  if (typeof text !== "string") return "";
  let clean = text.trim();
  // Strip common redundant preambles
  clean = clean.replace(/^(true\s*(or|\/)\s*false\s*[:\-\—]?\s*)/i, "");
  clean = clean.replace(
    /^(state\s+whether\s+(the\s+following\s+statement\s+is\s+)?(true\s*(or|\/)\s*false|correct)\s*[:\-\—]?\s*)/i,
    "",
  );
  clean = clean.replace(/^(statement\s*[:\-\—]?\s*)/i, "");
  return clean.trim();
}

export function formatQuizDate(dateString) {
  if (!dateString) return "Recently created";
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "Recently created";
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "Recently created";
  }
}

export function estimateQuizDuration(questionCount) {
  const count = Number(questionCount) || 1;
  const minutes = Math.max(2, Math.ceil(count * 1.5));
  return `~${minutes} min${minutes > 1 ? "s" : ""}`;
}

