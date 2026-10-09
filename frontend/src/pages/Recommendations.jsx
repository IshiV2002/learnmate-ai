import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import {
  analyzeQuizSubmission,
  getDocuments,
  getStudentRecommendations,
  getTutorHandoff,
} from "../services/api.js";
import "./Recommendations.css";

// Built-in preset quizzes for sandbox testing and grading demonstrations
const PRESET_QUIZZES = [
  {
    id: "preset_ir_basics",
    title: "Information Retrieval Fundamentals",
    questions: [
      {
        question_id: "q1_inverted_index",
        topic: "Inverted Index Construction",
        difficulty: "easy",
        question_text:
          "What is the primary architectural purpose of an Inverted Index in search systems?",
        selected_answer: "Mapping keywords to the list of documents containing them",
        correct_answer: "Mapping keywords to the list of documents containing them",
        is_correct: true,
      },
      {
        question_id: "q2_tfidf",
        topic: "TF-IDF Weighting",
        difficulty: "medium",
        question_text:
          "In the TF-IDF weighting scheme, what does high Inverse Document Frequency (IDF) signify?",
        selected_answer: "The term occurs very frequently across the entire corpus",
        correct_answer: "The term is rare and highly discriminative across the collection",
        is_correct: false,
      },
      {
        question_id: "q3_cosine",
        topic: "Cosine Similarity Calculation",
        difficulty: "hard",
        question_text:
          "Why is Cosine Similarity favored over Euclidean distance in the Vector Space Model for text?",
        selected_answer: "It is length-normalized and evaluates directional orientation of document vectors",
        correct_answer: "It is length-normalized and evaluates directional orientation of document vectors",
        is_correct: true,
      },
      {
        question_id: "q4_evaluation",
        topic: "Evaluation Metrics (P@K & MAP)",
        difficulty: "medium",
        question_text:
          "How does Mean Average Precision (MAP) differ from Precision at Rank K (P@K)?",
        selected_answer: "MAP rewards relevant documents returned earlier in the ranked list across multiple queries",
        correct_answer: "MAP rewards relevant documents returned earlier in the ranked list across multiple queries",
        is_correct: true,
      },
      {
        question_id: "q5_bm25",
        topic: "BM25 Probabilistic Ranking",
        difficulty: "hard",
        question_text:
          "What critical saturation mechanism does BM25 introduce to prevent term repetition abuse?",
        selected_answer: "Document length exponential scaling",
        correct_answer: "Term frequency saturation parameterized by k1",
        is_correct: false,
      },
    ],
  },
  {
    id: "preset_vector_space",
    title: "Vector Space Models & Semantic Embeddings",
    questions: [
      {
        question_id: "vsm_q1",
        topic: "Vector Space Model Foundations",
        difficulty: "easy",
        question_text:
          "In a standard Vector Space Model, how are documents and queries represented?",
        selected_answer: "As multi-dimensional vectors where each dimension corresponds to a vocabulary term",
        correct_answer: "As multi-dimensional vectors where each dimension corresponds to a vocabulary term",
        is_correct: true,
      },
      {
        question_id: "vsm_q2",
        topic: "Dense Semantic Embeddings",
        difficulty: "medium",
        question_text:
          "What fundamental limitation of lexical sparse search do dense transformer embeddings solve?",
        selected_answer: "Vocabulary mismatch and synonymy by projecting semantically similar concepts together",
        correct_answer: "Vocabulary mismatch and synonymy by projecting semantically similar concepts together",
        is_correct: true,
      },
      {
        question_id: "vsm_q3",
        topic: "ChromaDB & Approximate Nearest Neighbors",
        difficulty: "hard",
        question_text:
          "What algorithmic family does ChromaDB rely upon to rapidly retrieve top-K semantic chunks?",
        selected_answer: "Linear brute-force cosine distance search",
        correct_answer: "Hierarchical Navigable Small World (HNSW) graphs",
        is_correct: false,
      },
    ],
  },
];

// Curated interactive concept drills for instant on-the-spot recovery
const CONCEPT_DRILLS = {
  "Inverted Index": {
    question: "In an Inverted Index, what does each entry in a postings list record?",
    options: [
      "The document ID and term frequency where the keyword occurs",
      "A complete duplicate copy of the entire raw document text",
      "The student's search history and query timestamps",
      "An alphabetical list of discardable stop words",
    ],
    correctIndex: 0,
    explanation: "Postings lists record document IDs (and term frequencies/positions) for each indexed word, allowing near-instant intersection during search.",
  },
  "TF-IDF": {
    question: "Why does Inverse Document Frequency (IDF) penalize words like 'the' or 'is'?",
    options: [
      "Because they appear across almost every document, offering very low discriminative value",
      "Because stop words always have fewer than four characters",
      "Because IDF is inversely proportional to document file size in megabytes",
      "Because common words cause RAM overflows during vector multiplication",
    ],
    correctIndex: 0,
    explanation: "IDF lowers the weight of omnipresent words that appear across all documents, elevating discriminative domain keywords.",
  },
  "Cosine": {
    question: "Why is Cosine Similarity favored over Euclidean distance for comparing text documents?",
    options: [
      "It measures the angle between vectors, normalizing for differing document lengths",
      "It automatically converts negative term weights into positive values",
      "It only functions when document vectors have exactly 10 dimensions",
      "It ignores the vocabulary of the document collection entirely",
    ],
    correctIndex: 0,
    explanation: "Cosine similarity measures vector orientation rather than magnitude, ensuring a 10-page chapter isn't unfairly distant from a 1-page summary.",
  },
  "BM25": {
    question: "What key advantage does the BM25 formula introduce regarding term frequency?",
    options: [
      "It applies term frequency saturation so extreme repetitions don't dominate the score",
      "It eliminates the need for an inverted index",
      "It computes similarity strictly in binary 0 or 1 integers",
      "It ignores document length completely",
    ],
    correctIndex: 0,
    explanation: "BM25's k1 parameter caps the marginal gain of repeated keywords, preventing keyword stuffing from distorting rank relevance.",
  },
  "Evaluation": {
    question: "What does Precision at Rank K (P@K) measure in Information Retrieval evaluation?",
    options: [
      "The proportion of retrieved documents in the top K results that are relevant",
      "The exact latency in milliseconds required to rank K documents",
      "The percentage of all relevant documents in the entire corpus retrieved",
      "The position where the first irrelevant document occurred",
    ],
    correctIndex: 0,
    explanation: "Precision@K computes (relevant docs in top K) / K, reflecting what fraction of the immediate results are actually useful.",
  },
  "ChromaDB": {
    question: "Why do modern vector databases like ChromaDB use HNSW indexing?",
    options: [
      "To perform sub-linear Approximate Nearest Neighbor search across high-dimensional vectors",
      "To convert vector embeddings into plain SQL text tables",
      "To bypass GPU requirements by saving embeddings as JPEG images",
      "To replace dense embeddings with simple keyword matching",
    ],
    correctIndex: 0,
    explanation: "HNSW (Hierarchical Navigable Small World) allows sub-linear graph traversal to find nearest vectors in milliseconds.",
  },
};

function getDrillForTopic(topic, gapExplanation) {
  for (const [key, drill] of Object.entries(CONCEPT_DRILLS)) {
    if (topic.toLowerCase().includes(key.toLowerCase()) || key.toLowerCase().includes(topic.toLowerCase())) {
      return drill;
    }
  }
  return {
    question: `Key Concept Check for "${topic}": Which statement best describes the fundamental principle?`,
    options: [
      `It establishes structured representations to optimize retrieval relevance and ranking accuracy.`,
      `It discards all document text to minimize database storage consumption.`,
      `It operates solely on unindexed raw strings without semantic weighting.`,
    ],
    correctIndex: 0,
    explanation: gapExplanation || `Mastering ${topic} ensures search and generation agents correctly retrieve and rank passages.`,
  };
}

export default function Recommendations({
  initialSubmission,
  initialRecommendation,
  onLaunchTutor = null,
  onNavigate = null,
  onToggleTheme,
  theme = "light",
}) {
  const { user } = useAuth();
  const studentId = user?.user_id || "guest_student";

  // Data States
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(
    initialSubmission?.document_id || ""
  );
  const [studentHistory, setStudentHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Preset & Simulator States
  const [selectedPreset, setSelectedPreset] = useState(PRESET_QUIZZES[0]);
  const [activeQuestions, setActiveQuestions] = useState(
    initialSubmission?.questions || PRESET_QUIZZES[0].questions
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recommendationResult, setRecommendationResult] = useState(
    initialRecommendation || null
  );
  const [errorMessage, setErrorMessage] = useState("");
  const [showTutorModal, setShowTutorModal] = useState(false);
  const [copiedContract, setCopiedContract] = useState(false);

  // Navigation tab
  const [activeTab, setActiveTab] = useState(
    initialRecommendation || initialSubmission ? "dashboard" : "dashboard"
  );

  // Gamification & Psychological States
  const [completedMissions, setCompletedMissions] = useState(() => {
    try {
      const saved = localStorage.getItem("learnmate_completed_missions");
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });
  const [recoveredGaps, setRecoveredGaps] = useState({});
  const [activeDrills, setActiveDrills] = useState({});
  const [digestFilter, setDigestFilter] = useState("all"); // 'all' | 'missed' | 'correct'
  const [digestTopicFilter, setDigestTopicFilter] = useState("all");
  const [digestSearchQuery, setDigestSearchQuery] = useState("");
  const [digestViewMode, setDigestViewMode] = useState("detailed"); // 'detailed' | 'compact'
  const [expandedDigestCards, setExpandedDigestCards] = useState({});

  useEffect(() => {
    loadDocuments();
    loadStudentHistory();

    if (initialRecommendation) {
      setRecommendationResult(initialRecommendation);
      setActiveTab("dashboard");
    } else if (initialSubmission) {
      analyzeExternalSubmission(initialSubmission);
    }
  }, [initialRecommendation, initialSubmission]);

  async function loadStudentHistory() {
    if (!studentId || studentId === "guest_student") return;
    setIsLoadingHistory(true);
    try {
      const history = await getStudentRecommendations(studentId);
      if (Array.isArray(history) && history.length > 0) {
        setStudentHistory(history);
        if (!initialRecommendation && !initialSubmission && !recommendationResult) {
          setRecommendationResult(history[0]);
          setActiveTab("dashboard");
        }
      }
    } catch {
      // Historical recommendations optional for unauthenticated or first-time students
    } finally {
      setIsLoadingHistory(false);
    }
  }

  async function loadDocuments() {
    try {
      const docs = await getDocuments();
      setDocuments(docs || []);
      if (docs && docs.length > 0 && !selectedDocId) {
        setSelectedDocId(docs[0].document_id);
      }
    } catch {
      setDocuments([]);
    }
  }

  async function analyzeExternalSubmission(submission) {
    setIsSubmitting(true);
    setErrorMessage("");
    try {
      const res = await analyzeQuizSubmission(submission);
      setRecommendationResult(res);
      setActiveTab("dashboard");
      loadStudentHistory();
    } catch (err) {
      setErrorMessage(err?.message || "Failed to analyze quiz submission.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handlePresetChange(presetId) {
    const preset =
      PRESET_QUIZZES.find((p) => p.id === presetId) || PRESET_QUIZZES[0];
    setSelectedPreset(preset);
    setActiveQuestions(JSON.parse(JSON.stringify(preset.questions)));
  }

  function toggleQuestionCorrectness(qIndex) {
    const updated = [...activeQuestions];
    updated[qIndex].is_correct = !updated[qIndex].is_correct;
    if (updated[qIndex].is_correct) {
      updated[qIndex].selected_answer = updated[qIndex].correct_answer;
    } else {
      updated[qIndex].selected_answer = "Incorrect / Suboptimal Answer Choice";
    }
    setActiveQuestions(updated);
  }

  async function handleRunAnalysis() {
    setIsSubmitting(true);
    setErrorMessage("");
    try {
      const payload = {
        student_id: studentId,
        document_id: selectedDocId || (documents[0]?.document_id || "doc_demo"),
        quiz_attempt_id: "sim_" + Date.now(),
        questions: activeQuestions,
      };
      const res = await analyzeQuizSubmission(payload);
      setRecommendationResult(res);
      setActiveTab("dashboard");
      loadStudentHistory();
    } catch (err) {
      setErrorMessage(
        err?.message ||
          "Failed to generate recommendations. Please ensure the backend is running."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleCopyJson() {
    if (!recommendationResult?.tutor_handoff) return;
    navigator.clipboard.writeText(
      JSON.stringify(recommendationResult.tutor_handoff, null, 2)
    );
    setCopiedContract(true);
    setTimeout(() => setCopiedContract(false), 2000);
  }

  // Psychological & Gamification Calculations
  const scorePct = recommendationResult?.score_percentage || 0;

  // Assessment Question Digest (Breakdown of correct vs. incorrect)
  const questionsDigest = useMemo(() => {
    if (
      recommendationResult?.questions_digest &&
      recommendationResult.questions_digest.length > 0
    ) {
      return recommendationResult.questions_digest;
    }
    if (Array.isArray(activeQuestions) && activeQuestions.length > 0) {
      return activeQuestions.map((q) => ({
        question_id: q.question_id,
        topic: q.topic,
        difficulty: q.difficulty || "medium",
        question_text: q.question_text,
        selected_answer: q.selected_answer,
        correct_answer: q.correct_answer,
        is_correct: q.is_correct,
        explanation:
          q.explanation ||
          (q.is_correct
            ? "You answered this correctly."
            : "Review this concept to master the material."),
      }));
    }
    return [];
  }, [recommendationResult, activeQuestions]);

  // Derived filter stats and available topics
  const missedCount = useMemo(
    () => questionsDigest.filter((q) => !q.is_correct).length,
    [questionsDigest]
  );
  const correctCount = useMemo(
    () => questionsDigest.filter((q) => q.is_correct).length,
    [questionsDigest]
  );

  const digestTopics = useMemo(() => {
    const topicMap = new Map();
    questionsDigest.forEach((q) => {
      const top = q.topic || "General Concept";
      topicMap.set(top, (topicMap.get(top) || 0) + 1);
    });
    return Array.from(topicMap.entries()).map(([topic, count]) => ({
      topic,
      count,
    }));
  }, [questionsDigest]);

  const hasActiveDigestFilters =
    digestFilter !== "all" ||
    digestTopicFilter !== "all" ||
    digestSearchQuery.trim() !== "";

  const filteredDigest = useMemo(() => {
    return questionsDigest.filter((q) => {
      // 1. Status Filter
      if (digestFilter === "missed" && q.is_correct) return false;
      if (digestFilter === "correct" && !q.is_correct) return false;

      // 2. Topic Filter
      if (digestTopicFilter !== "all" && q.topic !== digestTopicFilter) {
        return false;
      }

      // 3. Search Query Filter
      if (digestSearchQuery.trim()) {
        const query = digestSearchQuery.toLowerCase().trim();
        const textMatch = (q.question_text || "").toLowerCase().includes(query);
        const topicMatch = (q.topic || "").toLowerCase().includes(query);
        const ansMatch = (q.selected_answer || "").toLowerCase().includes(query);
        const correctAnsMatch = (q.correct_answer || "").toLowerCase().includes(query);
        const explMatch = (q.explanation || "").toLowerCase().includes(query);
        if (!textMatch && !topicMatch && !ansMatch && !correctAnsMatch && !explMatch) {
          return false;
        }
      }

      return true;
    });
  }, [questionsDigest, digestFilter, digestTopicFilter, digestSearchQuery]);

  function handleResetDigestFilters() {
    setDigestFilter("all");
    setDigestTopicFilter("all");
    setDigestSearchQuery("");
  }

  function toggleDigestCardExpansion(qId) {
    setExpandedDigestCards((prev) => ({
      ...prev,
      [qId]: !prev[qId],
    }));
  }

  function handleAskTutorAboutQuestion(question) {
    const questionHandoff = {
      ...(recommendationResult?.tutor_handoff || {}),
      target_topics: [question.topic || "Targeted Concept Review"],
      suggested_opening_prompt: `Hi! In my recent quiz on "${question.topic || "Course Material"}", I missed this question: "${question.question_text}". I selected "${question.selected_answer}", but the correct answer is "${question.correct_answer}". Can you explain where my reasoning went off-track and how to master this concept?`,
      pedagogical_instruction: `Guide the student through understanding why "${question.correct_answer}" is correct instead of their selection "${question.selected_answer}" on the topic of "${question.topic}". Acknowledge their attempt with positive reinforcement and ask a Socratic guiding question.`,
    };

    if (onLaunchTutor) {
      onLaunchTutor(questionHandoff);
    } else {
      setShowTutorModal(true);
    }
  }

  // Mastered & Weak Topic Categorization (Cognitive Balance Matrix)
  const masteredTopics = useMemo(() => {
    if (
      recommendationResult?.mastered_topics &&
      recommendationResult.mastered_topics.length > 0
    ) {
      return recommendationResult.mastered_topics;
    }
    return (recommendationResult?.topic_mastery || [])
      .filter((tm) => tm.accuracy_percentage >= 70)
      .map((tm) => tm.topic);
  }, [recommendationResult]);

  const weakTopics = useMemo(() => {
    if (
      recommendationResult?.weak_topics &&
      recommendationResult.weak_topics.length > 0
    ) {
      return recommendationResult.weak_topics;
    }
    return (recommendationResult?.topic_mastery || [])
      .filter((tm) => tm.accuracy_percentage < 70)
      .map((tm) => tm.topic);
  }, [recommendationResult]);

  const scholarMeta = useMemo(() => {
    if (scorePct >= 85) {
      return {
        tier: "Grandmaster Scholar",
        className: "tier-grandmaster",
        icon: "🏆",
        message: "Exam Ready! Your conceptual foundation is rock-solid. Keep up the high retention!",
        boostPercent: 5,
        statusLabel: "Mastery: Elite",
      };
    }
    if (scorePct >= 70) {
      return {
        tier: "Proficient Challenger",
        className: "tier-challenger",
        icon: "⚔️",
        message: "Strong performance! You have a solid grasp. Polish the Quick Win below to hit 90%+.",
        boostPercent: 12,
        statusLabel: "Mastery: Proficient",
      };
    }
    if (scorePct >= 50) {
      return {
        tier: "Apprentice Explorer",
        className: "tier-explorer",
        icon: "🛡️",
        message: "Great baseline! Targeting your weak spots with the AI Coach will yield rapid score gains.",
        boostPercent: 18,
        statusLabel: "Mastery: Developing",
      };
    }
    return {
      tier: "Rising Scholar",
      className: "tier-rising",
      icon: "🚀",
      message: "High growth potential! Every expert was once a beginner. Start with the 5-minute Quick Win below.",
      boostPercent: 25,
      statusLabel: "Mastery: High Growth",
    };
  }, [scorePct]);

  // High-ROI Quick Win Selection (Lowest severity or medium difficulty gap)
  const quickWin = useMemo(() => {
    if (!recommendationResult?.knowledge_gaps?.length) return null;
    const gaps = recommendationResult.knowledge_gaps;
    return (
      gaps.find((g) => g.severity?.toLowerCase() === "low") ||
      gaps.find((g) => g.severity?.toLowerCase() === "medium") ||
      gaps[0]
    );
  }, [recommendationResult]);

  // Interactive Study Quest Missions
  const studyMissions = useMemo(() => {
    if (!recommendationResult) return [];
    const missions = [];

    if (quickWin) {
      missions.push({
        id: "mission-quickwin",
        type: "⚡ Quick Win",
        title: `Master ${quickWin.topic}`,
        desc: quickWin.explanation || "Highest return on investment for your study session.",
        time: 4,
        actionType: "drill",
        gap: quickWin,
      });
    }

    if (recommendationResult.tutor_handoff?.suggested_opening_prompt) {
      missions.push({
        id: "mission-tutor",
        type: "💬 AI Tutor",
        title: `Socratic Review on ${recommendationResult.tutor_handoff.target_topics?.slice(0, 2).join(", ") || "Key Concepts"}`,
        desc: recommendationResult.tutor_handoff.suggested_opening_prompt,
        time: 5,
        actionType: "tutor",
      });
    }

    (recommendationResult.action_items || []).forEach((act, idx) => {
      missions.push({
        id: `mission-act-${idx}`,
        type: act.action_type || "📖 Remediation",
        title: act.title,
        desc: act.description,
        time: act.estimated_minutes || 5,
        actionType: act.action_type?.toLowerCase().includes("tutor") ? "tutor" : "material",
      });
    });

    return missions;
  }, [recommendationResult, quickWin]);

  const currentRecId = recommendationResult?.recommendation_id || "default";
  const completedList = completedMissions[currentRecId] || [];
  const completedCount = completedList.length;
  const questPercent =
    studyMissions.length > 0
      ? Math.round((completedCount / studyMissions.length) * 100)
      : 0;

  function toggleMission(missionId) {
    setCompletedMissions((prev) => {
      const existing = prev[currentRecId] || [];
      const updated = existing.includes(missionId)
        ? existing.filter((id) => id !== missionId)
        : [...existing, missionId];
      const next = { ...prev, [currentRecId]: updated };
      try {
        localStorage.setItem("learnmate_completed_missions", JSON.stringify(next));
      } catch {}
      return next;
    });
  }

  // Micro-Drill Handlers
  function toggleDrill(gapId) {
    setActiveDrills((prev) => ({
      ...prev,
      [gapId]: prev[gapId] ? null : { selectedOpt: null, isSubmitted: false, isCorrect: false },
    }));
  }

  function handleSelectDrillOption(gapId, optIdx) {
    setActiveDrills((prev) => ({
      ...prev,
      [gapId]: { ...prev[gapId], selectedOpt: optIdx },
    }));
  }

  function handleSubmitDrill(gapId, drill) {
    const drillState = activeDrills[gapId];
    if (!drillState || drillState.selectedOpt === null) return;
    const isCorrect = drillState.selectedOpt === drill.correctIndex;
    setActiveDrills((prev) => ({
      ...prev,
      [gapId]: { ...prev[gapId], isSubmitted: true, isCorrect },
    }));

    if (isCorrect) {
      setRecoveredGaps((prev) => ({ ...prev, [gapId]: true }));
      // Automatically check off corresponding quick-win mission if applicable
      if (quickWin?.gap_id === gapId) {
        toggleMission("mission-quickwin");
      }
    }
  }

  // Circular gauge calculations
  const gaugeRadius = 64;
  const gaugeCircumference = 2 * Math.PI * gaugeRadius;
  const strokeDashoffset =
    gaugeCircumference - (gaugeCircumference * scorePct) / 100;
  const gaugeColor =
    scorePct >= 80
      ? "var(--rec-emerald)"
      : scorePct >= 50
      ? "var(--rec-amber)"
      : "var(--rec-rose)";

  return (
    <div className="recommendations-page" data-rec-theme={theme}>
      {/* Hero Header Section */}
      <section className="rec-hero">
        <div className="rec-hero-header-bar">
          <div className="rec-badge">
            <span className="rec-pulse-dot" />
            AI Study Coach & Knowledge Diagnostics
          </div>

          <button
            type="button"
            className="rec-theme-toggle"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Toggle ${theme === "dark" ? "Light" : "Dark"} Mode`}
          >
            <span className="rec-theme-icon">
              {theme === "dark" ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </span>
            <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
          </button>
        </div>

        <h1 className="rec-hero-title">Your Personalized Revision Guide</h1>
        <p className="rec-hero-subtitle">
          Diagnose knowledge gaps from assessment attempts, identify high-yield Quick Wins,
          and unlock tailored 1-on-1 Socratic tutoring sessions.
        </p>

        <nav className="rec-nav-bar" aria-label="Recommendation Modes">
          <button
            type="button"
            className={`rec-nav-btn ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <span>📊</span>
            <span>Study Hub & Diagnostics</span>
            {recommendationResult && (
              <span className="rec-status-indicator">Active</span>
            )}
          </button>
          <button
            type="button"
            className={`rec-nav-btn ${activeTab === "take_quiz" ? "active" : ""}`}
            onClick={() => setActiveTab("take_quiz")}
          >
            <span>🧪</span>
            <span>Diagnostic Sandbox</span>
          </button>
        </nav>
      </section>

      {/* Error Alert Box */}
      {errorMessage && (
        <div className="rec-alert" role="alert">
          <span>⚠️</span>
          <div>{errorMessage}</div>
        </div>
      )}

      {/* VIEW 1: Assessment History Switcher (Shown on Dashboard when history exists) */}
      {activeTab === "dashboard" && studentHistory.length > 0 && (
        <div className="rec-history-bar">
          <span className="rec-history-label">📂 Your Assessments:</span>
          <div className="rec-history-chips">
            {studentHistory.map((rec, idx) => {
              const isCurrent =
                rec.recommendation_id === recommendationResult?.recommendation_id;
              const chipColor =
                rec.score_percentage >= 80
                  ? "var(--rec-emerald)"
                  : rec.score_percentage >= 50
                  ? "var(--rec-amber)"
                  : "var(--rec-rose)";
              return (
                <button
                  key={rec.recommendation_id}
                  type="button"
                  className={`rec-history-chip ${isCurrent ? "active" : ""}`}
                  onClick={() => {
                    setRecommendationResult(rec);
                    setActiveTab("dashboard");
                  }}
                >
                  <span>🎯 Attempt #{studentHistory.length - idx}:</span>
                  <strong style={{ color: chipColor }}>
                    {rec.score_percentage}%
                  </strong>
                  <span className="rec-chip-date">
                    ({rec.overall_score}/{rec.total_questions})
                  </span>
                </button>
              );
            })}
            <button
              type="button"
              className="rec-history-chip sandbox-chip"
              onClick={() => setActiveTab("take_quiz")}
            >
              <span>🧪 Custom Sandbox</span>
            </button>
          </div>
        </div>
      )}

      {/* VIEW 2: Empty Launchpad State (When no assessment has been taken yet) */}
      {activeTab === "dashboard" && !recommendationResult && (
        <div className="rec-launchpad-card">
          <div className="rec-launchpad-icon">🎓</div>
          <h2 className="rec-launchpad-title">Welcome to Your AI Knowledge Coach</h2>
          <p className="rec-launchpad-desc">
            Your personal coach analyzes your lecture quizzes, detects underlying
            misconceptions, maps them to cited lecture slides, and generates
            interactive study quests with 1-click AI Tutoring.
          </p>
          <div className="rec-launchpad-actions">
            {onNavigate && (
              <button
                type="button"
                className="rec-quick-win-btn-primary"
                onClick={() => onNavigate("quiz")}
              >
                <span>🎯</span>
                <span>Take a Quiz to Diagnose Gaps</span>
              </button>
            )}
            <button
              type="button"
              className="rec-quick-win-btn-secondary"
              onClick={() => {
                analyzeExternalSubmission({
                  student_id: studentId,
                  document_id: selectedDocId || (documents[0]?.document_id || "doc_demo"),
                  quiz_attempt_id: "demo_diagnostic_run",
                  questions: PRESET_QUIZZES[0].questions,
                });
              }}
            >
              <span>⚡</span>
              <span>Try Instant Sample Diagnostic</span>
            </button>
            <button
              type="button"
              className="rec-quick-win-btn-secondary"
              onClick={() => setActiveTab("take_quiz")}
            >
              <span>🧪</span>
              <span>Open Diagnostic Sandbox</span>
            </button>
          </div>
        </div>
      )}

      {/* VIEW 3: Results Dashboard */}
      {activeTab === "dashboard" && recommendationResult && (
        <div>
          {/* Top Score & Scholar Persona Banner */}
          <section className="rec-score-hero">
            <div className="rec-score-gauge-box">
              <svg className="rec-gauge-svg" viewBox="0 0 160 160">
                <circle className="rec-gauge-bg" cx="80" cy="80" r={gaugeRadius} />
                <circle
                  className="rec-gauge-fill"
                  cx="80"
                  cy="80"
                  r={gaugeRadius}
                  stroke={gaugeColor}
                  strokeDasharray={gaugeCircumference}
                  strokeDashoffset={strokeDashoffset}
                />
              </svg>
              <div className="rec-gauge-text-box">
                <div className="rec-gauge-val">
                  {recommendationResult.score_percentage}%
                </div>
                <div className="rec-gauge-sub">
                  {recommendationResult.overall_score} /{" "}
                  {recommendationResult.total_questions} Correct
                </div>
              </div>
            </div>

            <div className="rec-score-details">
              <div>
                <span className={`rec-scholar-badge ${scholarMeta.className}`}>
                  <span>{scholarMeta.icon}</span> {scholarMeta.tier}
                </span>
              </div>

              <h2 className="rec-report-title">
                {selectedPreset?.title || "Course Material Assessment"}
              </h2>

              <p className="rec-summary-quote">
                "{scholarMeta.message}"
              </p>

              <div className="rec-boost-box">
                <span>⚡ Exam Readiness:</span>
                <strong>{recommendationResult.score_percentage}%</strong>
                <span className="rec-boost-arrow">──▶</span>
                <span className="rec-boost-val">
                  Target: {Math.min(100, recommendationResult.score_percentage + scholarMeta.boostPercent)}%
                </span>
                <span>(with Quick Win practice)</span>
              </div>

              <div className="rec-meta-tags" style={{ marginTop: "14px" }}>
                <span className="rec-meta-tag">
                  <span>👤</span> Student: <strong>{recommendationResult.student_id}</strong>
                </span>
                <span className="rec-meta-tag">
                  <span>🆔</span> Run: <code>{recommendationResult.recommendation_id}</code>
                </span>
              </div>
            </div>
          </section>

          {/* 📝 ENHANCED ASSESSMENT QUESTION DIGEST (Filter UI & Analysis) */}
          {questionsDigest.length > 0 && (
            <div className="rec-digest-panel">
              <div className="rec-digest-header">
                <div className="rec-digest-title-group">
                  <div className="rec-digest-title-badge">
                    <span>📝</span> Performance Digest
                  </div>
                  <h3 className="rec-digest-title">Assessment Question Breakdown</h3>
                  <p className="rec-digest-subtitle">
                    Examine your question-level choices, verify correct reasoning, and drill down by topic.
                  </p>
                </div>
                <div className="rec-digest-stats-strip">
                  <div className="rec-digest-stat-pill score">
                    <span className="rec-stat-pill-label">Score</span>
                    <strong className="rec-stat-pill-val">
                      {Math.round((correctCount / questionsDigest.length) * 100)}%
                    </strong>
                  </div>
                  <div className="rec-digest-stat-pill correct">
                    <span className="rec-stat-pill-icon">✓</span>
                    <span>{correctCount} Correct</span>
                  </div>
                  <div className="rec-digest-stat-pill missed">
                    <span className="rec-stat-pill-icon">✗</span>
                    <span>{missedCount} Missed</span>
                  </div>
                </div>
              </div>

              {/* Enhanced Question Filter Toolbar */}
              <div className="rec-digest-toolbar">
                {/* Row 1: Status Tabs + Topic Selector + View Toggle */}
                <div className="rec-digest-toolbar-row">
                  {/* Status Filter Segmented Control */}
                  <div className="rec-digest-status-pills" role="tablist" aria-label="Filter questions by status">
                    <button
                      type="button"
                      className={`rec-digest-status-btn ${digestFilter === "all" ? "active" : ""}`}
                      onClick={() => setDigestFilter("all")}
                    >
                      <span>All Questions</span>
                      <span className="rec-status-count-chip">{questionsDigest.length}</span>
                    </button>
                    <button
                      type="button"
                      className={`rec-digest-status-btn missed ${digestFilter === "missed" ? "active" : ""}`}
                      onClick={() => setDigestFilter("missed")}
                    >
                      <span className="rec-status-icon">✗</span>
                      <span>Missed</span>
                      <span className="rec-status-count-chip missed">{missedCount}</span>
                    </button>
                    <button
                      type="button"
                      className={`rec-digest-status-btn correct ${digestFilter === "correct" ? "active" : ""}`}
                      onClick={() => setDigestFilter("correct")}
                    >
                      <span className="rec-status-icon">✓</span>
                      <span>Correct</span>
                      <span className="rec-status-count-chip correct">{correctCount}</span>
                    </button>
                  </div>

                  {/* Secondary Controls: Topic Filter & View Mode Toggle */}
                  <div className="rec-digest-secondary-controls">
                    {/* Topic Filter Dropdown */}
                    <div className="rec-digest-topic-select-wrapper">
                      <span className="rec-select-icon">🏷️</span>
                      <select
                        className="rec-digest-topic-select"
                        value={digestTopicFilter}
                        onChange={(e) => setDigestTopicFilter(e.target.value)}
                        aria-label="Filter questions by topic"
                      >
                        <option value="all">All Topics ({questionsDigest.length})</option>
                        {digestTopics.map(({ topic, count }) => (
                          <option key={topic} value={topic}>
                            {topic} ({count})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* View Mode Toggle: Detailed vs Compact */}
                    <div className="rec-digest-view-toggle" role="group" aria-label="View density toggle">
                      <button
                        type="button"
                        className={`rec-view-mode-btn ${digestViewMode === "detailed" ? "active" : ""}`}
                        onClick={() => setDigestViewMode("detailed")}
                        title="Detailed cards view with full explanations"
                        aria-label="Detailed view"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                          <line x1="3" y1="9" x2="21" y2="9" />
                          <line x1="9" y1="21" x2="9" y2="9" />
                        </svg>
                        <span>Detailed</span>
                      </button>
                      <button
                        type="button"
                        className={`rec-view-mode-btn ${digestViewMode === "compact" ? "active" : ""}`}
                        onClick={() => setDigestViewMode("compact")}
                        title="Compact row view for quick scanning"
                        aria-label="Compact view"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="8" y1="6" x2="21" y2="6" />
                          <line x1="8" y1="12" x2="21" y2="12" />
                          <line x1="8" y1="18" x2="21" y2="18" />
                          <line x1="3" y1="6" x2="3.01" y2="6" />
                          <line x1="3" y1="12" x2="3.01" y2="12" />
                          <line x1="3" y1="18" x2="3.01" y2="18" />
                        </svg>
                        <span>Compact</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Row 2: Search Bar + Active Filters Indicators */}
                <div className="rec-digest-search-row">
                  <div className="rec-digest-search-box">
                    <span className="rec-search-icon">🔍</span>
                    <input
                      type="text"
                      className="rec-digest-search-input"
                      placeholder="Search questions, options, topics, or explanations..."
                      value={digestSearchQuery}
                      onChange={(e) => setDigestSearchQuery(e.target.value)}
                    />
                    {digestSearchQuery && (
                      <button
                        type="button"
                        className="rec-search-clear-btn"
                        onClick={() => setDigestSearchQuery("")}
                        title="Clear search query"
                        aria-label="Clear search"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  <div className="rec-digest-filter-summary">
                    <span className="rec-filter-count-label">
                      Showing <strong>{filteredDigest.length}</strong> of{" "}
                      <strong>{questionsDigest.length}</strong> questions
                    </span>

                    {hasActiveDigestFilters && (
                      <button
                        type="button"
                        className="rec-filter-reset-btn"
                        onClick={handleResetDigestFilters}
                        title="Reset all filters and search query"
                      >
                        <span>↻</span> Reset Filters
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Empty Search/Filter State */}
              {filteredDigest.length === 0 ? (
                <div className="rec-digest-empty-state">
                  <div className="rec-digest-empty-icon">
                    {digestFilter === "missed" && missedCount === 0 ? "🎉" : "🔍"}
                  </div>
                  <h4 className="rec-digest-empty-title">
                    {digestFilter === "missed" && missedCount === 0
                      ? "Zero Missed Questions!"
                      : "No matching questions found"}
                  </h4>
                  <p className="rec-digest-empty-desc">
                    {digestFilter === "missed" && missedCount === 0
                      ? "Flawless score! You got every question right on this assessment attempt."
                      : "Try clearing your search terms or selecting a different status/topic filter."}
                  </p>
                  <button
                    type="button"
                    className="rec-filter-reset-action-btn"
                    onClick={handleResetDigestFilters}
                  >
                    <span>↻</span> Show All {questionsDigest.length} Questions
                  </button>
                </div>
              ) : (
                /* Question Cards List (Detailed or Compact) */
                <div className={`rec-digest-list ${digestViewMode}`}>
                  {filteredDigest.map((q, idx) => {
                    const isCorrect = Boolean(q.is_correct);
                    const qId = q.question_id || `q_${idx}`;
                    const isExpanded = digestViewMode === "detailed" || Boolean(expandedDigestCards[qId]);
                    const originalIndex = questionsDigest.findIndex(
                      (item) => (item.question_id || item.question_text) === (q.question_id || q.question_text)
                    );
                    const questionNumber = originalIndex !== -1 ? originalIndex + 1 : idx + 1;

                    return (
                      <div
                        key={qId}
                        className={`rec-digest-card ${isCorrect ? "correct" : "incorrect"} ${digestViewMode}`}
                      >
                        {/* Card Header Row */}
                        <div className="rec-digest-card-top">
                          <div className="rec-digest-left-meta">
                            <span className="rec-digest-qnum-badge">Q{questionNumber}</span>
                            <span
                              className={`rec-digest-badge ${isCorrect ? "correct" : "incorrect"}`}
                            >
                              {isCorrect ? "✓ Correct" : "✗ Missed"}
                            </span>
                            {q.topic && (
                              <button
                                type="button"
                                className="rec-digest-topic"
                                onClick={() => setDigestTopicFilter(q.topic)}
                                title={`Filter by ${q.topic}`}
                              >
                                {q.topic}
                              </button>
                            )}
                            {q.difficulty && (
                              <span className={`rec-digest-difficulty ${q.difficulty.toLowerCase()}`}>
                                {q.difficulty}
                              </span>
                            )}
                          </div>

                          {digestViewMode === "compact" && (
                            <button
                              type="button"
                              className="rec-digest-accordion-btn"
                              onClick={() => toggleDigestCardExpansion(qId)}
                              aria-label={isExpanded ? "Collapse card details" : "Expand card details"}
                            >
                              <span>{isExpanded ? "Collapse ▲" : "Inspect Answers ▼"}</span>
                            </button>
                          )}
                        </div>

                        {/* Question Text */}
                        <div className="rec-digest-question">
                          {q.question_text}
                        </div>

                        {/* Collapsible Content in Compact Mode, or Always Visible in Detailed Mode */}
                        {isExpanded && (
                          <div className="rec-digest-card-expanded-body">
                            {/* Answers Comparison Grid */}
                            <div className="rec-digest-answers-grid">
                              <div
                                className={`rec-digest-answer-box ${
                                  !isCorrect ? "student-wrong" : "correct-target"
                                }`}
                              >
                                <div className="rec-digest-ans-label">
                                  <span>{isCorrect ? "✓" : "✗"}</span>
                                  <span>{isCorrect ? "Your Answer (Correct):" : "Your Selection:"}</span>
                                </div>
                                <div className="rec-digest-ans-text">
                                  {q.selected_answer || "No response provided"}
                                </div>
                              </div>

                              {!isCorrect && (
                                <div className="rec-digest-answer-box correct-target">
                                  <div className="rec-digest-ans-label">
                                    <span>🎯</span>
                                    <span>Expected Answer:</span>
                                  </div>
                                  <div className="rec-digest-ans-text">
                                    {q.correct_answer}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Pedagogical Explanation Box */}
                            {q.explanation && (
                              <div className="rec-digest-explanation">
                                <div className="rec-digest-explanation-title">
                                  <span>💡</span> Pedagogical Insight
                                </div>
                                <p className="rec-digest-explanation-text">
                                  {q.explanation}
                                </p>
                              </div>
                            )}

                            {/* Targeted Tutor Action for Missed Questions */}
                            {!isCorrect && (
                              <div className="rec-digest-card-actions">
                                <button
                                  type="button"
                                  className="rec-digest-tutor-ask-btn"
                                  onClick={() => handleAskTutorAboutQuestion(q)}
                                  title="Pass this specific question & misconception to AI Tutor"
                                >
                                  <span>💬</span>
                                  <span>Ask AI Tutor to Explain Question {questionNumber}</span>
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ⚖️ COGNITIVE BALANCE: VERIFIED STRENGTHS VS. PRIORITY GROWTH AREAS */}
          <section className="rec-balance-section">
            {/* Left Column: Strengths */}
            <div className="rec-balance-card strengths">
              <div className="rec-balance-header">
                <div>
                  <h3 className="rec-balance-title">
                    <span>🌟</span> Verified Strengths
                  </h3>
                  <p className="rec-balance-desc">
                    Concepts with solid retention (≥ 70% accuracy). Great foundation!
                  </p>
                </div>
                <span className="rec-balance-badge strengths">
                  {masteredTopics.length} Confirmed
                </span>
              </div>

              {masteredTopics.length === 0 ? (
                <div className="rec-balance-empty">
                  Take more practice assessments or complete quick drills to establish verified strengths.
                </div>
              ) : (
                <div className="rec-balance-list">
                  {masteredTopics.map((top) => {
                    const masteryObj = (recommendationResult.topic_mastery || []).find(
                      (tm) => tm.topic === top
                    );
                    const pct = masteryObj ? masteryObj.accuracy_percentage : 100;
                    return (
                      <div key={top} className="rec-balance-item">
                        <div>
                          <div className="rec-balance-topic">
                            <span>✓</span> {top}
                          </div>
                          <div className="rec-balance-sub">
                            High conceptual retention demonstrated
                          </div>
                        </div>
                        <span className="rec-balance-score-chip strengths">
                          {pct}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right Column: Weaknesses / Priority Growth Areas */}
            <div className="rec-balance-card weaknesses">
              <div className="rec-balance-header">
                <div>
                  <h3 className="rec-balance-title">
                    <span>🎯</span> Priority Growth Areas
                  </h3>
                  <p className="rec-balance-desc">
                    Targeted concepts to correct (&lt; 70% accuracy) for fastest grade leap.
                  </p>
                </div>
                <span className="rec-balance-badge weaknesses">
                  {weakTopics.length} Priority
                </span>
              </div>

              {weakTopics.length === 0 ? (
                <div className="rec-balance-empty">
                  🎉 Fantastic work! All tested concepts are currently above the 70% mastery threshold.
                </div>
              ) : (
                <div className="rec-balance-list">
                  {weakTopics.map((top) => {
                    const masteryObj = (recommendationResult.topic_mastery || []).find(
                      (tm) => tm.topic === top
                    );
                    const pct = masteryObj ? masteryObj.accuracy_percentage : 0;
                    const matchingGap = (recommendationResult.knowledge_gaps || []).find(
                      (kg) => kg.topic === top
                    );
                    return (
                      <div key={top} className="rec-balance-item">
                        <div>
                          <div className="rec-balance-topic">
                            <span>⚡</span> {top}
                          </div>
                          <div className="rec-balance-sub">
                            {matchingGap?.severity || "Needs"} attention · {masteryObj ? `${masteryObj.correct_count}/${masteryObj.total_questions} correct` : "Gap identified"}
                          </div>
                        </div>
                        <span className="rec-balance-score-chip weaknesses">
                          {pct}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </section>

          {/* ⚡ THE QUICK WIN PRIORITY CARD (Dopamine Trigger: Low Hanging Fruit) */}
          {quickWin && !recoveredGaps[quickWin.gap_id] && (
            <div className="rec-quick-win-card">
              <div className="rec-quick-win-top-bar">
                <span className="rec-quick-win-badge">
                  <span>⚡</span> 5-Minute Quick Win · Highest ROI
                </span>
                <span className="rec-quick-win-boost-badge">
                  <span>🚀</span> Estimated +{scholarMeta.boostPercent}% Readiness Leap
                </span>
              </div>

              <h3 className="rec-quick-win-title">
                Master Concept: "{quickWin.topic}"
              </h3>
              <p className="rec-quick-win-desc">
                {quickWin.explanation}
              </p>

              <div className="rec-quick-win-actions">
                <button
                  type="button"
                  className="rec-quick-win-btn-primary"
                  onClick={() => {
                    if (onLaunchTutor) {
                      onLaunchTutor(recommendationResult.tutor_handoff);
                    } else {
                      setShowTutorModal(true);
                    }
                  }}
                >
                  <span>💬</span>
                  <span>Launch 5-Min Socratic Coach</span>
                </button>

                <button
                  type="button"
                  className="rec-quick-win-btn-secondary"
                  onClick={() => toggleDrill(quickWin.gap_id)}
                >
                  <span>🧠</span>
                  <span>{activeDrills[quickWin.gap_id] ? "Close Micro-Drill" : "Take 30-Second Micro-Drill"}</span>
                </button>

                {onNavigate && (
                  <button
                    type="button"
                    className="rec-quick-win-btn-secondary"
                    onClick={() => onNavigate("materials")}
                  >
                    <span>📖</span>
                    <span>Review Lecture Slides</span>
                  </button>
                )}
              </div>

              {/* Inline Micro-Drill for Quick Win */}
              {activeDrills[quickWin.gap_id] && (() => {
                const drill = getDrillForTopic(quickWin.topic, quickWin.explanation);
                const drillState = activeDrills[quickWin.gap_id];
                return (
                  <div className="rec-micro-drill-card">
                    <div className="rec-drill-prompt">{drill.question}</div>
                    <div className="rec-drill-options">
                      {drill.options.map((opt, oIdx) => {
                        let btnClass = "";
                        if (drillState.isSubmitted) {
                          if (oIdx === drill.correctIndex) btnClass = "selected-correct";
                          else if (oIdx === drillState.selectedOpt) btnClass = "selected-incorrect";
                        } else if (drillState.selectedOpt === oIdx) {
                          btnClass = "selected-correct";
                        }
                        return (
                          <button
                            key={oIdx}
                            type="button"
                            className={`rec-drill-option-btn ${btnClass}`}
                            disabled={drillState.isSubmitted}
                            onClick={() => handleSelectDrillOption(quickWin.gap_id, oIdx)}
                          >
                            <strong>{String.fromCharCode(65 + oIdx)}.</strong> {opt}
                          </button>
                        );
                      })}
                    </div>

                    {!drillState.isSubmitted ? (
                      <button
                        type="button"
                        className="rec-quick-win-btn-primary"
                        disabled={drillState.selectedOpt === null}
                        onClick={() => handleSubmitDrill(quickWin.gap_id, drill)}
                      >
                        Check Answer
                      </button>
                    ) : (
                      <div className={`rec-drill-feedback ${drillState.isCorrect ? "success" : "error"}`}>
                        <span>
                          {drillState.isCorrect
                            ? "🎉 Spot on! Concept recovered (+50 XP). Your mastery level increased!"
                            : "💡 Not quite. " + drill.explanation}
                        </span>
                        {drillState.isCorrect && (
                          <span className="rec-gap-evidence-pill" style={{ background: "rgba(16,185,129,0.2)" }}>
                            ✓ Solved
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          {/* 🗺️ INTERACTIVE STUDY QUEST / ACTION CHECKLIST */}
          <div className="rec-quest-panel">
            <div className="rec-quest-header-row">
              <div className="rec-quest-title-box">
                <h3>
                  <span>🗺️</span> Your Actionable Recovery Quest
                </h3>
                <p>
                  Check off tasks as you review to level up your topic retention.
                </p>
              </div>

              <div className="rec-quest-progress-box">
                <div className="rec-quest-progress-label">
                  <span>Quest Progress</span>
                  <strong>{questPercent}% ({completedCount}/{studyMissions.length})</strong>
                </div>
                <div className="rec-quest-track">
                  <div
                    className="rec-quest-bar"
                    style={{ width: `${questPercent}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="rec-quest-list">
              {studyMissions.map((mission) => {
                const isDone = completedList.includes(mission.id);
                return (
                  <div
                    key={mission.id}
                    className={`rec-quest-item ${isDone ? "completed" : ""}`}
                  >
                    <button
                      type="button"
                      className="rec-quest-checkbox-btn"
                      onClick={() => toggleMission(mission.id)}
                      aria-label={`Mark mission as ${isDone ? "incomplete" : "complete"}`}
                    >
                      <div className="rec-quest-checkbox">
                        {isDone ? "✓" : ""}
                      </div>
                    </button>

                    <div className="rec-quest-body">
                      <div className="rec-quest-meta-line">
                        <span className="rec-quest-type-tag">{mission.type}</span>
                        <span className="rec-quest-time-tag">⏱️ ~{mission.time} mins</span>
                        {isDone && (
                          <span className="rec-gap-evidence-pill" style={{ background: "rgba(16,185,129,0.2)", color: "#10b981" }}>
                            ✓ Mission Cleared
                          </span>
                        )}
                      </div>

                      <h4 className="rec-quest-item-title">{mission.title}</h4>
                      <p className="rec-quest-item-desc">{mission.desc}</p>

                      <div className="rec-quest-cta-row">
                        {mission.actionType === "tutor" && (
                          <button
                            type="button"
                            className="rec-quest-action-btn"
                            onClick={() => {
                              toggleMission(mission.id);
                              if (onLaunchTutor) {
                                onLaunchTutor(recommendationResult.tutor_handoff);
                              } else {
                                setShowTutorModal(true);
                              }
                            }}
                          >
                            <span>💬</span>
                            <span>Ask AI Tutor Now</span>
                          </button>
                        )}

                        {mission.actionType === "drill" && mission.gap && (
                          <button
                            type="button"
                            className="rec-quest-action-btn"
                            onClick={() => toggleDrill(mission.gap.gap_id)}
                          >
                            <span>🧠</span>
                            <span>Take Quick Drill</span>
                          </button>
                        )}

                        {mission.actionType === "material" && onNavigate && (
                          <button
                            type="button"
                            className="rec-quest-action-btn"
                            onClick={() => onNavigate("materials")}
                          >
                            <span>📖</span>
                            <span>Open Lecture Slide</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Grid Layout: Topic Mastery + Socratic Tutor Handoff */}
          <div className="rec-dashboard-grid">
            {/* Topic Mastery Breakdown */}
            <div className="rec-panel" style={{ margin: 0 }}>
              <div className="rec-panel-header">
                <div>
                  <h3 className="rec-panel-title">
                    <span>📊</span> Topic Mastery Breakdown
                  </h3>
                  <p className="rec-panel-desc">
                    Fine-grained accuracy and difficulty weighting per lecture concept.
                  </p>
                </div>
              </div>

              <div className="rec-mastery-list">
                {recommendationResult.topic_mastery.map((tm) => {
                  const isRecovered = Object.keys(recoveredGaps).some((gId) =>
                    recommendationResult.knowledge_gaps.some(
                      (kg) => kg.gap_id === gId && kg.topic === tm.topic
                    )
                  );
                  const effectivePct = isRecovered
                    ? Math.min(100, tm.accuracy_percentage + 40)
                    : tm.accuracy_percentage;

                  const fillClass =
                    effectivePct >= 80
                      ? "fill-emerald"
                      : effectivePct >= 50
                      ? "fill-amber"
                      : "fill-rose";

                  return (
                    <div key={tm.topic} className="rec-mastery-item">
                      <div className="rec-mastery-top-row">
                        <span className="rec-mastery-topic">
                          {tm.topic}{" "}
                          {isRecovered && <span style={{ color: "#10b981", fontSize: "0.78rem" }}>★ Micro-Drill Boost</span>}
                        </span>
                        <span
                          className={`rec-mastery-status-pill ${
                            isRecovered ? "status-mastered" : `status-${tm.mastery_status.toLowerCase().replace(/\s+/g, "-")}`
                          }`}
                        >
                          {isRecovered ? "Recovered" : tm.mastery_status}
                        </span>
                      </div>
                      <div className="rec-progress-track">
                        <div
                          className={`rec-progress-fill ${fillClass}`}
                          style={{ width: `${effectivePct}%` }}
                        />
                      </div>
                      <div className="rec-mastery-bottom-row">
                        <span>
                          {tm.correct_count} of {tm.total_questions} questions correct
                        </span>
                        <strong>{effectivePct}%</strong>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Socratic Tutor Handoff Card */}
            <div className="rec-panel rec-tutor-panel" style={{ margin: 0 }}>
              <div>
                <span className="rec-interagent-badge">
                  <span>🤝</span> Inter-Agent Handshake
                </span>
                <h3 className="rec-panel-title">
                  <span>🤖</span> AI Tutor Remedial Handoff
                </h3>
                <p className="rec-panel-desc">
                  Tailored Socratic review package formulated for the Tutor Agent.
                </p>

                {/* Recognized Strengths Pills */}
                {recommendationResult.tutor_handoff?.mastered_topics?.length > 0 && (
                  <div className="rec-tutor-strengths-box">
                    <span className="rec-tutor-strengths-title">
                      Recognized Strengths:
                    </span>
                    <div className="rec-tutor-strengths-chips">
                      {recommendationResult.tutor_handoff.mastered_topics.map((top) => (
                        <span key={top} className="rec-tutor-strength-chip">
                          ✓ {top}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cognitive Bridge Analogy */}
                {recommendationResult.tutor_handoff?.cognitive_bridge_analogy && (
                  <div className="rec-tutor-bridge-box">
                    <div className="rec-tutor-bridge-header">
                      <span>🌉</span>
                      <span className="rec-tutor-bridge-title">
                        Cognitive Bridge (Strength ➔ Gap Analogy)
                      </span>
                    </div>
                    <p className="rec-tutor-bridge-text">
                      {recommendationResult.tutor_handoff.cognitive_bridge_analogy}
                    </p>
                  </div>
                )}

                <div className="rec-tutor-bubble-box">
                  <div className="rec-tutor-avatar">LM</div>
                  <div className="rec-tutor-bubble-text">
                    "{recommendationResult.tutor_handoff.suggested_opening_prompt}"
                  </div>
                </div>
              </div>

              <div className="rec-tutor-btn-row">
                <button
                  type="button"
                  className="rec-btn-tutor-launch"
                  onClick={() => {
                    if (onLaunchTutor) {
                      onLaunchTutor(recommendationResult.tutor_handoff);
                    } else {
                      setShowTutorModal(true);
                    }
                  }}
                >
                  <span>🚀</span>
                  <span>Launch Remedial Tutoring Session</span>
                </button>
                <button
                  type="button"
                  className="rec-btn-secondary"
                  onClick={() => setShowTutorModal(true)}
                >
                  <span>📜</span>
                  <span>Inspect Contract</span>
                </button>
              </div>
            </div>
          </div>

          {/* Identified Knowledge Gaps with Interactive On-the-Spot Micro-Drills */}
          <div className="rec-panel">
            <div className="rec-panel-header">
              <div>
                <h3 className="rec-panel-title">
                  <span>🔍</span> Knowledge Gaps & Pedagogical Explainability
                </h3>
                <p className="rec-panel-desc">
                  Transparent reasoning behind identified gaps, with on-the-spot concept challenges.
                </p>
              </div>
            </div>

            {recommendationResult.knowledge_gaps.length === 0 ? (
              <div className="rec-empty-gaps">
                ✨ No critical knowledge gaps detected in this assessment attempt. Excellent retention!
              </div>
            ) : (
              <div className="rec-gaps-grid">
                {recommendationResult.knowledge_gaps.map((gap) => {
                  const sevClass = gap.severity.toLowerCase();
                  const isRecovered = recoveredGaps[gap.gap_id];
                  const drill = getDrillForTopic(gap.topic, gap.explanation);
                  const drillState = activeDrills[gap.gap_id];

                  return (
                    <div
                      key={gap.gap_id}
                      className={`rec-gap-card ${sevClass}`}
                      style={{
                        borderColor: isRecovered ? "#10b981" : undefined,
                      }}
                    >
                      <div className="rec-gap-header">
                        <span className={`rec-gap-severity-badge ${sevClass}`}>
                          {gap.severity} Severity
                        </span>
                        <span className="rec-gap-evidence-pill">
                          {gap.missed_questions_count} missed{" "}
                          {gap.missed_questions_count === 1 ? "question" : "questions"}
                        </span>
                      </div>

                      <h4 className="rec-gap-topic-title">
                        {gap.topic}
                        {isRecovered && (
                          <span style={{ color: "#10b981", fontSize: "0.85rem", marginLeft: "8px" }}>
                            ✓ Recovered!
                          </span>
                        )}
                      </h4>

                      <div className="rec-explainability-box">
                        <div className="rec-explainability-title">
                          Pedagogical Rationale
                        </div>
                        <p className="rec-explainability-text">
                          {gap.explanation}
                        </p>
                      </div>

                      {gap.sample_misconceptions?.length > 0 && (
                        <div className="rec-misconceptions-box">
                          <div className="rec-misconceptions-title">
                            Logged Student Misconceptions
                          </div>
                          <ul className="rec-misconceptions-list">
                            {gap.sample_misconceptions.map((m, mIdx) => (
                              <li key={mIdx}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* On-the-spot concept recovery button */}
                      {isRecovered ? (
                        <div className="rec-gap-resolved-badge">
                          <span>🎉</span> Concept Mastered on the spot (+50 XP)
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="rec-gap-drill-toggle-btn"
                          onClick={() => toggleDrill(gap.gap_id)}
                        >
                          <span>🧠</span>
                          <span>{drillState ? "Close Concept Challenge" : "Test Myself on This (30s Drill)"}</span>
                        </button>
                      )}

                      {/* Interactive Micro-Drill Accordion */}
                      {drillState && !isRecovered && (
                        <div className="rec-micro-drill-card">
                          <div className="rec-drill-prompt">{drill.question}</div>
                          <div className="rec-drill-options">
                            {drill.options.map((opt, oIdx) => {
                              let btnClass = "";
                              if (drillState.isSubmitted) {
                                if (oIdx === drill.correctIndex) btnClass = "selected-correct";
                                else if (oIdx === drillState.selectedOpt) btnClass = "selected-incorrect";
                              } else if (drillState.selectedOpt === oIdx) {
                                btnClass = "selected-correct";
                              }
                              return (
                                <button
                                  key={oIdx}
                                  type="button"
                                  className={`rec-drill-option-btn ${btnClass}`}
                                  disabled={drillState.isSubmitted}
                                  onClick={() => handleSelectDrillOption(gap.gap_id, oIdx)}
                                >
                                  <strong>{String.fromCharCode(65 + oIdx)}.</strong> {opt}
                                </button>
                              );
                            })}
                          </div>

                          {!drillState.isSubmitted ? (
                            <button
                              type="button"
                              className="rec-quick-win-btn-primary"
                              disabled={drillState.selectedOpt === null}
                              onClick={() => handleSubmitDrill(gap.gap_id, drill)}
                            >
                              Check Answer
                            </button>
                          ) : (
                            <div className={`rec-drill-feedback ${drillState.isCorrect ? "success" : "error"}`}>
                              <span>
                                {drillState.isCorrect
                                  ? "🎉 Excellent! Concept recovered."
                                  : "💡 Insight: " + drill.explanation}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 🎯 CLOSED-LOOP RECOVERY BANNER (Action Oriented) */}
          <div className="rec-recovery-cta-panel">
            <div className="rec-recovery-cta-text">
              <h3>
                <span>🚀</span> Ready to Solidify Your Mastery?
              </h3>
              <p>
                Take a targeted 3-question recovery quiz with the Quiz Agent, or start a personalized
                1-on-1 Socratic discussion with your AI Tutor.
              </p>
            </div>
            <div className="rec-recovery-cta-btns">
              <button
                type="button"
                className="rec-btn-tutor-launch"
                onClick={() => {
                  if (onLaunchTutor) {
                    onLaunchTutor(recommendationResult.tutor_handoff);
                  } else {
                    setShowTutorModal(true);
                  }
                }}
              >
                <span>💬</span>
                <span>Chat with AI Tutor</span>
              </button>
              {onNavigate && (
                <button
                  type="button"
                  className="rec-quick-win-btn-primary"
                  onClick={() => onNavigate("quiz")}
                >
                  <span>🎯</span>
                  <span>Take Recovery Quiz</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 4: Assessment & Mistake Simulator (Sandbox Tab) */}
      {activeTab === "take_quiz" && (
        <div>
          {/* Panel 1: Configuration */}
          <div className="rec-panel">
            <div className="rec-panel-header">
              <div>
                <h2 className="rec-panel-title">
                  <span>⚙️</span> 1. Configure Diagnostic Scenario
                </h2>
                <p className="rec-panel-desc">
                  Select student context, course material, and assessment questions to test.
                </p>
              </div>
            </div>

            <div className="rec-grid-two-col">
              <div className="rec-form-group">
                <label className="rec-form-label" htmlFor="student-id-field">
                  Student Identifier
                </label>
                <input
                  id="student-id-field"
                  className="rec-form-input"
                  type="text"
                  value={studentId}
                  disabled
                />
              </div>

              <div className="rec-form-group">
                <label className="rec-form-label" htmlFor="doc-select-field">
                  Associated Course Material
                </label>
                <select
                  id="doc-select-field"
                  className="rec-form-select"
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                >
                  {documents.length === 0 ? (
                    <option value="doc_demo">
                      Information_Retrieval_Lecture_Notes.pdf (Demo)
                    </option>
                  ) : (
                    documents.map((d) => (
                      <option key={d.document_id} value={d.document_id}>
                        {d.original_filename} ({d.chunk_count || 0} chunks)
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>

            <div className="rec-form-group" style={{ marginTop: "16px" }}>
              <label className="rec-form-label">
                Select Formative Assessment Preset:
              </label>
              <div className="rec-preset-buttons-row">
                {PRESET_QUIZZES.map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    className={`rec-preset-btn ${
                      selectedPreset.id === preset.id ? "active" : ""
                    }`}
                    onClick={() => handlePresetChange(preset.id)}
                  >
                    <span>📑</span>
                    <span>{preset.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Panel 2: Questions Simulator */}
          <div className="rec-panel">
            <div className="rec-panel-header">
              <div>
                <h2 className="rec-panel-title">
                  <span>📝</span> 2. Student Responses & Mistake Simulator
                </h2>
                <p className="rec-panel-desc">
                  Toggle correctness to simulate mistakes and verify explainable gap calculations.
                </p>
              </div>
            </div>

            <div className="rec-questions-list">
              {activeQuestions.map((q, qIndex) => (
                <div
                  key={q.question_id}
                  className={`rec-question-card ${
                    q.is_correct ? "correct" : "incorrect"
                  }`}
                >
                  <div className="rec-question-card-header">
                    <span className="rec-question-num">
                      Question {qIndex + 1}
                    </span>
                    <span className="rec-question-topic">
                      <span>🏷️</span> {q.topic}
                    </span>
                    <span className={`rec-difficulty-badge ${q.difficulty}`}>
                      {q.difficulty} difficulty
                    </span>
                  </div>

                  <p className="rec-question-text">{q.question_text}</p>

                  <div className="rec-answer-box">
                    <div>
                      <span className="rec-answer-label">
                        Student's Selected Answer:
                      </span>
                      <div className="rec-answer-val">{q.selected_answer}</div>
                    </div>
                    {!q.is_correct && (
                      <div style={{ marginTop: "8px" }}>
                        <span
                          className="rec-answer-label"
                          style={{ color: "var(--rec-emerald)" }}
                        >
                          Expected Ground-Truth Answer:
                        </span>
                        <div
                          className="rec-answer-val"
                          style={{ color: "var(--rec-emerald)" }}
                        >
                          {q.correct_answer}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="rec-question-toggle-row">
                    <label className="rec-toggle-label">
                      <input
                        type="checkbox"
                        checked={q.is_correct}
                        onChange={() => toggleQuestionCorrectness(qIndex)}
                      />
                      <span>
                        Simulate Student Verdict:{" "}
                        <strong>{q.is_correct ? "✓ Correct" : "✗ Incorrect"}</strong>
                      </span>
                    </label>
                  </div>
                </div>
              ))}
            </div>

            <div className="rec-actions-bar">
              <button
                type="button"
                className="rec-btn-primary"
                onClick={handleRunAnalysis}
                disabled={isSubmitting}
              >
                <span>🚀</span>
                <span>
                  {isSubmitting
                    ? "Synthesizing Recommendations..."
                    : "Run Recommendation Agent Analysis"}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inter-Agent Contract Modal */}
      {showTutorModal && recommendationResult && (
        <div
          className="rec-modal-overlay"
          onClick={() => setShowTutorModal(false)}
        >
          <div
            className="rec-modal-content"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-contract-title"
          >
            <div className="rec-modal-header">
              <h3 className="rec-modal-title" id="modal-contract-title">
                🤝 Inter-Agent Contract: Recommendation → Tutor Agent
              </h3>
              <button
                type="button"
                className="rec-modal-close-btn"
                onClick={() => setShowTutorModal(false)}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <div className="rec-modal-body">
              <div className="rec-contract-field">
                <label>Target Topics for Remediation</label>
                <div className="rec-tag-cluster">
                  {recommendationResult.tutor_handoff.target_topics.map((t) => (
                    <span key={t} className="rec-tag">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              {recommendationResult.tutor_handoff.mastered_topics?.length > 0 && (
                <div className="rec-contract-field">
                  <label>Recognized Student Strengths (Anchors)</label>
                  <div className="rec-tag-cluster">
                    {recommendationResult.tutor_handoff.mastered_topics.map((t) => (
                      <span key={t} className="rec-tag" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10b981", borderColor: "rgba(16, 185, 129, 0.3)" }}>
                        ✓ {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {recommendationResult.tutor_handoff.cognitive_bridge_analogy && (
                <div className="rec-contract-field">
                  <label>Cognitive Bridge Analogy</label>
                  <div className="rec-quote-box" style={{ borderColor: "rgba(99, 102, 241, 0.3)", background: "rgba(99, 102, 241, 0.05)" }}>
                    🌉 {recommendationResult.tutor_handoff.cognitive_bridge_analogy}
                  </div>
                </div>
              )}

              <div className="rec-contract-field">
                <label>Pedagogical Directive for Tutor Agent</label>
                <div className="rec-quote-box">
                  {recommendationResult.tutor_handoff.pedagogical_instruction}
                </div>
              </div>

              <div className="rec-contract-field">
                <label>Suggested Opening Socratic Prompt</label>
                <div className="rec-quote-box" style={{ fontStyle: "italic" }}>
                  "{recommendationResult.tutor_handoff.suggested_opening_prompt}"
                </div>
              </div>

              <div className="rec-contract-field">
                <label>Structured JSON Contract</label>
                <div className="rec-json-container">
                  <button
                    type="button"
                    className="rec-copy-btn"
                    onClick={handleCopyJson}
                  >
                    {copiedContract ? "✓ Copied!" : "📋 Copy JSON"}
                  </button>
                  <pre className="rec-json-pre">
                    {JSON.stringify(recommendationResult.tutor_handoff, null, 2)}
                  </pre>
                </div>
              </div>
            </div>

            <div className="rec-modal-footer">
              <button
                type="button"
                className="rec-btn-primary"
                onClick={() => {
                  setShowTutorModal(false);
                  if (onLaunchTutor) {
                    onLaunchTutor(recommendationResult.tutor_handoff);
                  }
                }}
              >
                <span>🚀</span>
                <span>Launch Remedial Tutoring Now</span>
              </button>
              <button
                type="button"
                className="rec-btn-secondary"
                onClick={() => setShowTutorModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
