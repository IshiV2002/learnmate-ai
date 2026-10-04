import { useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import {
  deleteQuiz,
  evaluateAndRecommendQuiz,
  generateQuiz,
  getDocumentQuizzes,
  getDocuments,
  getQuiz,
  submitQuizEvaluation,
} from "../services/api.js";
import DeleteQuizModal from "./quiz/DeleteQuizModal.jsx";
import QuizGenerationJourney from "./quiz/QuizGenerationJourney.jsx";
import QuizIcon from "./quiz/QuizIcon.jsx";
import QuizSkeleton from "./quiz/QuizSkeleton.jsx";
import {
  formatTime,
  getDifficultyMeta,
  getQuizStats,
  getScoreTier,
  validateQuizConfig,
} from "./quiz/quizUtils.js";
import SavedQuizCard from "./quiz/SavedQuizCard.jsx";
import "./Quiz.css";

function Quiz({ onNavigateToRecommendations }) {
  const { user } = useAuth();
  const currentStudentId = user?.user_id || "student_default";

  // Navigation Views: 'configure' | 'taking' | 'results'
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
  const [questionType, setQuestionType] = useState("mcq");

  // Active Quiz Playing State
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [studentAnswers, setStudentAnswers] = useState({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [timeSpentSeconds, setTimeSpentSeconds] = useState(0);
  const timerRef = useRef(null);

  // Results & Evaluation State
  const [evaluationResult, setEvaluationResult] = useState(null);

  // Status & Loading States
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState("idle");
  const [generationTopic, setGenerationTopic] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);
  const [deletingQuizId, setDeletingQuizId] = useState(null);
  const [quizPendingDelete, setQuizPendingDelete] = useState(null);

  // Notifications
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const stats = useMemo(
    () => getQuizStats(savedQuizzes, documents),
    [savedQuizzes, documents],
  );

  const selectedDocObj = useMemo(
    () => documents.find((d) => d.document_id === selectedDocumentId),
    [documents, selectedDocumentId],
  );

  // Load documents on initial mount
  async function loadDocs(showLoading = true) {
    if (showLoading) setIsLoadingDocs(true);
    setErrorMessage("");
    try {
      const docs = await getDocuments();
      const docList = Array.isArray(docs) ? docs : [];
      setDocuments(docList);
      if (docList.length > 0 && !selectedDocumentId) {
        setSelectedDocumentId(docList[0].document_id);
      }
      return true;
    } catch (err) {
      setErrorMessage(err.message || "Failed to load uploaded documents.");
      return false;
    } finally {
      if (showLoading) setIsLoadingDocs(false);
    }
  }

  useEffect(() => {
    loadDocs();
  }, []);

  // Load saved quizzes whenever selected document changes
  async function loadSavedQuizzes(docId) {
    if (!docId) {
      setSavedQuizzes([]);
      return;
    }
    setIsLoadingSaved(true);
    try {
      const quizzes = await getDocumentQuizzes(docId);
      setSavedQuizzes(Array.isArray(quizzes) ? quizzes : []);
    } catch {
      setSavedQuizzes([]);
    } finally {
      setIsLoadingSaved(false);
    }
  }

  useEffect(() => {
    if (selectedDocumentId) {
      loadSavedQuizzes(selectedDocumentId);
    } else {
      setSavedQuizzes([]);
    }
  }, [selectedDocumentId]);

  // Timer lifecycle during active quiz taking
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

  // Generate a new quiz with AI
  async function handleGenerateQuiz(e) {
    e.preventDefault();
    const validationError = validateQuizConfig(
      selectedDocumentId,
      questionType,
    );
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setIsGenerating(true);
    setGenerationStatus("processing");
    setGenerationTopic(topic.trim());
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const payload = {
        document_id: selectedDocumentId,
        topic: topic.trim() || null,
        title: customTitle.trim() || null,
        num_questions: Number(numQuestions),
        difficulty: difficulty,
        question_types: [questionType],
      };

      const generated = await generateQuiz(payload);
      setGenerationStatus("complete");
      setActiveQuiz(generated);
      setStudentAnswers({});
      setCurrentQuestionIndex(0);
      setViewState("taking");
      setSuccessMessage("Assessment generated and grounded successfully!");

      // Refresh saved quizzes in background
      loadSavedQuizzes(selectedDocumentId);
    } catch (err) {
      setGenerationStatus("error");
      setErrorMessage(
        err.message || "Failed to generate assessment with AI agents.",
      );
    } finally {
      setIsGenerating(false);
    }
  }

  // Start taking a saved quiz
  async function handleStartSavedQuiz(quizId) {
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const quiz = await getQuiz(quizId, false);
      setActiveQuiz(quiz);
      setStudentAnswers({});
      setCurrentQuestionIndex(0);
      setViewState("taking");
    } catch (err) {
      setErrorMessage(err.message || "Could not load saved quiz.");
    }
  }

  // Confirm delete a saved quiz
  async function confirmDeleteQuiz() {
    if (!quizPendingDelete) return;

    const quizId = quizPendingDelete.quiz_id;
    const title = quizPendingDelete.title || "Assessment";

    setDeletingQuizId(quizId);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await deleteQuiz(quizId);
      setSavedQuizzes((prev) => prev.filter((q) => q.quiz_id !== quizId));
      setSuccessMessage(`“${title}” was removed from your quiz library.`);
      setQuizPendingDelete(null);
    } catch (err) {
      setErrorMessage(err.message || "Could not delete quiz.");
      setQuizPendingDelete(null);
    } finally {
      setDeletingQuizId(null);
    }
  }

  function handleAnswerSelect(questionId, answer) {
    setStudentAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  }

  // Submit active quiz for evaluation
  async function handleSubmitQuiz(andRecommend = false) {
    if (!activeQuiz) return;

    setIsSubmitting(true);
    setErrorMessage("");

    const formattedAnswers = (activeQuiz.questions || []).map((q) => ({
      question_id: q.question_id,
      answer_text: (studentAnswers[q.question_id] || "").trim(),
    }));

    const payload = {
      student_id: currentStudentId,
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
      setErrorMessage(err.message || "Failed to evaluate quiz submission.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="quiz-page">
      {/* Hero Header */}
      <header className="quiz-hero">
        <div className="quiz-hero-copy">
          <p className="quiz-eyebrow">Quiz Agent · Formative Assessment</p>
          <h1>Test understanding with lecture-grounded quizzes.</h1>
          <p className="quiz-hero-description">
            Synthesize Bloom-aligned assessments directly from your indexed lecture
            materials, test conceptual mastery with instant pedagogical feedback,
            and diagnose learning gaps.
          </p>
          <div className="quiz-hero-trust">
            <span>
              <QuizIcon name="shield" size={16} /> Server-evaluated grading
            </span>
            <span>
              <QuizIcon name="book" size={16} /> Page-aware citations
            </span>
            <span>
              <QuizIcon name="brain" size={16} /> Bloom taxonomy mapped
            </span>
          </div>
        </div>

        <div className="quiz-assessment-map" aria-label="Assessment statistics">
          <div className="quiz-map-visual" aria-hidden="true">
            <span className="quiz-map-ring quiz-map-ring-one" />
            <span className="quiz-map-ring quiz-map-ring-two" />
            <span className="quiz-map-line quiz-map-line-one" />
            <span className="quiz-map-line quiz-map-line-two" />
            <span className="quiz-map-node quiz-map-node-one" />
            <span className="quiz-map-node quiz-map-node-two" />
            <span className="quiz-map-node quiz-map-node-three" />
            <span className="quiz-map-core">
              <QuizIcon name="sparkles" size={22} />
            </span>
          </div>
          <div className="quiz-stat-grid">
            <div>
              <span>{isLoadingDocs ? "—" : stats.quizzes}</span>
              <small>Saved Quizzes</small>
            </div>
            <div>
              <span>{isLoadingDocs ? "—" : stats.documents}</span>
              <small>Course Sources</small>
            </div>
            <div>
              <span>{isLoadingDocs ? "—" : stats.questions}</span>
              <small>Questions</small>
            </div>
          </div>
        </div>
      </header>

      {/* Global Notifications */}
      <div className="quiz-feedback-stack" aria-live="polite">
        {errorMessage && (
          <div className="quiz-feedback quiz-feedback-error" role="alert">
            <span className="quiz-feedback-icon" aria-hidden="true">
              <QuizIcon name="close" size={17} />
            </span>
            <div>
              <strong>Something needs attention</strong>
              <p>{errorMessage}</p>
            </div>
            <button
              aria-label="Dismiss error"
              onClick={() => setErrorMessage("")}
              type="button"
            >
              <QuizIcon name="close" size={16} />
            </button>
          </div>
        )}

        {successMessage && (
          <div className="quiz-feedback quiz-feedback-success" role="status">
            <span className="quiz-feedback-icon" aria-hidden="true">
              <QuizIcon name="check" size={17} />
            </span>
            <div>
              <strong>Assessment updated</strong>
              <p>{successMessage}</p>
            </div>
            <button
              aria-label="Dismiss success message"
              onClick={() => setSuccessMessage("")}
              type="button"
            >
              <QuizIcon name="close" size={16} />
            </button>
          </div>
        )}
      </div>

      {/* VIEW 1: CONFIGURE & QUIZ LIBRARY */}
      {viewState === "configure" && (
        <>
          {isLoadingDocs ? (
            <section className="quiz-panel">
              <QuizSkeleton />
            </section>
          ) : documents.length === 0 ? (
            <div className="quiz-empty-state">
              <div className="quiz-empty-visual" aria-hidden="true">
                <span className="quiz-empty-document">
                  <QuizIcon name="document" size={30} />
                </span>
                <span className="quiz-empty-node quiz-empty-node-one" />
                <span className="quiz-empty-node quiz-empty-node-two" />
                <span className="quiz-empty-connection" />
              </div>
              <p className="quiz-section-kicker">Knowledge Vault required</p>
              <h3>No lecture materials found</h3>
              <p>
                Please upload a course PDF in the <strong>Knowledge Vault (Materials)</strong>{" "}
                tab before generating personalized assessments.
              </p>
            </div>
          ) : (
            <>
              {/* Section 01: Configure Assessment */}
              <section
                className="quiz-panel"
                aria-labelledby="quiz-config-heading"
              >
                <div className="quiz-section-heading">
                  <div>
                    <span className="quiz-section-number">01</span>
                    <div>
                      <p className="quiz-section-kicker">Assessment Generator</p>
                      <h2 id="quiz-config-heading">Synthesize a new quiz</h2>
                    </div>
                  </div>
                  <span className="quiz-security-label">
                    <QuizIcon name="shield" size={15} /> RAG Grounded Retrieval
                  </span>
                </div>

                <form className="quiz-config-form" onSubmit={handleGenerateQuiz}>
                  <div className="quiz-form-row">
                    <div className="quiz-form-group">
                      <label htmlFor="doc-select">Target Lecture PDF</label>
                      <select
                        id="doc-select"
                        className="quiz-form-control"
                        disabled={isGenerating}
                        onChange={(e) => setSelectedDocumentId(e.target.value)}
                        value={selectedDocumentId}
                      >
                        {documents.map((doc) => (
                          <option
                            key={doc.document_id}
                            value={doc.document_id}
                          >
                            {doc.original_filename} ({doc.page_count} pages)
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="quiz-form-group">
                      <label htmlFor="topic-input">
                        Specific Topic / Chapter (Optional)
                      </label>
                      <input
                        id="topic-input"
                        className="quiz-form-control"
                        disabled={isGenerating}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="e.g. Inverted Index, TF-IDF, Vector Space Model..."
                        type="text"
                        value={topic}
                      />
                      <small className="quiz-form-hint">
                        Leave blank to evaluate core concepts across the entire document.
                      </small>
                    </div>
                  </div>

                  <div className="quiz-form-row">
                    <div className="quiz-form-group">
                      <label htmlFor="num-q-select">Number of Questions</label>
                      <select
                        id="num-q-select"
                        className="quiz-form-control"
                        disabled={isGenerating}
                        onChange={(e) => setNumQuestions(Number(e.target.value))}
                        value={numQuestions}
                      >
                        <option value={3}>3 Questions (Quick Check)</option>
                        <option value={5}>5 Questions (Standard Assessment)</option>
                        <option value={8}>8 Questions (Comprehensive Review)</option>
                        <option value={10}>10 Questions (Deep Mastery Exam)</option>
                      </select>
                    </div>

                    <div className="quiz-form-group">
                      <label htmlFor="diff-select">Difficulty Tier</label>
                      <select
                        id="diff-select"
                        className="quiz-form-control"
                        disabled={isGenerating}
                        onChange={(e) => setDifficulty(e.target.value)}
                        value={difficulty}
                      >
                        <option value="mixed">Mixed (Adaptive Scope)</option>
                        <option value="easy">Easy (Foundational Recall)</option>
                        <option value="medium">Medium (Conceptual Understanding)</option>
                        <option value="hard">Hard (Application & Analysis)</option>
                      </select>
                    </div>
                  </div>

                  <div className="quiz-form-group">
                    <label>Question Format (Select One)</label>
                    <div className="quiz-formats-grid">
                      <label
                        className={`quiz-format-pill ${
                          questionType === "mcq" ? "quiz-format-pill-selected" : ""
                        }`}
                      >
                        <input
                          checked={questionType === "mcq"}
                          disabled={isGenerating}
                          name="questionFormat"
                          onChange={() => setQuestionType("mcq")}
                          type="radio"
                          value="mcq"
                        />
                        <span>Multiple Choice (MCQ)</span>
                      </label>

                      <label
                        className={`quiz-format-pill ${
                          questionType === "true_false"
                            ? "quiz-format-pill-selected"
                            : ""
                        }`}
                      >
                        <input
                          checked={questionType === "true_false"}
                          disabled={isGenerating}
                          name="questionFormat"
                          onChange={() => setQuestionType("true_false")}
                          type="radio"
                          value="true_false"
                        />
                        <span>True / False</span>
                      </label>

                      <label
                        className={`quiz-format-pill ${
                          questionType === "short_answer"
                            ? "quiz-format-pill-selected"
                            : ""
                        }`}
                      >
                        <input
                          checked={questionType === "short_answer"}
                          disabled={isGenerating}
                          name="questionFormat"
                          onChange={() => setQuestionType("short_answer")}
                          type="radio"
                          value="short_answer"
                        />
                        <span>Conceptual Short Answer</span>
                      </label>
                    </div>
                  </div>

                  <div className="quiz-upload-actions">
                    <p>
                      The Retrieval Agent grounds every question in the indexed
                      page chunks of your selected document.
                    </p>
                    <div>
                      <button
                        className="quiz-button quiz-button-primary"
                        disabled={isGenerating || !selectedDocumentId}
                        type="submit"
                      >
                        <QuizIcon
                          className={isGenerating ? "quiz-icon-spinning" : ""}
                          name="sparkles"
                          size={18}
                        />
                        {isGenerating
                          ? "Synthesizing with AI Agents…"
                          : "Generate AI Quiz"}
                      </button>
                    </div>
                  </div>
                </form>

                <QuizGenerationJourney
                  documentName={selectedDocObj?.original_filename}
                  status={generationStatus}
                  topic={generationTopic}
                />
              </section>

              {/* Grounding Transparency Banner */}
              <section
                className="quiz-transparency"
                aria-labelledby="quiz-transparency-heading"
              >
                <div className="quiz-transparency-icon" aria-hidden="true">
                  <QuizIcon name="search" size={23} />
                </div>
                <div>
                  <p className="quiz-section-kicker">How assessment generation works</p>
                  <h2 id="quiz-transparency-heading">
                    Grounded in your material, with page citations.
                  </h2>
                  <p>
                    LearnMate extracts text into searchable sections and keeps page
                    references so questions directly challenge understanding of
                    your specific course curriculum.
                  </p>
                </div>
                <div
                  className="quiz-pipeline"
                  aria-label="Assessment generation pipeline"
                >
                  <span>Lecture PDF</span>
                  <i aria-hidden="true" />
                  <span>Semantic Chunks</span>
                  <i aria-hidden="true" />
                  <span>Bloom Synthesis</span>
                  <i aria-hidden="true" />
                  <span>Pedagogical Grading</span>
                </div>
              </section>

              {/* Saved Quizzes Library Section */}
              <section
                className="quiz-library-section"
                aria-labelledby="quiz-library-heading"
              >
                <div className="quiz-library-heading">
                  <div>
                    <p className="quiz-section-kicker">Assessment Library</p>
                    <h2 id="quiz-library-heading">Available Quizzes</h2>
                    <p>
                      Saved assessments for{" "}
                      <strong>
                        {selectedDocObj?.original_filename || "selected document"}
                      </strong>
                    </p>
                  </div>
                  <button
                    className="quiz-button quiz-button-secondary"
                    disabled={isLoadingSaved || isGenerating}
                    onClick={() => loadSavedQuizzes(selectedDocumentId)}
                    type="button"
                  >
                    <QuizIcon
                      className={isLoadingSaved ? "quiz-icon-spinning" : ""}
                      name="refresh"
                      size={17}
                    />
                    Refresh library
                  </button>
                </div>

                {isLoadingSaved ? (
                  <QuizSkeleton />
                ) : savedQuizzes.length === 0 ? (
                  <div className="quiz-empty-state">
                    <div className="quiz-empty-visual" aria-hidden="true">
                      <span className="quiz-empty-document">
                        <QuizIcon name="sparkles" size={30} />
                      </span>
                      <span className="quiz-empty-node quiz-empty-node-one" />
                      <span className="quiz-empty-node quiz-empty-node-two" />
                      <span className="quiz-empty-connection" />
                    </div>
                    <p className="quiz-section-kicker">Ready for assessment</p>
                    <h3>No saved quizzes yet for this document</h3>
                    <p>
                      Generate your first lecture-grounded assessment using the
                      form above!
                    </p>
                  </div>
                ) : (
                  <div className="saved-quiz-grid">
                    {savedQuizzes.map((q) => (
                      <SavedQuizCard
                        documentName={selectedDocObj?.original_filename}
                        isDeleting={deletingQuizId === q.quiz_id}
                        key={q.quiz_id}
                        onDelete={setQuizPendingDelete}
                        onTakeQuiz={handleStartSavedQuiz}
                        quiz={q}
                      />
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </>
      )}

      {/* VIEW 2: ACTIVE QUIZ PLAYER */}
      {viewState === "taking" && activeQuiz && (
        <section className="quiz-panel quiz-player-panel">
          {/* Header */}
          <div className="quiz-player-header">
            <div>
              <button
                className="quiz-button quiz-button-quiet quiz-button-small"
                onClick={() => setViewState("configure")}
                style={{ marginBottom: "12px" }}
                type="button"
              >
                <QuizIcon name="arrowLeft" size={15} /> Exit to Assessment Hub
              </button>
              <h2>{activeQuiz.title}</h2>
              <p className="quiz-subtitle">
                Topic: <strong>{activeQuiz.topic}</strong> · Source:{" "}
                <strong>{selectedDocObj?.original_filename}</strong>
              </p>
            </div>

            <div className="quiz-player-meta-badges">
              <div className="quiz-timer-pill">
                <QuizIcon name="clock" size={16} />
                <span>{formatTime(timeSpentSeconds)}</span>
              </div>

              <div className="quiz-progress-box">
                <span>
                  Question <strong>{currentQuestionIndex + 1}</strong> of{" "}
                  <strong>{activeQuiz.questions?.length || 0}</strong>
                </span>
                <div className="quiz-progress-track">
                  <div
                    className="quiz-progress-bar"
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
          </div>

          {/* Question Display Card */}
          {(() => {
            const q = (activeQuiz.questions || [])[currentQuestionIndex];
            if (!q) return <p>No questions available in this assessment.</p>;

            const currentAnswer = studentAnswers[q.question_id] || "";
            const diffMeta = getDifficultyMeta(q.difficulty);

            return (
              <div className="question-display-card">
                <div className="question-meta-row">
                  <span className={`quiz-tag quiz-tag-diff-${diffMeta.shortLabel.toLowerCase()}`}>
                    <QuizIcon name="target" size={13} />
                    {diffMeta.shortLabel}
                  </span>
                  <span className="quiz-tag">
                    <QuizIcon name="brain" size={13} />
                    Bloom: {q.cognitive_level || "Application"}
                  </span>
                  <span className="quiz-tag">
                    <QuizIcon name="layers" size={13} />
                    {q.topic || activeQuiz.topic}
                  </span>
                  {q.source_page && (
                    <span className="quiz-tag quiz-tag-citation">
                      <QuizIcon name="book" size={13} />
                      Page {q.source_page}
                    </span>
                  )}
                </div>

                <h3 className="question-text">{q.question_text}</h3>

                {q.question_type === "short_answer" ? (
                  <div className="short-answer-container">
                    <label htmlFor={`input-${q.question_id}`}>
                      <strong>Your Conceptual Explanation:</strong>
                    </label>
                    <textarea
                      id={`input-${q.question_id}`}
                      className="quiz-form-control short-answer-input"
                      disabled={isSubmitting}
                      onChange={(e) =>
                        handleAnswerSelect(q.question_id, e.target.value)
                      }
                      placeholder="Type your explanation in your own words. The AI evaluation agent will review conceptual grounding..."
                      rows={5}
                      value={currentAnswer}
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
                            checked={isSelected}
                            disabled={isSubmitting}
                            name={`question-${q.question_id}`}
                            onChange={() =>
                              handleAnswerSelect(q.question_id, opt)
                            }
                            type="radio"
                            value={opt}
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
              className="quiz-button quiz-button-secondary"
              disabled={currentQuestionIndex === 0 || isSubmitting}
              onClick={() => setCurrentQuestionIndex((prev) => prev - 1)}
              type="button"
            >
              <QuizIcon name="arrowLeft" size={15} /> Previous Question
            </button>

            {currentQuestionIndex <
            (activeQuiz.questions?.length || 1) - 1 ? (
              <button
                className="quiz-button quiz-button-primary"
                onClick={() => setCurrentQuestionIndex((prev) => prev + 1)}
                type="button"
              >
                Next Question <QuizIcon name="arrowRight" size={15} />
              </button>
            ) : (
              <div className="quiz-submit-group">
                <button
                  className="quiz-button quiz-button-secondary"
                  disabled={isSubmitting}
                  onClick={() => handleSubmitQuiz(false)}
                  type="button"
                >
                  {isSubmitting ? "Evaluating…" : "Submit & Review"}
                </button>
                <button
                  className="quiz-button quiz-button-primary"
                  disabled={isSubmitting}
                  onClick={() => handleSubmitQuiz(true)}
                  type="button"
                >
                  {isSubmitting ? (
                    <>
                      <span className="quiz-processing-spinner" aria-hidden="true" />
                      Analyzing Knowledge Gaps…
                    </>
                  ) : (
                    <>
                      <QuizIcon name="sparkles" size={16} />
                      Submit & Analyze Gaps
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {/* VIEW 3: RESULTS & PEDAGOGICAL BREAKDOWN */}
      {viewState === "results" && evaluationResult && (
        <div className="results-container">
          {/* Results Hero Banner */}
          <section className="quiz-panel results-hero-panel">
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
                <strong>
                  {formatTime(evaluationResult.time_spent_seconds)}
                </strong>
              </p>
              {(() => {
                const tierMeta = getScoreTier(
                  evaluationResult.score_percentage,
                );
                return (
                  <span className={`quiz-tier-pill ${tierMeta.badgeClass}`}>
                    {tierMeta.label}
                  </span>
                );
              })()}
            </div>

            <div className="results-hero-actions">
              <button
                className="quiz-button quiz-button-primary quiz-button-large"
                onClick={() => {
                  if (onNavigateToRecommendations) {
                    onNavigateToRecommendations(
                      evaluationResult.submission_payload,
                    );
                  }
                }}
                type="button"
              >
                <QuizIcon name="sparkles" size={17} />
                View AI Study Coach & Recommendations
              </button>
              <button
                className="quiz-button quiz-button-secondary"
                onClick={() => setViewState("configure")}
                type="button"
              >
                <QuizIcon name="refresh" size={16} /> New Assessment
              </button>
            </div>
          </section>

          {/* Question Breakdown List */}
          <section
            className="quiz-panel results-breakdown-panel"
            aria-labelledby="results-breakdown-heading"
          >
            <div className="quiz-section-heading">
              <div>
                <span className="quiz-section-number">02</span>
                <div>
                  <p className="quiz-section-kicker">Pedagogical Review</p>
                  <h2 id="results-breakdown-heading">
                    Question Breakdown & Citations
                  </h2>
                </div>
              </div>
            </div>

            <div className="results-items-list">
              {(evaluationResult.results || []).map((res, idx) => (
                <div
                  key={res.question_id}
                  className={`result-item-card ${
                    res.is_correct
                      ? "result-item-correct"
                      : "result-item-incorrect"
                  }`}
                >
                  <div className="result-item-header">
                    <span className="result-question-num">
                      Question {idx + 1}
                    </span>
                    <span
                      className={`result-verdict-pill ${
                        res.is_correct
                          ? "verdict-correct"
                          : "verdict-incorrect"
                      }`}
                    >
                      {res.is_correct
                        ? "✓ Correct (1.0 pt)"
                        : "✗ Incorrect (0.0 pt)"}
                    </span>
                    <span className="quiz-tag">
                      <QuizIcon name="layers" size={13} />
                      {res.topic}
                    </span>
                    <span className="quiz-tag">
                      <QuizIcon name="target" size={13} />
                      {res.difficulty}
                    </span>
                    {res.source_page && (
                      <span className="quiz-tag quiz-tag-citation">
                        <QuizIcon name="book" size={13} />
                        Page {res.source_page}
                      </span>
                    )}
                  </div>

                  <p className="result-question-statement">
                    {res.question_text}
                  </p>

                  <div className="answers-comparison-box">
                    <div className="answer-row">
                      <span className="answer-label">Your Answer:</span>
                      <span
                        className={`answer-val ${
                          res.is_correct ? "text-success" : "text-danger"
                        }`}
                      >
                        {res.student_answer || "(No answer provided)"}
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
                      <strong>💡 Concept Explanation</strong>
                      <p>{res.explanation}</p>
                    </div>
                  )}

                  {res.feedback && res.feedback !== res.explanation && (
                    <div className="result-feedback-box">
                      <strong>Pedagogical Feedback</strong>
                      <p>{res.feedback}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <DeleteQuizModal
        isDeleting={deletingQuizId === quizPendingDelete?.quiz_id}
        onCancel={() => setQuizPendingDelete(null)}
        onConfirm={confirmDeleteQuiz}
        quiz={quizPendingDelete}
      />
    </div>
  );
}

export default Quiz;
