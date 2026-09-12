import { useEffect } from "react";

import MaterialIcon from "./MaterialIcon.jsx";

function DeleteDocumentModal({ document: targetDocument, isDeleting, onCancel, onConfirm }) {
  useEffect(() => {
    if (!targetDocument) {
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
  }, [targetDocument, isDeleting, onCancel]);

  if (!targetDocument) {
    return null;
  }

  const filename = targetDocument.original_filename || "this document";

  return (
    <div className="vault-modal-layer">
      <button
        aria-label="Close delete confirmation"
        className="vault-modal-backdrop"
        disabled={isDeleting}
        onClick={onCancel}
        type="button"
      />
      <section
        aria-describedby="delete-document-description"
        aria-labelledby="delete-document-title"
        aria-modal="true"
        className="vault-delete-dialog"
        role="dialog"
      >
        <span className="vault-delete-dialog-icon" aria-hidden="true">
          <MaterialIcon name="trash" size={24} />
        </span>
        <p className="vault-dialog-eyebrow">Remove knowledge source</p>
        <h2 id="delete-document-title">Delete “{filename}”?</h2>
        <p id="delete-document-description">
          This permanently removes the stored PDF, its metadata, and its searchable sections. Learning agents will no longer be able to retrieve from it.
        </p>
        <div className="vault-dialog-actions">
          <button
            autoFocus
            className="vault-button vault-button-secondary"
            disabled={isDeleting}
            onClick={onCancel}
            type="button"
          >
            Keep source
          </button>
          <button
            className="vault-button vault-button-danger"
            disabled={isDeleting}
            onClick={onConfirm}
            type="button"
          >
            <MaterialIcon name="trash" size={17} />
            {isDeleting ? "Deleting…" : "Delete permanently"}
          </button>
        </div>
      </section>
    </div>
  );
}

export default DeleteDocumentModal;
