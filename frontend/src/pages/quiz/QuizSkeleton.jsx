function QuizSkeleton() {
  return (
    <div
      aria-busy="true"
      aria-label="Loading available assessments"
      aria-live="polite"
      className="quiz-skeleton-grid"
      role="status"
    >
      {[0, 1, 2, 3].map((item) => (
        <div className="quiz-source-skeleton" key={item}>
          <span className="quiz-skeleton-block quiz-skeleton-icon" />
          <div className="quiz-skeleton-copy">
            <span className="quiz-skeleton-block quiz-skeleton-kicker" />
            <span className="quiz-skeleton-block quiz-skeleton-title" />
            <span className="quiz-skeleton-block quiz-skeleton-detail" />
          </div>
          <div className="quiz-skeleton-metadata">
            <span className="quiz-skeleton-block" />
            <span className="quiz-skeleton-block" />
            <span className="quiz-skeleton-block" />
          </div>
        </div>
      ))}
      <span className="visually-hidden">Loading assessments.</span>
    </div>
  );
}

export default QuizSkeleton;
