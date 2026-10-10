import MaterialIcon from "./MaterialIcon.jsx";

function ProcessingJourney({ fileName, onStudy = null, status }) {
  if (status === "idle") {
    return null;
  }

  const isComplete = status === "complete";
  const isError = status === "error";
  const isImage = /\.(png|jpe?g)$/i.test(fileName);
  const stages = [
    "Upload",
    isImage ? "Read image with OCR" : "Read PDF",
    "Process text",
    "Create knowledge sections",
    "Ready",
  ];

  return (
    <div
      aria-live="polite"
      className={`vault-journey vault-journey-${status}`}
      role="status"
    >
      <div className="vault-journey-heading">
        <span className="vault-journey-status-icon" aria-hidden="true">
          {isComplete ? (
            <MaterialIcon name="check" />
          ) : isError ? (
            <MaterialIcon name="close" />
          ) : (
            <span className="vault-processing-spinner" />
          )}
        </span>
        <div>
          <strong>
            {isComplete
              ? "Knowledge source ready"
              : isError
                ? "Processing was not completed"
                : "Uploading and processing securely"}
          </strong>
          <small>{fileName}</small>
        </div>
      </div>

      <ol className="vault-journey-track" aria-label="Material processing journey">
        {stages.map((stage, index) => (
          <li
            className={isComplete ? "vault-stage-complete" : isError ? "vault-stage-error" : "vault-stage-active"}
            key={stage}
          >
            <span className="vault-stage-node" aria-hidden="true">
              {isComplete ? <MaterialIcon name="check" size={13} /> : index + 1}
            </span>
            <span>{stage}</span>
          </li>
        ))}
      </ol>

      {!isComplete && !isError && (
        <p className="vault-journey-note">
          The backend completes validation, extraction, page-aware chunking, and indexing in one request, so exact stage timing is not available.
        </p>
      )}

      {isComplete && onStudy && (
        <div style={{ marginTop: "14px", display: "flex", justifyContent: "flex-end" }}>
          <button
            className="vault-button vault-button-primary"
            onClick={onStudy}
            type="button"
          >
            <MaterialIcon name="tutor" size={16} />
            <span>Study this Material with AI Tutor →</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default ProcessingJourney;
