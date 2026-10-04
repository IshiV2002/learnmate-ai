export default function TutorSkeleton() {
  return (
    <div
      aria-busy="true"
      aria-label="Loading tutor workspace"
      aria-live="polite"
      className="tutor-skeleton-container"
      role="status"
    >
      <div className="tutor-skeleton-chat">
        <div className="tutor-skeleton-header">
          <span className="tutor-skeleton-block tutor-skeleton-title" />
          <span className="tutor-skeleton-block tutor-skeleton-badge" />
        </div>
        <div className="tutor-skeleton-messages">
          <div className="tutor-skeleton-bubble tutor-skeleton-bubble-incoming">
            <span className="tutor-skeleton-avatar" />
            <div className="tutor-skeleton-lines">
              <span className="tutor-skeleton-block" style={{ width: "85%" }} />
              <span className="tutor-skeleton-block" style={{ width: "65%" }} />
              <span className="tutor-skeleton-block" style={{ width: "40%" }} />
            </div>
          </div>
          <div className="tutor-skeleton-bubble tutor-skeleton-bubble-outgoing">
            <div className="tutor-skeleton-lines">
              <span className="tutor-skeleton-block" style={{ width: "70%" }} />
            </div>
            <span className="tutor-skeleton-avatar" />
          </div>
          <div className="tutor-skeleton-bubble tutor-skeleton-bubble-incoming">
            <span className="tutor-skeleton-avatar" />
            <div className="tutor-skeleton-lines">
              <span className="tutor-skeleton-block" style={{ width: "90%" }} />
              <span className="tutor-skeleton-block" style={{ width: "75%" }} />
            </div>
          </div>
        </div>
      </div>
      <div className="tutor-skeleton-evidence">
        <span className="tutor-skeleton-block tutor-skeleton-kicker" />
        <span className="tutor-skeleton-block tutor-skeleton-title" />
        <div className="tutor-skeleton-card" />
        <div className="tutor-skeleton-card" />
      </div>
      <span className="visually-hidden">Loading Socratic dialogue workspace...</span>
    </div>
  );
}
