import { useState, useEffect } from "react";
import {
  analyzeQuizSubmission,
  getDocuments,
  getStudentRecommendations,
  getTutorHandoff,
} from "../services/api.js";

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

export default function Recommendations({ onLaunchTutor = null }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [studentId, setStudentId] = useState("student_demo_01");
  const [selectedPreset, setSelectedPreset] = useState(PRESET_QUIZZES[0]);
  const [activeQuestions, setActiveQuestions] = useState(PRESET_QUIZZES[0].questions);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recommendationResult, setRecommendationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [showTutorModal, setShowTutorModal] = useState(false);
  const [activeTab, setActiveTab] = useState("take_quiz"); // "take_quiz" | "dashboard"

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      const docs = await getDocuments();
      setDocuments(docs || []);
      if (docs && docs.length > 0) {
        setSelectedDocId(docs[0].document_id);
      }
    } catch {
      // Fallback: document might not be uploaded yet
      setDocuments([]);
    }
  }

  function handlePresetChange(presetId) {
    const preset = PRESET_QUIZZES.find((p) => p.id === presetId) || PRESET_QUIZZES[0];
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
      updated[qIndex].selected_answer = "Incorrect / alternative answer selected";
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
      // If no document exists, create/use the demo document ID
      targetDocId = "doc_demo_ir_01";
    }

    const payload = {
      student_id: studentId.trim() || "student_demo_01",
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
        err?.message || "Failed to generate recommendations. Please ensure the backend is running."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-container">
      {/* Header Banner */}
      <section className="recommendation-header">
        <div className="header-badge">AI Recommendation Agent & Study Coach</div>
        <h1 className="header-title">Personalized Knowledge Gap Analysis</h1>
        <p className="header-subtitle">
          Analyzes student assessment mistake logs, computes granular topic mastery,
          provides explainable pedagogical justifications, and synthesizes Socratic review packages for the Tutor Agent.
        </p>

        <div className="mode-toggle-bar">
          <button
            className={`mode-btn ${activeTab === "take_quiz" ? "mode-btn-active" : ""}`}
            onClick={() => setActiveTab("take_quiz")}
          >
            📝 Assessment & Mistake Simulator
          </button>
          <button
            className={`mode-btn ${activeTab === "dashboard" ? "mode-btn-active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
            disabled={!recommendationResult}
          >
            📊 Explainable Recommendations Dashboard
            {recommendationResult && <span className="ready-dot" />}
          </button>
        </div>
      </section>

      {errorMessage && (
        <div className="alert-box alert-error">
          <strong>⚠️ Notice:</strong> {errorMessage}
        </div>
      )}

      {/* VIEW 1: Assessment Simulator */}
      {activeTab === "take_quiz" && (
        <div className="assessment-container">
          <div className="card-panel">
            <h2 className="panel-title">1. Configure Student Assessment</h2>
            <div className="form-grid">
              <div className="form-group">
                <label>Student Identifier</label>
                <input
                  type="text"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  placeholder="e.g. student_ravin_2026"
                  className="input-field"
                />
              </div>

              <div className="form-group">
                <label>Select Course Material / Document</label>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="input-field"
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

              <div className="form-group full-width">
                <label>Assessment Preset (Quiz Agent Output)</label>
                <div className="preset-selector-grid">
                  {PRESET_QUIZZES.map((preset) => (
                    <div
                      key={preset.id}
                      className={`preset-card ${selectedPreset.id === preset.id ? "preset-card-active" : ""}`}
                      onClick={() => handlePresetChange(preset.id)}
                    >
                      <div className="preset-card-title">{preset.title}</div>
                      <div className="preset-card-desc">{preset.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Question Logs */}
          <div className="card-panel">
            <div className="panel-header-row">
              <div>
                <h2 className="panel-title">2. Assessment Question Logs</h2>
                <p className="panel-desc">
                  Click any question badge to toggle correct/incorrect state and test dynamic gap analysis.
                </p>
              </div>
              <div className="score-preview-badge">
                Current Score: {activeQuestions.filter((q) => q.is_correct).length} / {activeQuestions.length}
              </div>
            </div>

            <div className="question-list">
              {activeQuestions.map((q, idx) => (
                <div
                  key={q.question_id}
                  className={`question-item ${q.is_correct ? "q-correct" : "q-incorrect"}`}
                >
                  <div className="q-item-header">
                    <span className="q-number">Q{idx + 1}</span>
                    <span className="q-topic-tag">{q.topic}</span>
                    <span className={`q-diff-badge diff-${q.difficulty}`}>
                      {q.difficulty.toUpperCase()}
                    </span>
                    <button
                      type="button"
                      className={`q-toggle-btn ${q.is_correct ? "btn-pass" : "btn-fail"}`}
                      onClick={() => toggleQuestionCorrectness(idx)}
                    >
                      {q.is_correct ? "✓ Answered Correctly" : "✗ Marked Incorrect"}
                    </button>
                  </div>
                  <div className="q-text">{q.question_text}</div>
                  <div className="q-answers-grid">
                    <div className="ans-box ans-selected">
                      <small>Student's Chosen Answer:</small>
                      <div>{q.selected_answer}</div>
                    </div>
                    {!q.is_correct && (
                      <div className="ans-box ans-ground-truth">
                        <small>Ground Truth Correct Answer:</small>
                        <div>{q.correct_answer}</div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="action-row">
              <button
                type="button"
                className="btn-primary btn-large"
                onClick={handleAnalyze}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Analyzing Knowledge Gaps..." : "⚡ Run Recommendation Agent Analysis"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: Results Dashboard */}
      {activeTab === "dashboard" && recommendationResult && (
        <div className="dashboard-container">
          {/* Top Score Banner */}
          <div className="score-banner-card">
            <div className="score-circle-section">
              <div className="score-circle">
                <span className="score-num">{recommendationResult.score_percentage}%</span>
                <small className="score-ratio">
                  {recommendationResult.overall_score} / {recommendationResult.total_questions} Correct
                </small>
              </div>
            </div>

            <div className="score-details-section">
              <div className="mastery-badge-pill">
                Mastery Level: <strong>{recommendationResult.mastery_level}</strong>
              </div>
              <h2 className="report-quiz-title">{selectedPreset.title}</h2>
              <div className="summary-quote-box">
                <p>"{recommendationResult.summary}"</p>
              </div>
              <div className="meta-stats-row">
                <span>👤 Student: <strong>{recommendationResult.student_id}</strong></span>
                <span>🆔 Recommendation: <code>{recommendationResult.recommendation_id}</code></span>
              </div>
            </div>
          </div>

          {/* Grid Layout: Mastery + Knowledge Gaps */}
          <div className="dashboard-grid">
            {/* Topic Mastery Matrix */}
            <div className="card-panel">
              <h3 className="section-title">📊 Topic Mastery Breakdown</h3>
              <p className="panel-desc">Calculated topic-level accuracy & severity weighting.</p>

              <div className="topic-mastery-list">
                {recommendationResult.topic_mastery.map((tm) => (
                  <div key={tm.topic} className="topic-mastery-row">
                    <div className="tm-label-row">
                      <span className="tm-topic-name">{tm.topic}</span>
                      <span
                        className={`tm-status-pill status-${tm.mastery_status.toLowerCase().replace(" ", "-")}`}
                      >
                        {tm.mastery_status}
                      </span>
                    </div>
                    <div className="progress-track">
                      <div
                        className={`progress-fill ${
                          tm.accuracy_percentage >= 80
                            ? "fill-green"
                            : tm.accuracy_percentage >= 50
                            ? "fill-yellow"
                            : "fill-red"
                        }`}
                        style={{ width: `${tm.accuracy_percentage}%` }}
                      />
                    </div>
                    <div className="tm-meta-row">
                      <span>{tm.correct_count} / {tm.total_questions} Questions Correct</span>
                      <span><strong>{tm.accuracy_percentage}%</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Socratic Tutor Handoff Card */}
            <div className="card-panel tutor-cta-panel">
              <div className="tutor-cta-badge">Inter-Agent Collaboration</div>
              <h3 className="section-title">🤖 AI Tutor Remedial Handoff</h3>
              <p className="panel-desc">
                The Recommendation Agent has formulated a targeted Socratic session package for the Tutor Agent.
              </p>

              <div className="tutor-prompt-preview">
                <div className="tutor-avatar">LM</div>
                <div className="tutor-bubble">
                  "{recommendationResult.tutor_handoff.suggested_opening_prompt}"
                </div>
              </div>

              <div className="tutor-cta-button-row">
                <button
                  type="button"
                  className="btn-tutor-launch"
                  onClick={() => {
                    if (onLaunchTutor) {
                      onLaunchTutor(recommendationResult.tutor_handoff);
                    } else {
                      setShowTutorModal(true);
                    }
                  }}
                >
                  🚀 Launch Remedial Tutoring Session
                </button>
                <button
                  type="button"
                  className="btn-secondary btn-sm"
                  onClick={() => setShowTutorModal(true)}
                >
                  📜 View Inter-Agent JSON Contract
                </button>
              </div>
            </div>
          </div>

          {/* Identified Knowledge Gaps with Explainability */}
          <div className="card-panel">
            <h3 className="section-title">🔍 Identified Knowledge Gaps & Pedagogical Explainability</h3>
            <p className="panel-desc">
              Transparent, evidence-based reasoning behind each identified weakness.
            </p>

            {recommendationResult.knowledge_gaps.length === 0 ? (
              <div className="empty-gaps-box">
                🎉 No knowledge gaps identified! Full conceptual mastery achieved across all topics.
              </div>
            ) : (
              <div className="knowledge-gaps-grid">
                {recommendationResult.knowledge_gaps.map((gap, idx) => (
                  <div
                    key={gap.gap_id}
                    className={`gap-card gap-card-${gap.severity.toLowerCase()}`}
                  >
                    <div className="gap-card-header">
                      <span className={`severity-tag severity-${gap.severity.toLowerCase()}`}>
                        {gap.severity} GAP
                      </span>
                      <span className="confidence-pill">
                        Diagnosis Confidence: {Math.round(gap.confidence_score * 100)}%
                      </span>
                    </div>

                    <h4 className="gap-topic">{gap.topic}</h4>

                    <div className="gap-reasoning-box">
                      <strong>Explainability Rationale:</strong>
                      <p>{gap.explanation}</p>
                    </div>

                    {gap.sample_misconceptions.length > 0 && (
                      <div className="misconceptions-section">
                        <strong>Logged Misconceptions:</strong>
                        <ul>
                          {gap.sample_misconceptions.map((m, mIdx) => (
                            <li key={mIdx}>{m}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Prioritized Actionable Study Plan */}
          <div className="card-panel">
            <h3 className="section-title">🎯 Prioritized Actionable Study Plan</h3>
            <p className="panel-desc">
              Structured sequence of remedial steps prioritized by gap severity and cognitive difficulty.
            </p>

            <div className="study-plan-list">
              {recommendationResult.action_items.map((item) => (
                <div key={item.priority} className="action-item-card">
                  <div className="action-priority-badge">#{item.priority}</div>
                  <div className="action-details">
                    <div className="action-header-line">
                      <span className="action-type-pill">{item.action_type}</span>
                      <span className="action-time">⏱️ {item.estimated_minutes} mins</span>
                    </div>
                    <h4 className="action-title">{item.title}</h4>
                    <p className="action-desc">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bottom-bar">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setActiveTab("take_quiz")}
            >
              ← Test Another Quiz Assessment
            </button>
          </div>
        </div>
      )}

      {/* MODAL: Socratic Tutor Agent Handoff Package */}
      {showTutorModal && recommendationResult && (
        <div className="modal-overlay" onClick={() => setShowTutorModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🤝 Inter-Agent Contract: Recommendation → Tutor Agent</h3>
              <button
                type="button"
                className="close-modal-btn"
                onClick={() => setShowTutorModal(false)}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="json-contract-section">
                <div className="contract-field">
                  <label>Target Topics for Tutoring:</label>
                  <div className="tag-cluster">
                    {recommendationResult.tutor_handoff.target_topics.map((t) => (
                      <span key={t} className="topic-pill">{t}</span>
                    ))}
                  </div>
                </div>

                <div className="contract-field">
                  <label>Pedagogical Directive for Tutor Agent:</label>
                  <div className="directive-box">
                    {recommendationResult.tutor_handoff.pedagogical_instruction}
                  </div>
                </div>

                <div className="contract-field">
                  <label>Suggested Opening Socratic Prompt:</label>
                  <div className="opening-prompt-box">
                    "{recommendationResult.tutor_handoff.suggested_opening_prompt}"
                  </div>
                </div>

                <div className="contract-field">
                  <label>JSON Payload Sent to Tutor Agent API:</label>
                  <pre className="json-viewer">
                    {JSON.stringify(recommendationResult.tutor_handoff, null, 2)}
                  </pre>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn-primary"
                onClick={() => {
                  setShowTutorModal(false);
                  if (onLaunchTutor) {
                    onLaunchTutor(recommendationResult.tutor_handoff);
                  }
                }}
              >
                🚀 Start Remedial Tutoring Now
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowTutorModal(false)}
              >
                Close Contract Viewer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
