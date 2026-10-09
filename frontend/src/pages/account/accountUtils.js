export function getAttemptPercentage(attempt) {
  const score = Number(attempt?.score);
  const totalQuestions = Number(attempt?.total_questions);

  if (!Number.isFinite(score) || !Number.isFinite(totalQuestions) || totalQuestions <= 0) {
    return null;
  }

  return Math.round((score / totalQuestions) * 100);
}

export function getAccountStats({
  attempts = [],
  documents = [],
  quizzes = [],
  recommendations = [],
  tutorSessions = [],
} = {}) {
  const safeAttempts = Array.isArray(attempts) ? attempts : [];
  const percentages = safeAttempts
    .map(getAttemptPercentage)
    .filter((percentage) => percentage !== null);

  return {
    materials: Array.isArray(documents) ? documents.length : 0,
    pages: (Array.isArray(documents) ? documents : []).reduce(
      (total, document) => total + (Number(document.page_count) || 0),
      0,
    ),
    generatedQuizzes: Array.isArray(quizzes) ? quizzes.length : 0,
    quizzesTaken: safeAttempts.length,
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
