import { useState, useEffect } from "react";
import {
  analyzeQuizSubmission,
  getDocuments,
} from "../services/api.js";
import { useAuth } from "../auth/AuthContext.jsx";
import "./Recommendations.css";

const PRESET_QUIZZES = [
  {
    id: "quiz_ir_vsm",
    title: "Information Retrieval: Vector Space & Scoring",
    description: "5 questions covering Inverted Indexes, Term Weighting, and Vector Space Normalization.",
    questions: [
      {
        question_id: "q1",
        topic: "Term Weighting",
        difficulty: "easy",
        cognitive_level: "recall",
        question_text: "What does TF stand for in TF-IDF?",
        selected_answer: "Term Frequency",
        correct_answer: "Term Frequency",
        is_correct: true,
        explanation: "TF measures how frequently a term occurs in a document.",
      },
      {
        question_id: "q2",
        topic: "Term Weighting",
        difficulty: "medium",
        cognitive_level: "understanding",
        question_text: "Why is logarithmic scaling (log(1 + tf)) applied to Term Frequency?",
        selected_answer: "To make 10 occurrences tenfold more important than 1",
        correct_answer: "To reflect diminishing returns of repeated term occurrences",
        is_correct: false,
        explanation: "Sublinear scaling prevents very frequent terms from overly dominating scores.",
      },
      {
        question_id: "q3",
        topic: "Inverted Index",
        difficulty: "easy",
        cognitive_level: "recall",
        question_text: "In an inverted index, what does a postings list contain for a term?",
        selected_answer: "All words in alphabetical order",
        correct_answer: "A list of document IDs (and positions) where the term occurs",
        is_correct: false,
        explanation: "Postings lists store occurrences of a term across documents.",
      },
      {
        question_id: "q4",
        topic: "Inverted Index",
        difficulty: "medium",
        cognitive_level: "understanding",
        question_text: "How do skip pointers optimize postings list intersection?",
        selected_answer: "By skipping ahead without inspecting every posting element",
        correct_answer: "By skipping ahead without inspecting every posting element",
        is_correct: true,
        explanation: "Skip pointers enable faster merge without linear traversal.",
      },
      {
        question_id: "q5",
        topic: "Vector Space Scoring",
        difficulty: "hard",
        cognitive_level: "application",
        question_text: "Why is Euclidean length normalization (L2 norm) applied to document vectors?",
        selected_answer: "To shorten long queries",
        correct_answer: "To neutralize the unfair advantage long documents have due to high word counts",
        is_correct: false,
        explanation: "Length normalization ensures long documents do not dominate relevance.",
      },
    ],
  },
  {
    id: "quiz_ai_ethics",
    title: "AI Ethics, Fairness & Explainability",
    description: "4 questions assessing Algorithmic Bias, Fairness Metrics, and Model Interpretability.",
    questions: [
      {
        question_id: "q1",
        topic: "Algorithmic Bias",
        difficulty: "medium",
        cognitive_level: "understanding",
        question_text: "What is the primary cause of historical bias in machine learning models?",
        selected_answer: "Insufficient CPU processing power",
        correct_answer: "Unrepresentative or historically biased training datasets",
        is_correct: false,
        explanation: "Models replicate biases present in their training distributions.",
      },
      {
        question_id: "q2",
        topic: "Algorithmic Bias",
        difficulty: "easy",
        cognitive_level: "recall",
        question_text: "Can bias mitigation be performed during data pre-processing?",
        selected_answer: "Yes, through sample re-weighting and re-sampling",
        correct_answer: "Yes, through sample re-weighting and re-sampling",
        is_correct: true,
        explanation: "Pre-processing techniques balance representation before model training.",
      },
      {
        question_id: "q3",
        topic: "Explainability & SHAP",
        difficulty: "hard",
        cognitive_level: "application",
        question_text: "What mathematical foundation powers SHAP (SHapley Additive exPlanations)?",
        selected_answer: "Cooperative game theory Shapley values",
        correct_answer: "Cooperative game theory Shapley values",
        is_correct: true,
        explanation: "SHAP calculates fair marginal contribution of each feature to prediction.",
      },
      {
        question_id: "q4",
        topic: "Explainability & SHAP",
        difficulty: "medium",
        cognitive_level: "understanding",
        question_text: "What is the distinction between global and local interpretability?",
        selected_answer: "Global explains one instance, local explains the entire model",
        correct_answer: "Global explains overall model behavior, local explains a single prediction",
        is_correct: false,
        explanation: "Local interpretability focuses on reasons for a single inference outcome.",
      },
    ],
  },
];

export default function Recommendations({
  initialSubmission,
  initialRecommendation,
  onLaunchTutor = null,
}) {
  const { user } = useAuth();
  const [theme, setTheme] = useState(
    () => localStorage.getItem("learnmate_rec_theme") || "dark"
  );
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(
    initialSubmission?.document_id || ""
  );
  const studentId = user?.user_id || "guest_student";
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
  const [activeTab, setActiveTab] = useState(
    initialRecommendation || initialSubmission ? "dashboard" : "take_quiz"
  );
  const [copiedContract, setCopiedContract] = useState(false);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    localStorage.setItem("learnmate_rec_theme", nextTheme);
  }

  useEffect(() => {
    loadDocuments();
    if (initialRecommendation) {
      setRecommendationResult(initialRecommendation);
      setActiveTab("dashboard");
    } else if (initialSubmission) {
      analyzeExternalSubmission(initialSubmission);
    }
  }, [initialRecommendation, initialSubmission]);

  async function analyzeExternalSubmission(submission) {
    setIsSubmitting(true);
    try {
      const res = await analyzeQuizSubmission(submission);
      setRecommendationResult(res);
      setActiveTab("dashboard");
    } catch (err) {
      setErrorMessage(err?.message || "Failed to analyze quiz submission.");
    } finally {
      setIsSubmitting(false);
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

  function handlePresetChange(presetId) {
    const preset =
      PRESET_QUIZZES.find((p) => p.id === presetId) || PRESET_QUIZZES[0];
    setSelectedPreset(preset);
    setActiveQuestions(JSON.parse(JSON.stringify(preset.questions)));
    setRecommendationResult(null);
  }

  function toggleQuestionCorrectness(qIndex) {
    const updated = [...activeQuestions];
    updated[qIndex].is_correct = !updated[qIndex].is_correct;
    if (updated[qIndex].is_correct) {
      updated[qIndex].selected_answer = updated[qIndex].correct_answer;
    } else {
      updated[qIndex].selected_answer =
        "Alternative / misconception answer selected";
    }
    setActiveQuestions(updated);
  }

  async function handleAnalyze() {
    setIsSubmitting(true);
    setErrorMessage("");

    let targetDocId = selectedDocId;
    if (!targetDocId && documents.length > 0) {
      targetDocId = documents[0].document_id;
    }

    if (!targetDocId) {
      targetDocId = "doc_demo_ir_01";
    }

    const payload = {
      student_id: studentId,
      document_id: targetDocId,
      quiz_id: selectedPreset.id,
      quiz_title: selectedPreset.title,
      time_spent_seconds: 180,
      questions: activeQuestions,
    };

    try {
      const res = await analyzeQuizSubmission(payload);
      setRecommendationResult(res);
      setActiveTab("dashboard");
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

  // Circular gauge calculations
  const gaugeRadius = 64;
  const gaugeCircumference = 2 * Math.PI * gaugeRadius;
  const scorePct = recommendationResult?.score_percentage || 0;
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
            AI Recommendation Agent & Study Coach
          </div>

          <button
            type="button"
            className="rec-theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Toggle ${theme === "dark" ? "Light" : "Dark"} Mode`}
          >
            <span className="rec-theme-icon">
              {theme === "dark" ? (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
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
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </span>
            <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
          </button>
        </div>

        <h1 className="rec-hero-title">Personalized Knowledge Gap Analysis</h1>
        <p className="rec-hero-subtitle">
          Intelligently inspects student assessment logs, calculates fine-grained topic mastery,
          provides explainable pedagogical justifications, and formulates targeted Socratic review packages for the Tutor Agent.
        </p>
        <div className="rec-hero-disclaimer">
          <span>ℹ️</span>
          <span>
            These suggestions reflect evidence from the current assessment attempt, providing formative guidance rather than a permanent measure of capability.
          </span>
        </div>

        <nav className="rec-nav-bar" aria-label="Recommendation Modes">
          <button
            type="button"
            className={`rec-nav-btn ${activeTab === "take_quiz" ? "active" : ""}`}
            onClick={() => setActiveTab("take_quiz")}
          >
            <span>📝</span>
            <span>Assessment & Mistake Simulator</span>
          </button>
          <button
            type="button"
            className={`rec-nav-btn ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
            disabled={!recommendationResult}
          >
            <span>📊</span>
            <span>Explainable Gap Dashboard</span>
            {recommendationResult && (
              <span className="rec-status-indicator">Ready</span>
            )}
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

      {/* VIEW 1: Assessment Simulator */}
      {activeTab === "take_quiz" && (
        <div>
          {/* Panel 1: Configuration */}
          <div className="rec-panel">
            <div className="rec-panel-header">
              <div>
                <h2 className="rec-panel-title">
                  <span>⚙️</span> 1. Configure Student Assessment
                </h2>
                <p className="rec-panel-desc">
                  Select student context, course material, and assessment questions.
                </p>
              </div>
            </div>

            <div className="rec-form-grid">
              <div className="rec-form-group">
                <label className="rec-label">Student Profile</label>
                <input
                  type="text"
                  value={user?.full_name || "Learner"}
                  readOnly
                  className="rec-input"
                />
              </div>

              <div className="rec-form-group">
                <label className="rec-label">Course Material / Knowledge Base</label>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="rec-select"
                >
                  {documents.length === 0 && (
                    <option value="doc_demo_ir_01">
                      Lecture_4_Vector_Space_Model.pdf (Demo Document)
                    </option>
                  )}
                  {documents.map((doc) => (
                    <option key={doc.document_id} value={doc.document_id}>
                      {doc.original_filename} ({doc.page_count} pages)
                    </option>
                  ))}
                </select>
              </div>

              <div className="rec-form-group full-width">
                <label className="rec-label">Assessment Domain Presets</label>
                <div className="rec-preset-grid">
                  {PRESET_QUIZZES.map((preset) => (
                    <div
                      key={preset.id}
                      className={`rec-preset-card ${
                        selectedPreset.id === preset.id ? "active" : ""
                      }`}
                      onClick={() => handlePresetChange(preset.id)}
                      tabIndex={0}
                      role="button"
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          handlePresetChange(preset.id);
                        }
                      }}
                    >
                      <div className="rec-preset-title">{preset.title}</div>
                      <div className="rec-preset-desc">{preset.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Panel 2: Interactive Question Logs */}
          <div className="rec-panel">
            <div className="rec-panel-header">
              <div>
                <h2 className="rec-panel-title">
                  <span>📋</span> 2. Assessment Question Mistake Logs
                </h2>
                <p className="rec-panel-desc">
                  Click the toggle badge on any question to flip between correct and incorrect answers to test dynamic gap analysis.
                </p>
              </div>
              <div className="rec-q-badge" style={{ fontSize: "0.85rem", padding: "6px 14px" }}>
                Score: {activeQuestions.filter((q) => q.is_correct).length} / {activeQuestions.length} Correct
              </div>
            </div>

            <div className="rec-question-list">
              {activeQuestions.map((q, idx) => (
                <div
                  key={q.question_id}
                  className={`rec-question-card ${
                    q.is_correct ? "correct" : "incorrect"
                  }`}
                >
                  <div className="rec-question-header">
                    <span className="rec-q-badge">Q{idx + 1}</span>
                    <span className="rec-topic-pill">{q.topic}</span>
                    <span className={`rec-diff-badge rec-diff-${q.difficulty}`}>
                      {q.difficulty}
                    </span>
                    {q.cognitive_level && (
                      <span className="rec-q-badge" style={{ opacity: 0.8 }}>
                        {q.cognitive_level}
                      </span>
                    )}

                    <button
                      type="button"
                      className={`rec-toggle-btn ${
                        q.is_correct ? "btn-correct" : "btn-incorrect"
                      }`}
                      onClick={() => toggleQuestionCorrectness(idx)}
                      aria-label={`Toggle correctness for question ${idx + 1}`}
                    >
                      <span>{q.is_correct ? "✓" : "✗"}</span>
                      <span>{q.is_correct ? "Marked Correct" : "Marked Incorrect"}</span>
                    </button>
                  </div>

                  <div className="rec-question-text">{q.question_text}</div>

                  <div className="rec-answers-grid">
                    <div className="rec-answer-box">
                      <span className="rec-answer-label">Student Chosen Answer</span>
                      <div>{q.selected_answer}</div>
                    </div>
                    {!q.is_correct && (
                      <div className="rec-answer-box rec-answer-correct">
                        <span className="rec-answer-label">Ground Truth Correct Answer</span>
                        <div>{q.correct_answer}</div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="rec-actions-bar">
              <button
                type="button"
                className="rec-btn-primary"
                onClick={handleAnalyze}
                disabled={isSubmitting}
              >
                <span>{isSubmitting ? "⏳" : "⚡"}</span>
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

      {/* VIEW 2: Results Dashboard */}
      {activeTab === "dashboard" && recommendationResult && (
        <div>
          {/* Top Score Banner */}
          <section className="rec-score-hero">
            <div className="rec-score-gauge-box">
              <svg className="rec-gauge-svg" viewBox="0 0 160 160">
                <circle
                  className="rec-gauge-bg"
                  cx="80"
                  cy="80"
                  r={gaugeRadius}
                />
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
              <div className="rec-mastery-pill">
                <span>Signal:</span>
                <strong style={{ color: gaugeColor }}>
                  {recommendationResult.mastery_level}
                </strong>
              </div>
              <h2 className="rec-report-title">{selectedPreset.title}</h2>
              <blockquote className="rec-summary-quote">
                "{recommendationResult.summary}"
              </blockquote>
              <div className="rec-meta-tags">
                <span className="rec-meta-tag">
                  <span>👤</span> Student: <strong>{recommendationResult.student_id}</strong>
                </span>
                <span className="rec-meta-tag">
                  <span>🆔</span> Run: <code>{recommendationResult.recommendation_id}</code>
                </span>
              </div>
            </div>
          </section>

          {/* Grid Layout: Mastery + Socratic Tutor Handoff */}
          <div className="rec-dashboard-grid">
            {/* Topic Mastery Breakdown */}
            <div className="rec-panel" style={{ margin: 0 }}>
              <div className="rec-panel-header">
                <div>
                  <h3 className="rec-panel-title">
                    <span>📊</span> Topic Mastery Breakdown
                  </h3>
                  <p className="rec-panel-desc">
                    Calculated accuracy & severity weighting per evaluated topic.
                  </p>
                </div>
              </div>

              <div className="rec-mastery-list">
                {recommendationResult.topic_mastery.map((tm) => {
                  const statusClass = tm.mastery_status
                    .toLowerCase()
                    .replace(/\s+/g, "-");
                  const fillClass =
                    tm.accuracy_percentage >= 80
                      ? "fill-emerald"
                      : tm.accuracy_percentage >= 50
                      ? "fill-amber"
                      : "fill-rose";

                  return (
                    <div key={tm.topic} className="rec-mastery-item">
                      <div className="rec-mastery-top-row">
                        <span className="rec-mastery-topic">{tm.topic}</span>
                        <span
                          className={`rec-mastery-status-pill status-${statusClass}`}
                        >
                          {tm.mastery_status}
                        </span>
                      </div>
                      <div className="rec-progress-track">
                        <div
                          className={`rec-progress-fill ${fillClass}`}
                          style={{ width: `${tm.accuracy_percentage}%` }}
                        />
                      </div>
                      <div className="rec-mastery-bottom-row">
                        <span>
                          {tm.correct_count} of {tm.total_questions} questions correct
                        </span>
                        <strong>{tm.accuracy_percentage}%</strong>
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
                  The Recommendation Agent has generated a tailored Socratic coaching package for the Tutor Agent.
                </p>

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

          {/* Identified Knowledge Gaps & Pedagogical Explainability */}
          <div className="rec-panel">
            <div className="rec-panel-header">
              <div>
                <h3 className="rec-panel-title">
                  <span>🔍</span> Identified Knowledge Gaps & Pedagogical Explainability
                </h3>
                <p className="rec-panel-desc">
                  Transparent, evidence-based reasoning behind each identified area of weakness.
                </p>
              </div>
            </div>

            {recommendationResult.knowledge_gaps.length === 0 ? (
              <div className="rec-empty-gaps">
                ✨ No critical knowledge gaps detected in this assessment attempt.
              </div>
            ) : (
              <div className="rec-gaps-grid">
                {recommendationResult.knowledge_gaps.map((gap) => {
                  const sevClass = gap.severity.toLowerCase();
                  return (
                    <div
                      key={gap.gap_id}
                      className={`rec-gap-card ${sevClass}`}
                    >
                      <div className="rec-gap-header">
                        <span
                          className={`rec-gap-severity-badge ${sevClass}`}
                        >
                          {gap.severity} Severity
                        </span>
                        <span className="rec-gap-evidence-pill">
                          {gap.missed_questions_count} missed{" "}
                          {gap.missed_questions_count === 1
                            ? "question"
                            : "questions"}
                        </span>
                      </div>

                      <h4 className="rec-gap-topic-title">{gap.topic}</h4>

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
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Prioritized Actionable Study Plan */}
          <div className="rec-panel">
            <div className="rec-panel-header">
              <div>
                <h3 className="rec-panel-title">
                  <span>🎯</span> Prioritized Actionable Study Plan
                </h3>
                <p className="rec-panel-desc">
                  Curated sequence of remediation steps prioritized by gap severity and cognitive progression.
                </p>
              </div>
            </div>

            <div className="rec-plan-list">
              {recommendationResult.action_items.map((item) => (
                <div key={item.priority} className="rec-plan-item">
                  <div className="rec-plan-priority-badge">
                    #{item.priority}
                  </div>
                  <div className="rec-plan-details">
                    <div className="rec-plan-meta-row">
                      <span className="rec-plan-type-pill">
                        {item.action_type}
                      </span>
                      <span className="rec-plan-time">
                        ⏱️ {item.estimated_minutes} mins
                      </span>
                    </div>
                    <h4 className="rec-plan-title">{item.title}</h4>
                    <p className="rec-plan-desc">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: "24px" }}>
            <button
              type="button"
              className="rec-btn-secondary"
              onClick={() => setActiveTab("take_quiz")}
            >
              <span>←</span>
              <span>Test Another Assessment Scenario</span>
            </button>
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
