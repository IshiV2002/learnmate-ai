import { useEffect, useState } from "react";
import TutorIcon from "./TutorIcon.jsx";
import { formatSessionDate, getModeMeta } from "./tutorUtils.js";

export default function SessionHistoryModal({
  isOpen,
  sessions = [],
  currentSessionId,
  onClose,
  onSelectSession,
  onDeleteSession,
}) {
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (!isOpen) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleEscape(event) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredSessions = sessions.filter((s) => {
    const term = searchTerm.toLowerCase().trim();
    if (!term) return true;
    const topic = (s.topic_focus || "").toLowerCase();
    const mode = (s.mode || "").toLowerCase();
    return topic.includes(term) || mode.includes(term);
  });

  return (
    <div className="tutor-modal-layer">
      <button
        aria-label="Close session history modal"
        className="tutor-modal-backdrop"
        onClick={onClose}
        type="button"
      />
      <section
        aria-describedby="history-modal-description"
        aria-labelledby="history-modal-title"
        aria-modal="true"
        className="tutor-history-dialog"
        role="dialog"
      >
        <div className="tutor-history-header">
          <div>
            <span className="tutor-dialog-eyebrow">Workspace Dialogue Records</span>
            <h2 id="history-modal-title">Tutoring History ({sessions.length})</h2>
            <p id="history-modal-description">
              Revisit past Socratic sessions, continue active dialogue threads, or manage your history.
            </p>
          </div>
          <button
            aria-label="Close dialog"
            className="tutor-icon-button"
            onClick={onClose}
            type="button"
          >
            <TutorIcon name="close" size={18} />
          </button>
        </div>

        <div className="tutor-history-search-row">
          <div className="tutor-search-wrapper">
            <TutorIcon className="tutor-search-icon" name="search" size={16} />
            <input
              className="tutor-search-input"
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter sessions by topic or mode..."
              type="text"
              value={searchTerm}
            />
            {searchTerm && (
              <button
                aria-label="Clear filter"
                className="tutor-search-clear"
                onClick={() => setSearchTerm("")}
                type="button"
              >
                <TutorIcon name="close" size={14} />
              </button>
            )}
          </div>
        </div>

        <div className="tutor-history-body">
          {filteredSessions.length === 0 ? (
            <div className="tutor-history-empty">
              <span className="tutor-history-empty-icon">
                <TutorIcon name="history" size={28} />
              </span>
              <h3>{searchTerm ? "No matching sessions found" : "No tutoring sessions yet"}</h3>
              <p>
                {searchTerm
                  ? "Try searching for a different keyword or clear the filter."
                  : "Start a new lecture-grounded session to begin building your Socratic study history."}
              </p>
            </div>
          ) : (
            <div className="tutor-history-list">
              {filteredSessions.map((session) => {
                const isCurrent = currentSessionId === session.session_id;
                const modeMeta = getModeMeta(session.mode);

                return (
                  <div
                    className={`tutor-history-card ${isCurrent ? "tutor-history-card-active" : ""}`}
                    key={session.session_id}
                    onClick={() => onSelectSession(session.session_id)}
                  >
                    <div className="tutor-history-card-main">
                      <div className="tutor-history-card-title-row">
                        <span className="tutor-history-card-icon">
                          <TutorIcon name={modeMeta.icon} size={17} />
                        </span>
                        <h4>{session.topic_focus || "Course Lecture Review"}</h4>
                        {isCurrent && (
                          <span className="tutor-active-pill">Active Session</span>
                        )}
                      </div>

                      <div className="tutor-history-card-meta">
                        <span className="tutor-meta-tag">
                          <TutorIcon name="brain" size={13} /> {modeMeta.shortLabel}
                        </span>
                        <span className="tutor-meta-tag">
                          <TutorIcon name="clock" size={13} />{" "}
                          {formatSessionDate(session.updated_at || session.created_at)}
                        </span>
                      </div>
                    </div>

                    <div className="tutor-history-card-actions">
                      <button
                        aria-label="Resume this session"
                        className="tutor-button tutor-button-secondary tutor-button-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectSession(session.session_id);
                        }}
                        type="button"
                      >
                        Resume
                        <TutorIcon name="arrow-right" size={14} />
                      </button>
                      <button
                        aria-label="Delete this session"
                        className="tutor-delete-icon-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session);
                        }}
                        title="Delete session"
                        type="button"
                      >
                        <TutorIcon name="trash" size={16} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="tutor-history-footer">
          <button
            className="tutor-button tutor-button-secondary"
            onClick={onClose}
            type="button"
          >
            Close History
          </button>
        </div>
      </section>
    </div>
  );
}
