import QuizIcon from "./QuizIcon.jsx";

const stages = [
  "Target Material",
  "Vector Retrieval",
  "Bloom Synthesis",
  "Pedagogy Grounding",
  "Ready",
];

function QuizGenerationJourney({ topic, documentName, status }) {
  if (status === "idle") {
    return null;
  }

  const isComplete = status === "complete";
  const isError = status === "error";

  return (
    <div
      aria-live="polite"
      className={`quiz-journey quiz-journey-${status}`}
      role="status"
    >
      <div className="quiz-journey-heading">
        <span className="quiz-journey-status-icon" aria-hidden="true">
          {isComplete ? (
            <QuizIcon name="check" size={18} />
          ) : isError ? (
            <QuizIcon name="close" size={18} />
          ) : (
            <span className="quiz-processing-spinner" />
          )}
        </span>
        <div>
          <strong>
            {isComplete
              ? "Assessment Synthesized & Ready"
              : isError
                ? "Generation encountered an issue"
                : "Retrieving context & synthesizing questions…"}
          </strong>
          <small>
            {topic ? `Topic: ${topic} · ` : ""}Source: {documentName || "Target Lecture"}
          </small>
        </div>
      </div>

      <ol className="quiz-journey-track" aria-label="Quiz synthesis progression">
        {stages.map((stage, index) => (
          <li
            className={
              isComplete
                ? "quiz-stage-complete"
                : isError
                  ? "quiz-stage-error"
                  : "quiz-stage-active"
            }
            key={stage}
          >
            <span className="quiz-stage-node" aria-hidden="true">
              {isComplete ? <QuizIcon name="check" size={13} /> : index + 1}
            </span>
            <span>{stage}</span>
          </li>
        ))}
      </ol>

      {!isComplete && !isError && (
        <p className="quiz-journey-note">
          The Retrieval Agent fetches semantic chunks from your indexed PDF while the Quiz Agent designs Bloom-aligned questions with page citations.
        </p>
      )}
    </div>
  );
}

export default QuizGenerationJourney;
