import { useEffect, useState } from "react";

import MaterialIcon from "./MaterialIcon.jsx";

function ProcessingJourney({ fileName, onStudy = null, status }) {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    if (status === "idle") {
      setActiveStage(0);
      return undefined;
    }

    if (status === "complete") {
      setActiveStage(4);
      return undefined;
    }

    if (status !== "processing") {
      return undefined;
    }

    setActiveStage(0);
    const stageTimers = [
      window.setTimeout(() => setActiveStage(1), 800),
      window.setTimeout(() => setActiveStage(2), 1900),
      window.setTimeout(() => setActiveStage(3), 3200),
    ];

    return () => {
      stageTimers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [fileName, status]);

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
  const progressMessages = [
    "Uploading your material",
    isImage ? "Reading the image with OCR" : "Reading the PDF pages",
    "Preparing searchable text",
    "Creating knowledge sections",
    "Knowledge source ready",
  ];

  function getStageState(index) {
    if (isComplete || index < activeStage) {
      return "complete";
    }

    if (index === activeStage) {
      return isError ? "error" : "active";
    }

    return "pending";
  }

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
                : progressMessages[activeStage]}
          </strong>
          <small>{fileName}</small>
        </div>
      </div>

      <ol className="vault-journey-track" aria-label="Material processing journey">
        {stages.map((stage, index) => {
          const stageState = getStageState(index);

          return (
            <li
              aria-current={stageState === "active" ? "step" : undefined}
              className={`vault-stage-${stageState}`}
              key={stage}
            >
              <span className="vault-stage-node" aria-hidden="true">
                {stageState === "complete" ? <MaterialIcon name="check" size={13} /> : index + 1}
              </span>
              <span>{stage}</span>
            </li>
          );
        })}
      </ol>

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
