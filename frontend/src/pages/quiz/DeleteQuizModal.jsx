import { useEffect } from "react";
import QuizIcon from "./QuizIcon.jsx";

function DeleteQuizModal({ quiz, isDeleting, onCancel, onConfirm }) {
  useEffect(() => {
    if (!quiz) {
      return undefined;
    }

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
  }, [quiz, isDeleting, onCancel]);

  if (!quiz) {
    return null;
  }

  const title = quiz.title || "this quiz";

  return (
    <div className="quiz-modal-layer">
      <button
        aria-label="Close delete confirmation"
        className="quiz-modal-backdrop"
        disabled={isDeleting}
        onClick={onCancel}
        type="button"
      />
      <section
        aria-describedby="delete-quiz-description"
        aria-labelledby="delete-quiz-title"
        aria-modal="true"
        className="quiz-delete-dialog"
        role="dialog"
      >
        <span className="quiz-delete-dialog-icon" aria-hidden="true">
          <QuizIcon name="trash" size={24} />
        </span>
        <p className="quiz-dialog-eyebrow">Remove assessment</p>
        <h2 id="delete-quiz-title">Delete “{title}”?</h2>
        <p id="delete-quiz-description">
          This permanently removes this synthesized assessment, all its questions, and past evaluation records.
        </p>
        <div className="quiz-dialog-actions">
          <button
            autoFocus
            className="quiz-button quiz-button-secondary"
            disabled={isDeleting}
            onClick={onCancel}
            type="button"
          >
            Keep quiz
          </button>
          <button
            className="quiz-button quiz-button-danger"
            disabled={isDeleting}
            onClick={onConfirm}
            type="button"
          >
            <QuizIcon name="trash" size={17} />
            {isDeleting ? "Deleting…" : "Delete permanently"}
          </button>
        </div>
      </section>
    </div>
  );
}

export default DeleteQuizModal;
