import { useEffect } from "react";
import TutorIcon from "./TutorIcon.jsx";

export default function DeleteSessionModal({
  session,
  isDeleting,
  onCancel,
  onConfirm,
}) {
  useEffect(() => {
    if (!session) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleEscape(event) {
      if (event.key === "Escape" && !isDeleting) {
        onCancel();
      }
    }

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = previousOverflow;
    };
  }, [session, isDeleting, onCancel]);

  if (!session) return null;

  const title = session.topic_focus || "this tutoring session";

  return (
    <div className="tutor-modal-layer">
      <button
        aria-label="Close delete confirmation"
        className="tutor-modal-backdrop"
        disabled={isDeleting}
        onClick={onCancel}
        type="button"
      />
      <section
        aria-describedby="delete-session-description"
        aria-labelledby="delete-session-title"
        aria-modal="true"
        className="tutor-delete-dialog"
        role="dialog"
      >
        <span className="tutor-delete-dialog-icon" aria-hidden="true">
          <TutorIcon name="trash" size={24} />
        </span>
        <p className="tutor-dialog-eyebrow">Remove dialogue history</p>
        <h2 id="delete-session-title">Delete “{title}”?</h2>
        <p id="delete-session-description">
          This permanently removes this Socratic dialogue session and its entire message history from your workspace.
        </p>
        <div className="tutor-dialog-actions">
          <button
            autoFocus
            className="tutor-button tutor-button-secondary"
            disabled={isDeleting}
            onClick={onCancel}
            type="button"
          >
            Keep session
          </button>
          <button
            className="tutor-button tutor-button-danger"
            disabled={isDeleting}
            onClick={onConfirm}
            type="button"
          >
            <TutorIcon name="trash" size={17} />
            {isDeleting ? "Deleting…" : "Delete permanently"}
          </button>
        </div>
      </section>
    </div>
  );
}
