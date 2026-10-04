import QuizIcon from "./QuizIcon.jsx";
import { getDifficultyMeta } from "./quizUtils.js";

function MetadataItem({ icon, label, value }) {
  return (
    <div className="quiz-metadata-item">
      <QuizIcon name={icon} size={16} />
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function SavedQuizCard({
  quiz,
  documentName,
  isDeleting,
  onTakeQuiz,
  onDelete,
}) {
  const title = quiz.title || "Untitled Assessment";
  const topic = quiz.topic || "General Course Topics";
  const diffMeta = getDifficultyMeta(quiz.difficulty);
  const questionCount = quiz.total_questions || quiz.questions?.length || 0;

  return (
    <article className="saved-quiz-card">
      <div className="quiz-card-accent" aria-hidden="true" />
      <div className="quiz-card-heading">
        <span className="quiz-card-icon" aria-hidden="true">
          <QuizIcon name="sparkles" size={24} />
          <small>QUIZ</small>
        </span>
        <div className="quiz-title-group">
          <span className="quiz-indexed-label">
            <span className="quiz-ready-dot" aria-hidden="true" />
            AI Grounded Assessment
          </span>
          <h3 title={title}>{title}</h3>
          <p>Topic: <strong>{topic}</strong></p>
        </div>
        <button
          aria-label={`Delete ${title}`}
          className="quiz-delete-button"
          disabled={isDeleting}
          onClick={() => onDelete(quiz)}
          type="button"
        >
          <QuizIcon name="trash" size={17} />
          <span>{isDeleting ? "Deleting…" : "Delete"}</span>
        </button>
      </div>

      <dl className="quiz-metadata-grid">
        <MetadataItem
          icon="layers"
          label="Questions"
          value={`${questionCount} items`}
        />
        <MetadataItem
          icon="target"
          label="Difficulty"
          value={diffMeta.shortLabel}
        />
        <MetadataItem
          icon="brain"
          label="Pedagogy"
          value={quiz.cognitive_level || "Bloom Mapped"}
        />
      </dl>

      <div className="quiz-card-footer">
        <div className="quiz-grounding-note">
          <QuizIcon name="book" size={15} />
          <span>Grounded in {documentName || "Target Lecture"}</span>
        </div>
        <button
          className="quiz-button quiz-button-primary quiz-button-small"
          onClick={() => onTakeQuiz(quiz.quiz_id)}
          type="button"
        >
          <QuizIcon name="play" size={14} />
          Take Quiz
        </button>
      </div>
    </article>
  );
}

export default SavedQuizCard;
