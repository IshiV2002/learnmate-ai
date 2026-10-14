export function getAttemptPercentage(attempt) {
  const score = Number(attempt?.score);
  const totalQuestions = Number(attempt?.total_questions);

  if (!Number.isFinite(score) || !Number.isFinite(totalQuestions) || totalQuestions <= 0) {
    return null;
  }

  return Math.round((score / totalQuestions) * 100);
}

/**
 * Checks if a quiz attempt is successfully completed with all questions answered.
 */
export function isAttemptCompleted(attempt) {
  if (!attempt || typeof attempt !== "object") return false;

  // Explicit completion flag from API
  if (typeof attempt.is_completed === "boolean") {
    return attempt.is_completed;
  }
  if (attempt.status === "completed") {
    return true;
  }
  if (attempt.status === "incomplete") {
    return false;
  }

  // Answer count vs total questions check
  if (typeof attempt.questions_answered === "number" && typeof attempt.total_questions === "number") {
    return attempt.questions_answered >= attempt.total_questions && attempt.total_questions > 0;
  }

  // Fallback: If score and total_questions are valid finite numbers > 0
  const total = Number(attempt.total_questions);
  return Number.isFinite(total) && total > 0;
}

/**
 * Deduplicates quiz attempts by removing redundant duplicates submitted within a short window.
 */
export function deduplicateAttempts(attempts = []) {
  if (!Array.isArray(attempts)) return [];

  const seen = new Set();
  const deduped = [];

  for (const attempt of attempts) {
    if (!attempt || typeof attempt !== "object") continue;

    // Use attempt_id first
    if (attempt.attempt_id && seen.has(attempt.attempt_id)) {
      continue;
    }
    if (attempt.attempt_id) {
      seen.add(attempt.attempt_id);
    }

    // Check cluster key: quiz_id + score + 10-second timestamp bucket
    const quizId = attempt.quiz_id || "";
    const score = attempt.score !== undefined ? attempt.score : "";
    const timeMs = Date.parse(attempt.created_at || "") || 0;
    const timeBucket = Math.floor(timeMs / 10000); // 10-second bucket

    const clusterKey = `${quizId}_${score}_${timeBucket}`;
    if (seen.has(clusterKey)) {
      continue;
    }
    if (quizId) {
      seen.add(clusterKey);
    }

    deduped.push(attempt);
  }

  return deduped;
}

export function getAccountStats({
  attempts = [],
  documents = [],
  quizzes = [],
  recommendations = [],
  tutorSessions = [],
} = {}) {
  const safeAttempts = deduplicateAttempts(Array.isArray(attempts) ? attempts : []);
  const completedAttempts = safeAttempts.filter(isAttemptCompleted);
  const incompleteAttempts = safeAttempts.filter((a) => !isAttemptCompleted(a));

  const percentages = completedAttempts
    .map(getAttemptPercentage)
    .filter((percentage) => percentage !== null);

  return {
    materials: Array.isArray(documents) ? documents.length : 0,
    pages: (Array.isArray(documents) ? documents : []).reduce(
      (total, document) => total + (Number(document.page_count) || 0),
      0,
    ),
    generatedQuizzes: Array.isArray(quizzes) ? quizzes.length : 0,
    quizzesTaken: completedAttempts.length,
    completedQuizzes: completedAttempts.length,
    incompleteQuizzes: incompleteAttempts.length,
    pendingQuizzes: Math.max(
      0,
      (Array.isArray(quizzes) ? quizzes.length : 0) - completedAttempts.length,
    ),
    averageScore:
      percentages.length > 0
        ? Math.round(
            percentages.reduce((total, percentage) => total + percentage, 0) /
              percentages.length,
          )
        : null,
    tutorSessions: Array.isArray(tutorSessions) ? tutorSessions.length : 0,
    recommendations: Array.isArray(recommendations) ? recommendations.length : 0,
  };
}

export function getAccountSuggestions(stats) {
  const suggestions = [];

  if (stats.materials === 0) {
    suggestions.push({
      destination: "materials",
      eyebrow: "Start here",
      title: "Add your first course material",
      description: "Upload lecture notes or a reading before opening the study tools.",
      action: "Add material",
      icon: "materials",
    });
  } else {
    if (stats.tutorSessions === 0) {
      suggestions.push({
        destination: "tutor",
        eyebrow: "Build understanding",
        title: "Try a guided Tutor session",
        description: "Work through one difficult topic using your uploaded source.",
        action: "Open Tutor",
        icon: "tutor",
      });
    }

    if (stats.quizzesTaken === 0) {
      suggestions.push({
        destination: "quiz",
        eyebrow: "Check your recall",
        title: "Take a short practice quiz",
        description: "Turn one of your materials into questions and check what you remember.",
        action: "Create quiz",
        icon: "quiz",
      });
    }
  }

  if (stats.recommendations > 0) {
    suggestions.push({
      destination: "recommendations",
      eyebrow: "Continue studying",
      title: "Review your latest study advice",
      description: "Use your quiz feedback to decide which topic to revisit next.",
      action: "View recommendations",
      icon: "recommendations",
    });
  } else if (stats.quizzesTaken > 0) {
    suggestions.push({
      destination: "quiz",
      eyebrow: "Personalise your next step",
      title: "Complete a quiz with recommendations",
      description: "Submit another quiz and request a study plan from the results screen.",
      action: "Open quizzes",
      icon: "quiz",
    });
  }

  if (suggestions.length < 3 && stats.materials > 0) {
    suggestions.push({
      destination: "materials",
      eyebrow: "Stay organised",
      title: "Review your course library",
      description: "Search, sort or add the sources you need for your next study session.",
      action: "View materials",
      icon: "materials",
    });
  }

  return suggestions.slice(0, 3);
}

export function formatAccountDate(value, fallback = "Not available") {
  const date = new Date(value);

  if (!value || Number.isNaN(date.getTime())) {
    return fallback;
  }

  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

export function getInitials(fullName = "") {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);

  if (parts.length === 0) return "S";
  return parts.slice(0, 2).map((part) => part[0].toUpperCase()).join("");
}
