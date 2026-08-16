import { useState, useEffect, useRef } from "react";
import {
  generateQuiz,
  getDocumentQuizzes,
  getDocuments,
  getQuiz,
  submitQuizEvaluation,
  evaluateAndRecommendQuiz,
  deleteQuiz,
} from "../services/api.js";

function Quiz({ onNavigateToRecommendations }) {
  // Navigation & View States: 'configure' | 'taking' | 'results'
  const [viewState, setViewState] = useState("configure");

  // Data States
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [savedQuizzes, setSavedQuizzes] = useState([]);

  // Quiz Configuration State
  const [topic, setTopic] = useState("");
  const [customTitle, setCustomTitle] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState("mixed");
  const [questionTypes, setQuestionTypes] = useState(["mcq"]);

  // Active Quiz State
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [studentAnswers, setStudentAnswers] = useState({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [timeSpentSeconds, setTimeSpentSeconds] = useState(0);
  const timerRef = useRef(null);

  // Results State
  const [evaluationResult, setEvaluationResult] = useState(null);

  // Status & Loading States
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Load documents on mount
  useEffect(() => {
    async function loadDocs() {
      setIsLoadingDocs(true);
      try {
        const docs = await getDocuments();
        const docList = Array.isArray(docs) ? docs : [];
        setDocuments(docList);
        if (docList.length > 0) {
          setSelectedDocumentId(docList[0].document_id);
        }
      } catch (err) {
        setErrorMessage(err.message || "Failed to load uploaded documents.");
      } finally {
        setIsLoadingDocs(false);
      }
    }
    loadDocs();
  }, []);

  // Load saved quizzes whenever selected document changes
  useEffect(() => {
    if (!selectedDocumentId) {
      setSavedQuizzes([]);
      return;
    }
    async function loadSaved() {
      setIsLoadingSaved(true);
      try {
        const quizzes = await getDocumentQuizzes(selectedDocumentId);
        setSavedQuizzes(Array.isArray(quizzes) ? quizzes : []);
      } catch {
        setSavedQuizzes([]);
      } finally {
        setIsLoadingSaved(false);
      }
    }
    loadSaved();
  }, [selectedDocumentId]);

  // Timer management during active quiz
  useEffect(() => {
    if (viewState === "taking") {
      setTimeSpentSeconds(0);
      timerRef.current = setInterval(() => {
        setTimeSpentSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [viewState]);

  // Format seconds into MM:SS
  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }

  // Handle Question Type Checkbox
  function toggleQuestionType(type) {
    setQuestionTypes((prev) => {
      if (prev.includes(type)) {
        if (prev.length === 1) return prev; // Keep at least one
        return prev.filter((t) => t !== type);
      }
      return [...prev, type];
    });
  }

  // Generate a new quiz with AI
  async function handleGenerateQuiz(e) {
    e.preventDefault();
    if (!selectedDocumentId) {
      setErrorMessage("Please select a document first.");
      return;
    }

    setIsGenerating(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const payload = {
        document_id: selectedDocumentId,
        topic: topic.trim() || null,
        title: customTitle.trim() || null,
        num_questions: Number(numQuestions),
        difficulty: difficulty,
        question_types: questionTypes,
      };

      const generated = await generateQuiz(payload);
      setActiveQuiz(generated);
      setStudentAnswers({});
      setCurrentQuestionIndex(0);
      setViewState("taking");
      setSuccessMessage("Quiz generated successfully!");
    } catch (err) {
      setErrorMessage(err.message || "Failed to generate quiz with AI.");
    } finally {
      setIsGenerating(false);
    }
  }

  // Start taking a saved quiz
  async function handleStartSavedQuiz(quizId) {
    setErrorMessage("");
    try {
      const quiz = await getQuiz(quizId, false);
      setActiveQuiz(quiz);
      setStudentAnswers({});
      setCurrentQuestionIndex(0);
      setViewState("taking");
    } catch (err) {
      setErrorMessage(err.message || "Could not load quiz.");
    }
  }

  // Delete a saved quiz
  async function handleDeleteSavedQuiz(quizId, e) {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this quiz?")) return;
    try {
      await deleteQuiz(quizId);
      setSavedQuizzes((prev) => prev.filter((q) => q.quiz_id !== quizId));
      setSuccessMessage("Quiz removed.");
    } catch (err) {
      setErrorMessage(err.message || "Could not delete quiz.");
    }
  }

  // Handle student selecting or typing an answer
  function handleAnswerSelect(questionId, answer) {
    setStudentAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  }

  // Submit quiz for evaluation
  async function handleSubmitQuiz(andRecommend = false) {
    if (!activeQuiz) return;

    setIsSubmitting(true);
    setErrorMessage("");

    const formattedAnswers = (activeQuiz.questions || []).map((q) => ({
      question_id: q.question_id,
      answer_text: (studentAnswers[q.question_id] || "").trim(),
    }));

    const payload = {
      student_id: "student_default",
      time_spent_seconds: timeSpentSeconds,
      answers: formattedAnswers,
    };

    try {
      let result;
      if (andRecommend) {
        result = await evaluateAndRecommendQuiz(activeQuiz.quiz_id, payload);
      } else {
        result = await submitQuizEvaluation(activeQuiz.quiz_id, payload);
      }

      setEvaluationResult(result);
      setViewState("results");

      if (andRecommend && onNavigateToRecommendations && result.recommendation) {
        onNavigateToRecommendations(result.recommendation);
      }
    } catch (err) {
      setErrorMessage(err.message || "Failed to submit and evaluate quiz.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const selectedDocObj = documents.find(
    (d) => d.document_id === selectedDocumentId
  );

  return (
    <div className="page-container">
      {/* Top Header */}
      <section className="page-heading">
        <div>
          <p className="eyebrow">Formative Assessment Agent</p>
          <h1>Interactive AI Quiz Generator</h1>
          <p>
            Synthesize lecture-grounded assessments, test your conceptual understanding,
            and pinpoint learning gaps with automated pedagogical grading.
          </p>
        </div>
        {viewState === "taking" && (
          <div className="quiz-timer-badge">
            ⏱️ <strong>{formatTime(timeSpentSeconds)}</strong>
          </div>
        )}
      </section>

      {/* Global Notifications */}
      {errorMessage && (
        <div className="feedback feedback-error" role="alert">
          <strong>Notice:</strong> {errorMessage}
        </div>
      )}
      {successMessage && (
        <div className="feedback feedback-success" role="status">
          <strong>Success:</strong> {successMessage}
        </div>
      )}

      {/* VIEW 1: CONFIGURE & GENERATE */}
      {viewState === "configure" && (
        <>
          {isLoadingDocs ? (
            <div className="state-card" role="status">
              <span className="spinner" aria-hidden="true" />
              <h3>Loading Materials...</h3>
              <p>Fetching uploaded PDFs from the library.</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="state-card">
              <span className="empty-icon" aria-hidden="true">
                📚
              </span>
              <h3>No Lecture Materials Found</h3>
              <p>
                Please upload a lecture PDF in the <strong>Materials & Retrieval</strong> tab
                before generating assessments.
              </p>
            </div>
          ) : (
            <div className="quiz-layout-grid">
              {/* Left Column: Generator Form */}
              <section className="panel" aria-labelledby="quiz-gen-heading">
                <div className="panel-heading">
                  <div>
                    <h2 id="quiz-gen-heading">Configure Assessment</h2>
                    <p>Customize topic scope, question format, and difficulty.</p>
                  </div>
                  <span className="step-badge">AI Generator</span>
                </div>

                <form onSubmit={handleGenerateQuiz} className="quiz-config-form">
                  <div className="form-group">
                    <label htmlFor="doc-select">
                      <strong>Target Lecture PDF:</strong>
                    </label>
                    <select
                      id="doc-select"
                      className="form-control"
                      value={selectedDocumentId}
                      onChange={(e) => setSelectedDocumentId(e.target.value)}
                      disabled={isGenerating}
                    >
                      {documents.map((doc) => (
                        <option key={doc.document_id} value={doc.document_id}>
                          {doc.original_filename} ({doc.page_count} pages)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="topic-input">
                      <strong>Specific Topic / Chapter (Optional):</strong>
                    </label>
                    <input
                      id="topic-input"
                      type="text"
                      className="form-control"
                      placeholder="e.g. Inverted Index, TF-IDF, Vector Space Model..."
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      disabled={isGenerating}
                    />
                    <small className="form-hint">
                      Leave blank to cover all key concepts in the document.
                    </small>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="num-q-select">
                        <strong>Number of Questions:</strong>
                      </label>
                      <select
                        id="num-q-select"
                        className="form-control"
                        value={numQuestions}
                        onChange={(e) => setNumQuestions(Number(e.target.value))}
                        disabled={isGenerating}
                      >
                        <option value={3}>3 Quick Check</option>
                        <option value={5}>5 Standard Assessment</option>
                        <option value={8}>8 Comprehensive</option>
                        <option value={10}>10 Deep Mastery</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label htmlFor="diff-select">
                        <strong>Difficulty Tier:</strong>
                      </label>
                      <select
                        id="diff-select"
                        className="form-control"
                        value={difficulty}
                        onChange={(e) => setDifficulty(e.target.value)}
                        disabled={isGenerating}
                      >
                        <option value="mixed">Mixed (Adaptive)</option>
                        <option value="easy">Easy (Foundational Recall)</option>
                        <option value="medium">Medium (Understanding)</option>
                        <option value="hard">Hard (Application & Analysis)</option>
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>
                      <strong>Question Formats:</strong>
                    </label>
                    <div className="checkbox-group">
                      <label className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={questionTypes.includes("mcq")}
                          onChange={() => toggleQuestionType("mcq")}
                          disabled={isGenerating}
                        />
                        <span>Multiple Choice (MCQ)</span>
                      </label>
                      <label className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={questionTypes.includes("true_false")}
                          onChange={() => toggleQuestionType("true_false")}
                          disabled={isGenerating}
                        />
                        <span>True / False</span>
                      </label>
                      <label className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={questionTypes.includes("short_answer")}
                          onChange={() => toggleQuestionType("short_answer")}
                          disabled={isGenerating}
                        />
                        <span>Conceptual Short Answer</span>
                      </label>
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="button button-primary button-large"
                    disabled={isGenerating || !selectedDocumentId}
                  >
                    {isGenerating ? (
                      <>
                        <span className="spinner" aria-hidden="true" />
                        Synthesizing with Retrieval Agent...
                      </>
                    ) : (
                      "✨ Generate AI Quiz"
                    )}
                  </button>
                </form>
              </section>

              {/* Right Column: Saved Quizzes & Summary */}
              <section className="panel" aria-labelledby="saved-quizzes-heading">
                <div className="panel-heading">
                  <div>
                    <h2 id="saved-quizzes-heading">Available Quizzes</h2>
                    <p>
                      Saved assessments for{" "}
                      <strong>{selectedDocObj?.original_filename || "selected document"}</strong>
                    </p>
                  </div>
                  <span className="document-count">{savedQuizzes.length}</span>
                </div>

                {isLoadingSaved ? (
                  <div className="state-card" role="status">
                    <span className="spinner" aria-hidden="true" />
                    <p>Loading quizzes...</p>
                  </div>
                ) : savedQuizzes.length === 0 ? (
                  <div className="state-card">
                    <p>No saved quizzes yet for this document.</p>
                    <small>Generate your first quiz using the form on the left!</small>
                  </div>
                ) : (
                  <div className="saved-quiz-list">
                    {savedQuizzes.map((q) => (
                      <div key={q.quiz_id} className="saved-quiz-card">
                        <div className="saved-quiz-info">
                          <h4>{q.title}</h4>
                          <div className="quiz-meta-tags">
                            <span className="tag tag-topic">{q.topic}</span>
                            <span className="tag tag-questions">
                              {q.total_questions} Questions
                            </span>
                            <span className={`tag tag-${q.difficulty}`}>
                              {q.difficulty}
                            </span>
                          </div>
                        </div>
                        <div className="saved-quiz-actions">
                          <button
                            type="button"
                            className="button button-primary button-small"
                            onClick={() => handleStartSavedQuiz(q.quiz_id)}
                          >
                            ▶ Take Quiz
                          </button>
                          <button
                            type="button"
                            className="button button-quiet button-small"
                            onClick={(e) => handleDeleteSavedQuiz(q.quiz_id, e)}
                            title="Delete Quiz"
                          >
                            🗑
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}
        </>
      )}

      {/* VIEW 2: ACTIVE QUIZ PLAYER */}
      {viewState === "taking" && activeQuiz && (
        <section className="panel quiz-player-panel">
          {/* Quiz Player Header */}
          <div className="quiz-player-header">
            <div>
              <button
                type="button"
                className="button button-quiet button-small"
                onClick={() => setViewState("configure")}
              >
                ← Exit Quiz
              </button>
              <h2>{activeQuiz.title}</h2>
              <p className="quiz-subtitle">
                Topic: <strong>{activeQuiz.topic}</strong> · Document:{" "}
                <strong>{selectedDocObj?.original_filename}</strong>
              </p>
            </div>
            <div className="quiz-progress-indicator">
              <span>
                Question <strong>{currentQuestionIndex + 1}</strong> of{" "}
                <strong>{activeQuiz.questions?.length || 0}</strong>
              </span>
              <div className="progress-bar-track">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${
                      (((currentQuestionIndex + 1) /
                        (activeQuiz.questions?.length || 1)) *
                        100)
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Question View */}
          {(() => {
            const q = (activeQuiz.questions || [])[currentQuestionIndex];
            if (!q) return <p>No questions available.</p>;

            const currentAnswer = studentAnswers[q.question_id] || "";

            return (
              <div className="question-display-card">
                <div className="question-meta-row">
                  <span className={`tag tag-difficulty tag-${q.difficulty}`}>
                    {q.difficulty}
                  </span>
                  <span className="tag tag-cognitive">
                    Bloom: {q.cognitive_level}
                  </span>
                  <span className="tag tag-topic">{q.topic}</span>
                  {q.source_page && (
                    <span className="tag tag-citation">
                      📖 Page {q.source_page}
                    </span>
                  )}
                </div>

                <h3 className="question-text">{q.question_text}</h3>

                {/* Option Rendering by Question Type */}
                {q.question_type === "short_answer" ? (
                  <div className="short-answer-container">
                    <label htmlFor={`input-${q.question_id}`}>
                      <strong>Your Explanation:</strong>
                    </label>
                    <textarea
                      id={`input-${q.question_id}`}
                      className="form-control short-answer-input"
                      rows={4}
                      placeholder="Type your conceptual answer here in your own words..."
                      value={currentAnswer}
                      onChange={(e) =>
                        handleAnswerSelect(q.question_id, e.target.value)
                      }
                      disabled={isSubmitting}
                    />
                  </div>
                ) : (
                  <div className="options-grid">
                    {(q.options || []).map((opt, optIdx) => {
                      const isSelected = currentAnswer === opt;
                      return (
                        <label
                          key={optIdx}
                          className={`option-card ${
                            isSelected ? "option-card-selected" : ""
                          }`}
                        >
                          <input
                            type="radio"
                            name={`question-${q.question_id}`}
                            value={opt}
                            checked={isSelected}
                            onChange={() =>
                              handleAnswerSelect(q.question_id, opt)
                            }
                            disabled={isSubmitting}
                          />
                          <span className="option-indicator">
                            {String.fromCharCode(65 + optIdx)}
                          </span>
                          <span className="option-label">{opt}</span>
                        </label>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })()}

          {/* Navigation Controls */}
          <div className="quiz-controls-row">
            <button
              type="button"
              className="button button-secondary"
              disabled={currentQuestionIndex === 0 || isSubmitting}
              onClick={() => setCurrentQuestionIndex((prev) => prev - 1)}
            >
              ← Previous
            </button>

            {currentQuestionIndex <
            (activeQuiz.questions?.length || 1) - 1 ? (
              <button
                type="button"
                className="button button-primary"
                onClick={() => setCurrentQuestionIndex((prev) => prev + 1)}
              >
                Next Question →
              </button>
            ) : (
              <div className="submit-buttons-group">
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={isSubmitting}
                  onClick={() => handleSubmitQuiz(false)}
                >
                  {isSubmitting ? "Grading..." : "Submit & Review"}
                </button>
                <button
                  type="button"
                  className="button button-primary"
                  disabled={isSubmitting}
                  onClick={() => handleSubmitQuiz(true)}
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner" aria-hidden="true" />
                      Evaluating & Analyzing Gaps...
                    </>
                  ) : (
                    "🚀 Submit & Analyze Knowledge Gaps"
                  )}
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {/* VIEW 3: RESULTS & PEDAGOGICAL FEEDBACK */}
      {viewState === "results" && evaluationResult && (
        <div className="results-container">
          {/* Score Banner */}
          <section className="panel results-hero-panel">
            <div className="score-badge-circle">
              <span className="score-percentage">
                {Math.round(evaluationResult.score_percentage)}%
              </span>
              <span className="score-fraction">
                {evaluationResult.score} / {evaluationResult.max_possible_score} pts
              </span>
            </div>

            <div className="results-hero-content">
              <h2>Assessment Complete!</h2>
              <p>
                Quiz: <strong>{evaluationResult.quiz_title}</strong> · Duration:{" "}
                <strong>{formatTime(evaluationResult.time_spent_seconds)}</strong>
              </p>
              <div className="results-badge-group">
                <span
                  className={`status-pill ${
                    evaluationResult.score_percentage >= 80
                      ? "status-mastered"
                      : evaluationResult.score_percentage >= 50
                      ? "status-review"
                      : "status-critical"
                  }`}
                >
                  {evaluationResult.score_percentage >= 80
                    ? "🌟 High Mastery"
                    : evaluationResult.score_percentage >= 50
                    ? "📖 Review Recommended"
                    : "⚠️ Foundational Gaps Detected"}
                </span>
              </div>
            </div>

            <div className="results-hero-actions">
              <button
                type="button"
                className="button button-primary button-large"
                onClick={() => {
                  if (onNavigateToRecommendations) {
                    onNavigateToRecommendations(
                      evaluationResult.submission_payload
                    );
                  }
                }}
              >
                🎯 View AI Study Coach & Recommendations →
              </button>
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setViewState("configure")}
              >
                🔄 New Assessment
              </button>
            </div>
          </section>

          {/* Question Breakdown List */}
          <section className="panel results-breakdown-panel">
            <div className="panel-heading">
              <div>
                <h3>Question Breakdown & Pedagogical Explanations</h3>
                <p>Review each question, your answer, and ground-truth citations.</p>
              </div>
            </div>

            <div className="results-items-list">
              {(evaluationResult.results || []).map((res, idx) => (
                <div
                  key={res.question_id}
                  className={`result-item-card ${
                    res.is_correct ? "result-item-correct" : "result-item-incorrect"
                  }`}
                >
                  <div className="result-item-header">
                    <span className="result-question-num">Question {idx + 1}</span>
                    <span
                      className={`result-verdict-pill ${
                        res.is_correct ? "verdict-correct" : "verdict-incorrect"
                      }`}
                    >
                      {res.is_correct ? "✓ Correct (1.0 pt)" : "✗ Incorrect (0.0 pt)"}
                    </span>
                    <span className="tag tag-topic">{res.topic}</span>
                    <span className={`tag tag-${res.difficulty}`}>{res.difficulty}</span>
                    {res.source_page && (
                      <span className="tag tag-citation">📖 PDF Page {res.source_page}</span>
                    )}
                  </div>

                  <p className="result-question-statement">{res.question_text}</p>

                  <div className="answers-comparison-box">
                    <div className="answer-row">
                      <span className="answer-label">Your Answer:</span>
                      <span
                        className={`answer-val ${
                          res.is_correct ? "text-success" : "text-danger"
                        }`}
                      >
                        {res.student_answer || "(None)"}
                      </span>
                    </div>

                    {!res.is_correct && (
                      <div className="answer-row">
                        <span className="answer-label">Expected Solution:</span>
                        <span className="answer-val text-correct">
                          {res.correct_answer}
                        </span>
                      </div>
                    )}
                  </div>

                  {res.explanation && (
                    <div className="result-explanation-box">
                      <strong>💡 Concept Explanation:</strong>
                      <p>{res.explanation}</p>
                    </div>
                  )}

                  {res.feedback && res.feedback !== res.explanation && (
                    <div className="result-feedback-box">
                      <strong>Teacher Feedback:</strong>
                      <p>{res.feedback}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default Quiz;
