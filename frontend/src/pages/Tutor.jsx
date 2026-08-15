import { useState, useEffect, useRef } from "react";
import {
  getDocuments,
  getStudentTutorSessions,
  getTutorSession,
  sendTutorMessage,
  startTutorSession,
  deleteTutorSession,
} from "../services/api.js";

export default function Tutor({ initialHandoff = null, onClearHandoff = null }) {
  const [studentId, setStudentId] = useState("student_demo_01");
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [topicFocus, setTopicFocus] = useState("");
  const [mode, setMode] = useState("socratic"); // 'socratic' | 'step_by_step' | 'concept_check'

  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [activeCitations, setActiveCitations] = useState([]);
  const [suggestedFollowups, setSuggestedFollowups] = useState([]);
  const [conceptCheck, setConceptCheck] = useState(null);

  const [pastSessions, setPastSessions] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showHistoryModal, setShowHistoryModal] = useState(false);

  const messagesEndRef = useRef(null);

  // Scroll chat to bottom when messages update
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load available documents
  useEffect(() => {
    async function loadDocs() {
      try {
        const docs = await getDocuments();
        setDocuments(docs || []);
        if (docs && docs.length > 0 && !selectedDocId) {
          setSelectedDocId(docs[0].document_id);
        }
      } catch (err) {
        console.error("Failed to load documents:", err);
      }
    }
    loadDocs();
  }, []);

  // Handle incoming initial handoff from Recommendations tab
  useEffect(() => {
    if (initialHandoff && initialHandoff.document_id) {
      setSelectedDocId(initialHandoff.document_id);
      if (initialHandoff.target_topics && initialHandoff.target_topics.length > 0) {
        setTopicFocus(initialHandoff.target_topics[0]);
      }
      if (initialHandoff.student_id) {
        setStudentId(initialHandoff.student_id);
      }
      // Auto-start remedial session
      initSessionFromHandoff(initialHandoff);
    }
  }, [initialHandoff]);

  // Load student session list
  useEffect(() => {
    if (studentId) {
      loadStudentSessions();
    }
  }, [studentId]);

  async function loadStudentSessions() {
    try {
      const list = await getStudentTutorSessions(studentId);
      setPastSessions(list || []);
    } catch (err) {
      console.warn("Could not load past sessions:", err);
    }
  }

  async function initSessionFromHandoff(handoff) {
    setSessionLoading(true);
    setError(null);
    try {
      const payload = {
        student_id: handoff.student_id || studentId,
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
    } catch (err) {
      setError(err.message || "Could not start remedial tutoring session.");
    } finally {
      setSessionLoading(false);
    }
  }

  async function handleStartNewSession(e) {
    if (e) e.preventDefault();
    if (!selectedDocId) {
      setError("Please select or upload a document first.");
      return;
    }

    setSessionLoading(true);
    setError(null);
    if (onClearHandoff) onClearHandoff();

    try {
      const payload = {
        student_id: studentId.trim() || "student_demo_01",
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
      loadStudentSessions();
    } catch (err) {
      setError(err.message || "Failed to start AI tutoring session.");
    } finally {
      setSessionLoading(false);
    }
  }

  async function handleSelectPastSession(sessionId) {
    setSessionLoading(true);
    setError(null);
    setShowHistoryModal(false);
    try {
      const session = await getTutorSession(sessionId);
      setCurrentSession(session);
      setMessages(session.messages || []);
      setSelectedDocId(session.document_id);
      setMode(session.mode);
      setTopicFocus(session.topic_focus);
      // Collect citations from recent tutor message
      const lastTutorMsg = [...session.messages].reverse().find((m) => m.role === "tutor");
      setActiveCitations(lastTutorMsg?.citations || []);
      setSuggestedFollowups([]);
      setConceptCheck(null);
    } catch (err) {
      setError(err.message || "Could not load session.");
    } finally {
      setSessionLoading(false);
    }
  }

  async function handleDeleteSession(sessionId, e) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this tutoring session?")) return;
    try {
      await deleteTutorSession(sessionId);
      if (currentSession?.session_id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
        setActiveCitations([]);
      }
      loadStudentSessions();
    } catch (err) {
      alert("Failed to delete session: " + err.message);
    }
  }

  async function handleSendMessage(textToSend = null) {
    const text = (textToSend || inputMessage).trim();
    if (!text || !currentSession) return;

    setInputMessage("");
    setLoading(true);
    setError(null);

    // Optimistically add student message
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
    } catch (err) {
      setError(err.message || "Failed to receive response from Tutor Agent.");
    } finally {
      setLoading(false);
    }
  }

  const activeDocName =
    documents.find((d) => d.document_id === selectedDocId)?.original_filename || "Course Lecture";

  return (
    <div className="tutor-page-layout">
      {/* Top Banner / Session Setup Bar */}
      <div className="tutor-control-panel">
        <div className="tutor-header-row">
          <div>
            <h2 className="tutor-main-title">💬 AI Socratic Tutor</h2>
            <p className="tutor-subtitle">
              Pedagogical conversational learning grounded strictly in your course lecture materials.
            </p>
          </div>

          <div className="tutor-action-group">
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => setShowHistoryModal(true)}
            >
              📜 Past Sessions ({pastSessions.length})
            </button>
            <button
              type="button"
              className="btn-primary btn-sm"
              onClick={handleStartNewSession}
              disabled={sessionLoading || documents.length === 0}
            >
              ✨ Start New Session
            </button>
          </div>
        </div>

        {/* Configuration Row */}
        <div className="tutor-config-grid">
          <div className="form-group">
            <label>👤 Student ID</label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="e.g. student_demo_01"
            />
          </div>

          <div className="form-group">
            <label>📚 Course Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              disabled={documents.length === 0}
            >
              {documents.length === 0 && <option value="">No documents uploaded</option>}
              {documents.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {doc.original_filename} ({doc.page_count} pages)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>🎯 Concept / Topic Focus</label>
            <input
              type="text"
              value={topicFocus}
              onChange={(e) => setTopicFocus(e.target.value)}
              placeholder="e.g. Vector Space Scoring, Inverted Index..."
            />
          </div>

          <div className="form-group">
            <label>🧠 Teaching Mode</label>
            <div className="mode-toggle-group">
              <button
                type="button"
                className={`mode-btn ${mode === "socratic" ? "active" : ""}`}
                onClick={() => setMode("socratic")}
                title="Guides you with probing questions to discover answers"
              >
                🧠 Socratic
              </button>
              <button
                type="button"
                className={`mode-btn ${mode === "step_by_step" ? "active" : ""}`}
                onClick={() => setMode("step_by_step")}
                title="Structured numbered breakdown with intuitive analogies"
              >
                🪜 Step-by-Step
              </button>
              <button
                type="button"
                className={`mode-btn ${mode === "concept_check" ? "active" : ""}`}
                onClick={() => setMode("concept_check")}
                title="Concise recap followed by a quick comprehension challenge"
              >
                🎯 Concept Check
              </button>
            </div>
          </div>
        </div>

        {/* Remedial Handoff Context Banner */}
        {initialHandoff && (
          <div className="handoff-alert-banner">
            <div className="handoff-alert-icon">🤝</div>
            <div className="handoff-alert-content">
              <strong>Inter-Agent Remedial Handoff Active:</strong>
              <span>
                Personalized review initialized by Recommendation Agent for:{" "}
                <em>{initialHandoff.target_topics?.join(", ") || "Identified Knowledge Gaps"}</em> (Severity:{" "}
                <span className="severity-badge-pill">{initialHandoff.gap_severity}</span>)
              </span>
            </div>
            {onClearHandoff && (
              <button
                type="button"
                className="close-banner-btn"
                onClick={onClearHandoff}
                title="Dismiss Handoff Banner"
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="error-alert">
          <span>⚠️ {error}</span>
          <button type="button" onClick={() => setError(null)}>
            ✕
          </button>
        </div>
      )}

      {/* Main Tutoring Area: Chat Thread + Evidence Citations Drawer */}
      <div className="tutor-workspace-grid">
        {/* Chat Section */}
        <div className="tutor-chat-card">
          <div className="chat-card-header">
            <div className="session-status-indicator">
              <span className="pulse-dot"></span>
              <strong>{currentSession ? `Session: ${currentSession.topic_focus || activeDocName}` : "AI Tutor Ready"}</strong>
            </div>
            <div className="active-mode-badge">
              Mode: {mode === "socratic" ? "🧠 Socratic Discovery" : mode === "step_by_step" ? "🪜 Step-by-Step Breakdown" : "🎯 Concept Check"}
            </div>
          </div>

          <div className="chat-messages-container">
            {!currentSession && !sessionLoading && (
              <div className="empty-chat-state">
                <div className="empty-icon">🤖</div>
                <h3>Welcome to LearnMate AI Tutoring!</h3>
                <p>
                  Click <strong>"Start New Session"</strong> above or select a topic from your quiz recommendations to start a guided, lecture-grounded Socratic study session.
                </p>
                {documents.length > 0 && (
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleStartNewSession}
                  >
                    Start Tutoring on {documents[0].original_filename}
                  </button>
                )}
              </div>
            )}

            {sessionLoading && (
              <div className="chat-loading-state">
                <div className="spinner"></div>
                <p>Preparing Socratic pedagogy and indexing lecture context...</p>
              </div>
            )}

            {messages.map((msg, index) => (
              <div
                key={msg.message_id || index}
                className={`chat-bubble-wrapper ${msg.role === "student" ? "student-wrapper" : "tutor-wrapper"}`}
              >
                <div className="bubble-avatar">
                  {msg.role === "student" ? "👤" : "🎓"}
                </div>
                <div className="bubble-content-box">
                  <div className="bubble-header-line">
                    <span className="bubble-author">
                      {msg.role === "student" ? "You (Student)" : "LearnMate AI Tutor"}
                    </span>
                    <span className="bubble-time">
                      {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                    </span>
                  </div>

                  <div className="bubble-body-text">
                    {msg.content.split("\n\n").map((para, pIdx) => (
                      <p key={pIdx}>{para}</p>
                    ))}
                  </div>

                  {/* Inline citation pill badges */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="bubble-citations-tray">
                      <span className="citations-label">📑 Lecture Citations:</span>
                      {msg.citations.map((c, cIdx) => (
                        <button
                          key={cIdx}
                          type="button"
                          className="citation-chip"
                          onClick={() => setActiveCitations([c])}
                          title={`Page ${c.page_number} of ${c.source || "Lecture"}`}
                        >
                          Page {c.page_number}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble-wrapper tutor-wrapper">
                <div className="bubble-avatar">🎓</div>
                <div className="bubble-content-box tutor-thinking-box">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <small>Grounding response on lecture citations...</small>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Interactive Suggestions & Concept Check Callout */}
          {conceptCheck && (
            <div className="concept-check-card">
              <div className="concept-check-header">
                <strong>🎯 Concept Check Challenge:</strong>
              </div>
              <p className="concept-check-text">{conceptCheck}</p>
            </div>
          )}

          {suggestedFollowups.length > 0 && (
            <div className="followup-chips-cluster">
              <span className="followup-heading">💡 Quick Follow-Ups:</span>
              {suggestedFollowups.map((suggestion, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="followup-chip-btn"
                  onClick={() => handleSendMessage(suggestion)}
                  disabled={loading}
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          )}

          {/* Chat Input Bar */}
          <div className="chat-input-bar">
            <textarea
              rows={2}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder={
                currentSession
                  ? "Type your question or explanation... (Enter to send, Shift+Enter for new line)"
                  : "Start a session to chat with the AI Tutor..."
              }
              disabled={!currentSession || loading}
            />
            <button
              type="button"
              className="send-message-btn"
              onClick={() => handleSendMessage()}
              disabled={!currentSession || !inputMessage.trim() || loading}
            >
              {loading ? "..." : "Send 🚀"}
            </button>
          </div>
        </div>

        {/* Right Sidebar: Grounding Evidence & Lecture Citations */}
        <div className="tutor-evidence-drawer">
          <div className="evidence-header">
            <h3>📑 Verified Lecture Grounding</h3>
            <span className="evidence-count-badge">
              {activeCitations.length} cited {activeCitations.length === 1 ? "excerpt" : "excerpts"}
            </span>
          </div>

          <p className="evidence-desc">
            Passages retrieved via the <strong>Retrieval Agent</strong> semantic search to prevent hallucination.
          </p>

          <div className="citations-feed">
            {activeCitations.length === 0 ? (
              <div className="no-citations-state">
                <span className="no-citations-icon">🔍</span>
                <p>No citations active. As you converse with the AI Tutor, verified lecture passages will appear here with page numbers.</p>
              </div>
            ) : (
              activeCitations.map((chunk, idx) => (
                <div key={idx} className="evidence-chunk-card">
                  <div className="evidence-chunk-meta">
                    <span className="page-badge">📄 Page {chunk.page_number}</span>
                    <span className="source-label">{chunk.source || activeDocName}</span>
                  </div>
                  <div className="evidence-chunk-text">
                    "{chunk.text || chunk.text_preview}"
                  </div>
                  {chunk.distance !== undefined && (
                    <div className="similarity-score">
                      Semantic match distance: <code>{chunk.distance.toFixed(4)}</code>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* MODAL: Past Sessions History */}
      {showHistoryModal && (
        <div className="modal-overlay" onClick={() => setShowHistoryModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📜 Student Tutoring History ({studentId})</h3>
              <button
                type="button"
                className="close-modal-btn"
                onClick={() => setShowHistoryModal(false)}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              {pastSessions.length === 0 ? (
                <p className="no-data-msg">No past sessions found for student '{studentId}'.</p>
              ) : (
                <div className="session-history-list">
                  {pastSessions.map((s) => (
                    <div
                      key={s.session_id}
                      className={`session-history-item ${currentSession?.session_id === s.session_id ? "active-session-item" : ""}`}
                      onClick={() => handleSelectPastSession(s.session_id)}
                    >
                      <div className="session-item-main">
                        <div className="session-item-title">
                          <strong>{s.topic_focus || "Course Review"}</strong>
                          <span className="session-mode-pill">{s.mode}</span>
                        </div>
                        <div className="session-item-date">
                          📅 {new Date(s.updated_at || s.created_at).toLocaleString()}
                        </div>
                      </div>
                      <button
                        type="button"
                        className="delete-session-btn"
                        onClick={(e) => handleDeleteSession(s.session_id, e)}
                        title="Delete Session"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowHistoryModal(false)}
              >
                Close History
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
