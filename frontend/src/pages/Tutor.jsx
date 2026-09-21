import { useState, useEffect, useRef, useMemo } from "react";
import {
  getDocuments,
  getStudentTutorSessions,
  getTutorSession,
  sendTutorMessage,
  startTutorSession,
  deleteTutorSession,
} from "../services/api.js";
import { useAuth } from "../auth/AuthContext.jsx";
import TutorIcon from "./tutor/TutorIcon.jsx";
import TutorSkeleton from "./tutor/TutorSkeleton.jsx";
import DeleteSessionModal from "./tutor/DeleteSessionModal.jsx";
import SessionHistoryModal from "./tutor/SessionHistoryModal.jsx";
import {
  getTutorStats,
  getModeMeta,
  validateSessionConfig,
  TUTOR_MODES,
} from "./tutor/tutorUtils.js";
import "./Tutor.css";

export default function Tutor({ initialHandoff = null, onClearHandoff = null }) {
  const { user } = useAuth();
  const studentId = user?.user_id || "student_default";

  // Data states
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [topicFocus, setTopicFocus] = useState("");
  const [mode, setMode] = useState("socratic"); // 'socratic' | 'step_by_step' | 'concept_check'

  // Active dialogue states
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [activeCitations, setActiveCitations] = useState([]);
  const [highlightedCitationIndex, setHighlightedCitationIndex] = useState(null);
  const [suggestedFollowups, setSuggestedFollowups] = useState([]);
  const [conceptCheck, setConceptCheck] = useState(null);

  // History & past sessions
  const [pastSessions, setPastSessions] = useState([]);
  const [sessionPendingDelete, setSessionPendingDelete] = useState(null);
  const [isDeletingSession, setIsDeletingSession] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);

  // Interactive input & status
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Compute workspace stats
  const stats = useMemo(
    () => getTutorStats(pastSessions, documents),
    [pastSessions, documents]
  );

  // Scroll chat to bottom when messages update or loading state changes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load uploaded documents on initial mount
  useEffect(() => {
    async function loadDocs() {
      try {
        const docs = await getDocuments();
        const docList = Array.isArray(docs) ? docs : [];
        setDocuments(docList);
        if (docList.length > 0 && !selectedDocId) {
          setSelectedDocId(docList[0].document_id);
        }
      } catch (err) {
        console.error("Failed to load documents:", err);
      }
    }
    loadDocs();
  }, []);

  // Handle incoming initial remedial handoff from Recommendations tab
  useEffect(() => {
    if (initialHandoff && initialHandoff.document_id) {
      setSelectedDocId(initialHandoff.document_id);
      if (initialHandoff.target_topics && initialHandoff.target_topics.length > 0) {
        setTopicFocus(initialHandoff.target_topics[0]);
      }
      initSessionFromHandoff(initialHandoff);
    }
  }, [initialHandoff]);

  // Load student past sessions
  useEffect(() => {
    if (studentId) {
      loadStudentSessions();
    }
  }, [studentId]);

  async function loadStudentSessions() {
    try {
      const list = await getStudentTutorSessions(studentId);
      setPastSessions(Array.isArray(list) ? list : []);
    } catch (err) {
      console.warn("Could not load past sessions:", err);
    }
  }

  async function initSessionFromHandoff(handoff) {
    setSessionLoading(true);
    setErrorMessage("");
    try {
      const payload = {
        student_id: studentId,
        document_id: handoff.document_id,
        recommendation_id: handoff.recommendation_id,
        mode: "socratic",
        topic_focus: handoff.target_topics?.[0] || "Remedial Concept Review",
      };
      const session = await startTutorSession(payload);
      setCurrentSession(session);
      setMessages(session.messages || []);
      if (session.messages && session.messages.length > 0) {
        setActiveCitations(session.messages[0].citations || []);
      }
      setMode(session.mode || "socratic");
      setTopicFocus(session.topic_focus || "");
      loadStudentSessions();
      setSuccessMessage("Remedial Socratic session initialized from Recommendations.");
    } catch (err) {
      setErrorMessage(err.message || "Could not start remedial tutoring session.");
    } finally {
      setSessionLoading(false);
    }
  }

  async function handleStartNewSession(e) {
    if (e) e.preventDefault();

    const validation = validateSessionConfig({
      documentId: selectedDocId,
      mode: mode,
      topicFocus: topicFocus,
    });

    if (!validation.isValid) {
      setErrorMessage(validation.error);
      return;
    }

    setSessionLoading(true);
    setErrorMessage("");
    setSuccessMessage("");
    if (onClearHandoff) onClearHandoff();

    try {
      const payload = {
        student_id: studentId,
        document_id: selectedDocId,
        mode: mode,
        topic_focus: topicFocus.trim() || null,
      };
      const session = await startTutorSession(payload);
      setCurrentSession(session);
      setMessages(session.messages || []);
      if (session.messages && session.messages.length > 0) {
        setActiveCitations(session.messages[0].citations || []);
      }
      setSuggestedFollowups([]);
      setConceptCheck(null);
      setHighlightedCitationIndex(null);
      loadStudentSessions();
      setSuccessMessage("New Socratic dialogue session established.");
    } catch (err) {
      setErrorMessage(err.message || "Failed to start AI tutoring session.");
    } finally {
      setSessionLoading(false);
    }
  }

  async function handleSelectPastSession(sessionId) {
    setSessionLoading(true);
    setErrorMessage("");
    setShowHistoryModal(false);
    try {
      const session = await getTutorSession(sessionId);
      setCurrentSession(session);
      setMessages(session.messages || []);
      setSelectedDocId(session.document_id);
      setMode(session.mode);
      setTopicFocus(session.topic_focus || "");
      const lastTutorMsg = [...(session.messages || [])]
        .reverse()
        .find((m) => m.role === "tutor");
      setActiveCitations(lastTutorMsg?.citations || []);
      setSuggestedFollowups([]);
      setConceptCheck(null);
      setHighlightedCitationIndex(null);
    } catch (err) {
      setErrorMessage(err.message || "Could not load session.");
    } finally {
      setSessionLoading(false);
    }
  }

  function handlePromptDeleteSession(session) {
    setSessionPendingDelete(session);
  }

  async function handleConfirmDeleteSession() {
    if (!sessionPendingDelete) return;

    setIsDeletingSession(true);
    setErrorMessage("");
    try {
      await deleteTutorSession(sessionPendingDelete.session_id);
      if (currentSession?.session_id === sessionPendingDelete.session_id) {
        setCurrentSession(null);
        setMessages([]);
        setActiveCitations([]);
      }
      setSuccessMessage("Tutoring session removed from your workspace.");
      setSessionPendingDelete(null);
      loadStudentSessions();
    } catch (err) {
      setErrorMessage(err.message || "Failed to delete tutoring session.");
    } finally {
      setIsDeletingSession(false);
    }
  }

  async function handleSendMessage(textToSend = null) {
    const text = (textToSend || inputMessage).trim();
    if (!text || !currentSession) return;

    setInputMessage("");
    setLoading(true);
    setErrorMessage("");

    // Optimistically append student message
    const tempStudentMsg = {
      message_id: `temp_${Date.now()}`,
      session_id: currentSession.session_id,
      role: "student",
      content: text,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempStudentMsg]);

    try {
      const payload = {
        session_id: currentSession.session_id,
        message: text,
        mode: mode,
      };
      const response = await sendTutorMessage(payload);

      const tutorMsg = {
        message_id: response.message_id,
        session_id: response.session_id,
        role: "tutor",
        content: response.reply,
        citations: response.citations || [],
        created_at: response.created_at,
      };

      setMessages((prev) => [...prev, tutorMsg]);
      if (response.citations && response.citations.length > 0) {
        setActiveCitations(response.citations);
      }
      setSuggestedFollowups(response.suggested_followups || []);
      setConceptCheck(response.concept_check_question || null);
      setHighlightedCitationIndex(null);
    } catch (err) {
      setErrorMessage(err.message || "Failed to receive response from Tutor Agent.");
    } finally {
      setLoading(false);
    }
  }

  function handleHighlightCitation(citationIndex) {
    setHighlightedCitationIndex(citationIndex);
    // Remove highlight pulse after 3 seconds
    setTimeout(() => {
      setHighlightedCitationIndex(null);
    }, 3000);
  }

  const activeDocName =
    documents.find((d) => d.document_id === selectedDocId)?.original_filename ||
    "Course Lecture";

  const currentModeMeta = getModeMeta(mode);

  return (
    <div className="tutor-page">
      {/* Hero Header & Telemetry Map */}
      <header className="tutor-hero">
        <div className="tutor-hero-copy">
          <p className="tutor-eyebrow">Tutor · Socratic Guidance</p>
          <h1>Master complex concepts with lecture-grounded dialogue.</h1>
          <p className="tutor-hero-description">
            Engage in personalized Socratic study sessions grounded strictly in your uploaded course lecture PDFs, with verified page-aware citations.
          </p>
          <div className="tutor-hero-trust">
            <span>
              <TutorIcon name="shield" size={15} /> Server-grounded retrieval
            </span>
            <span>
              <TutorIcon name="book" size={15} /> Page-aware citations
            </span>
            <span>
              <TutorIcon name="brain" size={15} /> Bloom-aligned scaffolding
            </span>
          </div>
        </div>

        <div className="tutor-telemetry-map" aria-label="Tutor workspace statistics">
          <div className="tutor-map-visual" aria-hidden="true">
            <span className="tutor-map-ring tutor-map-ring-one" />
            <span className="tutor-map-ring tutor-map-ring-two" />
            <span className="tutor-map-node tutor-map-node-one" />
            <span className="tutor-map-node tutor-map-node-two" />
            <span className="tutor-map-node tutor-map-node-three" />
            <span className="tutor-map-core">
              <TutorIcon name="sparkles" size={24} />
            </span>
          </div>
          <div className="tutor-stat-grid">
            <div>
              <span>{stats.sessions}</span>
              <small>Sessions</small>
            </div>
            <div>
              <span>{stats.documents}</span>
              <small>Course Sources</small>
            </div>
            <div>
              <span>{stats.topics}</span>
              <small>Topics</small>
            </div>
          </div>
        </div>
      </header>

      {/* Global Notifications Feedback Stack */}
      <div className="tutor-feedback-stack" aria-live="polite">
        {errorMessage && (
          <div className="tutor-feedback tutor-feedback-error" role="alert">
            <span className="tutor-feedback-icon" aria-hidden="true">
              <TutorIcon name="close" size={17} />
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
              <TutorIcon name="close" size={16} />
            </button>
          </div>
        )}

        {successMessage && (
          <div className="tutor-feedback tutor-feedback-success" role="status">
            <span className="tutor-feedback-icon" aria-hidden="true">
              <TutorIcon name="check" size={17} />
            </span>
            <div>
              <strong>Dialogue updated</strong>
              <p>{successMessage}</p>
            </div>
            <button
              aria-label="Dismiss success message"
              onClick={() => setSuccessMessage("")}
              type="button"
            >
              <TutorIcon name="close" size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Section 01: Socratic Session Architect */}
      <section className="tutor-panel" aria-labelledby="tutor-setup-heading">
        <div className="tutor-section-heading">
          <div>
            <span className="tutor-section-number">01</span>
            <div>
              <p className="tutor-section-kicker">Session Architect</p>
              <h2 id="tutor-setup-heading">Configure Socratic study session</h2>
            </div>
          </div>
          <div className="tutor-heading-actions">
            <button
              className="tutor-button tutor-button-secondary tutor-button-sm"
              onClick={() => setShowHistoryModal(true)}
              type="button"
            >
              <TutorIcon name="history" size={15} />
              Past Sessions ({pastSessions.length})
            </button>
            <button
              className="tutor-button tutor-button-primary tutor-button-sm"
              disabled={sessionLoading || documents.length === 0}
              onClick={handleStartNewSession}
              type="button"
            >
              <TutorIcon name="sparkles" size={15} />
              Start New Session
            </button>
          </div>
        </div>

        {/* Remedial Inter-Agent Handoff Banner */}
        {initialHandoff && (
          <div className="tutor-handoff-banner" role="status">
            <div className="tutor-handoff-icon" aria-hidden="true">
              <TutorIcon name="lightbulb" size={22} />
            </div>
            <div className="tutor-handoff-content">
              <strong>Inter-Agent Remedial Handoff Active:</strong>
              <p>
                Personalized review initialized by Recommendation Agent for:{" "}
                <em>
                  {initialHandoff.target_topics?.join(", ") || "Identified Knowledge Gaps"}
                </em>
                <span className="tutor-handoff-badge">
                  Severity: {initialHandoff.gap_severity || "medium"}
                </span>
              </p>
            </div>
            {onClearHandoff && (
              <button
                aria-label="Dismiss remedial handoff"
                className="tutor-handoff-close"
                onClick={onClearHandoff}
                type="button"
              >
                <TutorIcon name="close" size={16} />
              </button>
            )}
          </div>
        )}

        <form onSubmit={handleStartNewSession}>
          <div className="tutor-form-grid">
            <div className="tutor-form-group">
              <label htmlFor="tutor-doc-select">
                <TutorIcon name="document" size={15} /> Target Lecture PDF
              </label>
              <select
                className="tutor-form-control"
                disabled={sessionLoading || documents.length === 0}
                id="tutor-doc-select"
                onChange={(e) => setSelectedDocId(e.target.value)}
                value={selectedDocId}
              >
                {documents.length === 0 && (
                  <option value="">No course documents uploaded yet</option>
                )}
                {documents.map((doc) => (
                  <option key={doc.document_id} value={doc.document_id}>
                    {doc.original_filename} ({doc.page_count} pages)
                  </option>
                ))}
              </select>
            </div>

            <div className="tutor-form-group">
              <label htmlFor="tutor-topic-input">
                <TutorIcon name="search" size={15} /> Specific Topic / Focus (Optional)
              </label>
              <input
                className="tutor-form-control"
                disabled={sessionLoading}
                id="tutor-topic-input"
                onChange={(e) => setTopicFocus(e.target.value)}
                placeholder="e.g. Vector Space Model, Inverted Index, TF-IDF..."
                type="text"
                value={topicFocus}
              />
            </div>
          </div>

          {/* Teaching Mode Selector Cards */}
          <div className="tutor-modes-selector">
            <span className="tutor-modes-selector-label">
              <TutorIcon name="brain" size={15} /> Select Pedagogical Mode
            </span>
            <div className="tutor-modes-grid" role="radiogroup">
              {Object.values(TUTOR_MODES).map((item) => {
                const isSelected = mode === item.id;
                return (
                  <button
                    aria-checked={isSelected}
                    className={`tutor-mode-card ${isSelected ? "tutor-mode-card-active" : ""}`}
                    key={item.id}
                    onClick={() => setMode(item.id)}
                    role="radio"
                    type="button"
                  >
                    <div className="tutor-mode-card-header">
                      <strong>
                        <TutorIcon name={item.icon} size={17} />
                        {item.label}
                      </strong>
                      <span className="tutor-mode-kicker">{item.kicker}</span>
                    </div>
                    <p>{item.description}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </form>
      </section>

      {/* Section 02: Intelligent Socratic Dialogue Workspace */}
      <section className="tutor-panel" aria-labelledby="tutor-workspace-heading">
        <div className="tutor-section-heading">
          <div>
            <span className="tutor-section-number">02</span>
            <div>
              <p className="tutor-section-kicker">Pedagogical Dialogue</p>
              <h2 id="tutor-workspace-heading">Active Socratic Workspace</h2>
            </div>
          </div>
          <span className="tutor-security-label">
            <TutorIcon name="shield" size={15} /> Zero-hallucination grounding
          </span>
        </div>

        <div className="tutor-workspace-grid">
          {/* Main Chat Stream Card */}
          <div className="tutor-chat-card">
            <div className="tutor-chat-header">
              <div className="tutor-session-status">
                <span className="tutor-pulse-dot" aria-hidden="true" />
                <strong>
                  {currentSession
                    ? currentSession.topic_focus || activeDocName
                    : "Socratic AI Tutor Ready"}
                </strong>
              </div>

              <div className="tutor-header-badges">
                <span className="tutor-mode-pill">
                  <TutorIcon name={currentModeMeta.icon} size={13} />
                  {currentModeMeta.shortLabel}
                </span>
                {documents.length > 0 && selectedDocId && (
                  <span className="tutor-mode-pill">
                    <TutorIcon name="book" size={13} />
                    {activeDocName}
                  </span>
                )}
              </div>
            </div>

            <div className="tutor-messages-container" role="log">
              {/* Empty State (Clean Constellation - No Floating Robot) */}
              {!currentSession && !sessionLoading && (
                <div className="tutor-empty-state">
                  <div className="tutor-empty-visual" aria-hidden="true">
                    <span className="tutor-empty-icon-core">
                      <TutorIcon name="brain" size={32} />
                    </span>
                  </div>
                  <p className="tutor-section-kicker">Dialogue Ready</p>
                  <h3>Socratic Dialogue Grounded in Course Evidence</h3>
                  <p>
                    Select an uploaded course lecture above and click <strong>“Start New Session”</strong> to engage in interactive, step-by-step Socratic inquiry with verified page citations.
                  </p>
                  {documents.length > 0 ? (
                    <button
                      className="tutor-button tutor-button-primary"
                      onClick={handleStartNewSession}
                      type="button"
                    >
                      <TutorIcon name="sparkles" size={16} />
                      Start Tutoring on {activeDocName}
                    </button>
                  ) : (
                    <p className="tutor-empty-hint">
                      Please upload a course PDF in the <strong>Knowledge Vault (Materials)</strong> tab first.
                    </p>
                  )}
                </div>
              )}

              {/* Shimmering Loading State */}
              {sessionLoading && <TutorSkeleton />}

              {/* Message Feed */}
              {messages.map((msg, index) => {
                const isStudent = msg.role === "student";

                return (
                  <div
                    className={`tutor-bubble-wrapper ${
                      isStudent ? "tutor-bubble-student" : "tutor-bubble-tutor"
                    }`}
                    key={msg.message_id || index}
                  >
                    <div
                      className={`tutor-avatar ${
                        isStudent ? "tutor-avatar-student" : "tutor-avatar-tutor"
                      }`}
                      aria-hidden="true"
                    >
                      <TutorIcon name={isStudent ? "user" : "brain"} size={18} />
                    </div>

                    <div className="tutor-bubble-content">
                      <div className="tutor-bubble-meta">
                        <span className="tutor-bubble-author">
                          {isStudent ? user?.full_name || "You (Learner)" : "LearnMate AI Tutor"}
                        </span>
                        <span className="tutor-bubble-time">
                          {msg.created_at
                            ? new Date(msg.created_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : ""}
                        </span>
                      </div>

                      <div className="tutor-bubble-text">
                        {msg.content.split("\n\n").map((para, pIdx) => (
                          <p key={pIdx}>{para}</p>
                        ))}
                      </div>

                      {/* Inline Citations Tray in Tutor replies */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="tutor-citations-tray">
                          <span className="tutor-citations-label">
                            <TutorIcon name="book" size={13} /> Citations:
                          </span>
                          {msg.citations.map((c, cIdx) => (
                            <button
                              className="tutor-citation-chip"
                              key={cIdx}
                              onClick={() => {
                                setActiveCitations([c]);
                                handleHighlightCitation(cIdx);
                              }}
                              title={`Page ${c.page_number} of ${c.source || "Lecture"}`}
                              type="button"
                            >
                              Page {c.page_number}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Live Thinking Indicator */}
              {loading && (
                <div className="tutor-bubble-wrapper tutor-bubble-tutor">
                  <div className="tutor-avatar tutor-avatar-tutor" aria-hidden="true">
                    <TutorIcon name="brain" size={18} />
                  </div>
                  <div className="tutor-thinking-card">
                    <div className="tutor-typing-dots" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                    </div>
                    <span>Grounding response on lecture citations…</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Interactive Concept Check Challenge & Quick Follow-ups */}
            {(conceptCheck || suggestedFollowups.length > 0) && (
              <div className="tutor-interactive-panel">
                {conceptCheck && (
                  <div className="tutor-concept-check-card" role="region">
                    <div className="tutor-concept-check-icon" aria-hidden="true">
                      <TutorIcon name="target" size={20} />
                    </div>
                    <div className="tutor-concept-check-text">
                      <strong>Concept Check Challenge:</strong>
                      <p>{conceptCheck}</p>
                    </div>
                  </div>
                )}

                {suggestedFollowups.length > 0 && (
                  <div className="tutor-followup-cluster">
                    <span className="tutor-followup-label">
                      <TutorIcon name="lightbulb" size={14} /> Quick Follow-ups:
                    </span>
                    {suggestedFollowups.map((suggestion, idx) => (
                      <button
                        className="tutor-followup-pill"
                        disabled={loading}
                        key={idx}
                        onClick={() => handleSendMessage(suggestion)}
                        type="button"
                      >
                        “{suggestion}”
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Chat Input Bar */}
            <div className="tutor-input-bar">
              <div className="tutor-input-textarea-wrapper">
                <textarea
                  className="tutor-chat-textarea"
                  disabled={!currentSession || loading}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder={
                    currentSession
                      ? "Ask a conceptual question or respond to the Socratic prompt..."
                      : "Start a study session above to chat with the AI Tutor..."
                  }
                  ref={textareaRef}
                  rows={2}
                  value={inputMessage}
                />
                <span className="tutor-input-helper">
                  Press <kbd>Enter</kbd> to send, <kbd>Shift</kbd> + <kbd>Enter</kbd> for newline
                </span>
              </div>

              <button
                aria-label="Send message to AI Tutor"
                className="tutor-send-button"
                disabled={!currentSession || !inputMessage.trim() || loading}
                onClick={() => handleSendMessage()}
                type="button"
              >
                <span>Send</span>
                <TutorIcon name="send" size={16} />
              </button>
            </div>
          </div>

          {/* Right Column: Grounding Evidence Drawer */}
          <aside className="tutor-evidence-drawer" aria-label="Course Lecture Grounding Citations">
            <div className="tutor-evidence-header">
              <h3>
                <TutorIcon name="book" size={17} /> Verified Grounding
              </h3>
              <span className="tutor-evidence-count-badge">
                {activeCitations.length} cited {activeCitations.length === 1 ? "excerpt" : "excerpts"}
              </span>
            </div>

            <p className="tutor-evidence-desc">
              Passages retrieved via the <strong>Retrieval Agent</strong> semantic search directly from your course PDF.
            </p>

            <div className="tutor-citations-feed">
              {activeCitations.length === 0 ? (
                <div className="tutor-no-citations">
                  <span className="tutor-no-citations-icon" aria-hidden="true">
                    <TutorIcon name="search" size={24} />
                  </span>
                  <p>
                    No citations active yet. As you converse with the AI Tutor, verified lecture passages will appear here with page numbers.
                  </p>
                </div>
              ) : (
                activeCitations.map((chunk, idx) => (
                  <div
                    className={`tutor-evidence-chunk-card ${
                      highlightedCitationIndex === idx ? "tutor-chunk-highlighted" : ""
                    }`}
                    key={idx}
                  >
                    <div className="tutor-chunk-meta">
                      <span className="tutor-page-badge">
                        <TutorIcon name="document" size={13} /> Page {chunk.page_number}
                      </span>
                      <span className="tutor-source-label">
                        {chunk.source || activeDocName}
                      </span>
                    </div>

                    <blockquote className="tutor-chunk-quote">
                      “{chunk.text || chunk.text_preview}”
                    </blockquote>

                    {chunk.distance !== undefined && (
                      <div className="tutor-similarity-score">
                        <span>Match distance:</span>
                        <code>{chunk.distance.toFixed(4)}</code>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </aside>
        </div>
      </section>

      {/* Accessible Session History Modal */}
      <SessionHistoryModal
        currentSessionId={currentSession?.session_id}
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        onDeleteSession={handlePromptDeleteSession}
        onSelectSession={handleSelectPastSession}
        sessions={pastSessions}
      />

      {/* Accessible Delete Confirmation Modal */}
      <DeleteSessionModal
        isDeleting={isDeletingSession}
        onCancel={() => setSessionPendingDelete(null)}
        onConfirm={handleConfirmDeleteSession}
        session={sessionPendingDelete}
      />
    </div>
  );
}
