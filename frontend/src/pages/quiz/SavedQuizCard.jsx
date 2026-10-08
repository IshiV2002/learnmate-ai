import QuizIcon from "./QuizIcon.jsx";
import {
  estimateQuizDuration,
  formatQuizDate,
  getDifficultyMeta,
} from "./quizUtils.js";

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
  const estDuration = estimateQuizDuration(questionCount);
  const cognitiveLevels = [
    ...new Set(
      (quiz.questions || [])
        .map((question) => question.cognitive_level)
        .filter(Boolean),
    ),
  ];
  const bloomLevel = cognitiveLevels.length
    ? cognitiveLevels
        .map((level) => level.charAt(0).toUpperCase() + level.slice(1))
        .join(", ")
    : "Bloom mapped";
  const createdDate = formatQuizDate(quiz.created_at);
  const isMixed = Boolean(quiz.document_id && quiz.document_id.includes(","));
  const docCount = isMixed ? quiz.document_id.split(",").filter(Boolean).length : 1;
  const displayDocName = isMixed
    ? `Mixed Assessment (${docCount} Course Sources)`
    : (documentName || "Target Course Material");

  return (
    <article className="saved-quiz-card">
      <div className="quiz-card-accent" aria-hidden="true" />

      {/* Card Header: Topic Badge, Difficulty Tier, and Spacious Title */}
      <div className="quiz-card-header">
        <div className="quiz-card-tags-row">
          <span className="quiz-topic-pill" title={`Topic: ${topic}`}>
            <span className="quiz-ready-dot" aria-hidden="true" />
            <span className="quiz-topic-text">{topic}</span>
          </span>
          {isMixed && (
            <span className="quiz-diff-badge quiz-diff-mixed" title={`Synthesized from ${docCount} documents`}>
              <QuizIcon name="layers" size={12} />
              Mixed ({docCount} Docs)
            </span>
          )}
          <span
            className={`quiz-diff-badge quiz-diff-${diffMeta.shortLabel.toLowerCase()}`}
          >
            <QuizIcon name="target" size={12} />
            {diffMeta.shortLabel}
          </span>
        </div>

        <h3 className="quiz-card-title" title={title}>
          {title}
        </h3>
      </div>

      {/* Modern Meta Pill Chips */}
      <div className="quiz-card-meta-chips">
        <div className="quiz-meta-chip">
          <QuizIcon name="layers" size={14} />
          <span>
            <strong>{questionCount}</strong>{" "}
            {questionCount === 1 ? "Question" : "Questions"}
          </span>
        </div>
        <div className="quiz-meta-chip">
          <QuizIcon name="clock" size={14} />
          <span>{estDuration}</span>
        </div>
        <div className="quiz-meta-chip" title={`Cognitive Level: ${bloomLevel}`}>
          <QuizIcon name="brain" size={14} />
          <span>{bloomLevel}</span>
        </div>
      </div>

      {/* Grounding Source Info */}
      <div className="quiz-card-grounding">
        <QuizIcon name={isMixed ? "layers" : "document"} size={13} />
        <span
          className="quiz-grounding-doc"
          title={displayDocName}
        >
          {displayDocName}
        </span>
        <span className="quiz-grounding-dot" aria-hidden="true" />
        <span className="quiz-grounding-date">{createdDate}</span>
      </div>

      {/* Card Footer: Balanced Action Bar with Repositioned Delete Button */}
      <div className="quiz-card-footer">
        <button
          aria-label={`Delete assessment ${title}`}
          className="quiz-card-delete-button"
          disabled={isDeleting}
          onClick={() => onDelete(quiz)}
          title="Delete this assessment"
          type="button"
        >
          <QuizIcon name="trash" size={15} />
          <span>{isDeleting ? "Deleting…" : "Delete"}</span>
        </button>

        <button
          className="quiz-button quiz-button-primary quiz-button-small quiz-card-take-btn"
          onClick={() => onTakeQuiz(quiz.quiz_id)}
          type="button"
        >
          <QuizIcon name="play" size={13} />
          Take Quiz
        </button>
      </div>
    </article>
  );
}

export default SavedQuizCard;

