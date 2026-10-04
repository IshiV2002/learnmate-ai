/**
 * Utility functions for the AI Tutor Agent interface.
 */

/**
 * Calculate high-level summary statistics from sessions and documents.
 *
 * @param {Array} pastSessions - Array of past tutor session objects.
 * @param {Array} documents - Array of uploaded document objects.
 * @returns {{ sessions: number, documents: number, topics: number, exchanges: number }}
 */
export function getTutorStats(pastSessions = [], documents = []) {
  const safeSessions = Array.isArray(pastSessions) ? pastSessions : [];
  const safeDocs = Array.isArray(documents) ? documents : [];

  const uniqueTopics = new Set();
  let totalExchanges = 0;

  for (const session of safeSessions) {
    if (session.topic_focus && typeof session.topic_focus === "string") {
      uniqueTopics.add(session.topic_focus.trim().toLowerCase());
    }
    if (Array.isArray(session.messages)) {
      totalExchanges += session.messages.length;
    }
  }

  return {
    sessions: safeSessions.length,
    documents: safeDocs.length,
    topics: uniqueTopics.size,
    exchanges: totalExchanges,
  };
}

/**
 * Teaching mode metadata mapping.
 */
export const TUTOR_MODES = {
  socratic: {
    id: "socratic",
    label: "Socratic Discovery",
    shortLabel: "Socratic",
    icon: "brain",
    kicker: "Guided Inquiry",
    description:
      "Guides with probing, thoughtful questions to help you discover principles from lecture evidence.",
    badgeClass: "tutor-mode-badge-socratic",
  },
  step_by_step: {
    id: "step_by_step",
    label: "Step-by-Step Breakdown",
    shortLabel: "Step-by-Step",
    icon: "ladder",
    kicker: "Structured Analysis",
    description:
      "Deconstructs complex concepts into structured numbered steps with intuitive analogies.",
    badgeClass: "tutor-mode-badge-step",
  },
  concept_check: {
    id: "concept_check",
    label: "Concept Check Challenge",
    shortLabel: "Concept Check",
    icon: "target",
    kicker: "Active Retrieval",
    description:
      "Delivers a concise recap followed by targeted comprehension challenges to solidify recall.",
    badgeClass: "tutor-mode-badge-check",
  },
};

/**
 * Resolve metadata for a teaching mode.
 *
 * @param {string} mode - The mode identifier.
 * @returns {object} The mode configuration object.
 */
export function getModeMeta(mode = "socratic") {
  return TUTOR_MODES[mode] || TUTOR_MODES.socratic;
}

/**
 * Format timestamp into human-readable relative or short date format.
 *
 * @param {string|number|Date} dateValue - Date to format.
 * @returns {string} Formatted string.
 */
export function formatSessionDate(dateValue) {
  if (!dateValue) return "Recently";
  const date = new Date(dateValue);
  if (isNaN(date.getTime())) return "Recently";

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

/**
 * Validate session configuration before initiating.
 *
 * @param {{ documentId: string, mode: string, topicFocus?: string }} config
 * @returns {{ isValid: boolean, error: string | null }}
 */
export function validateSessionConfig(config) {
  if (!config || typeof config !== "object") {
    return { isValid: false, error: "Invalid session configuration." };
  }

  if (!config.documentId || typeof config.documentId !== "string" || !config.documentId.trim()) {
    return {
      isValid: false,
      error: "Please select or upload a course lecture document first.",
    };
  }

  const validModes = Object.keys(TUTOR_MODES);
  if (config.mode && !validModes.includes(config.mode)) {
    return {
      isValid: false,
      error: `Invalid teaching mode selected. Must be one of: ${validModes.join(", ")}.`,
    };
  }

  return { isValid: true, error: null };
}
