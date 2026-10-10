import { useEffect, useRef, useState } from "react";

import { getDocumentContent } from "../../services/api.js";
import MaterialIcon from "./MaterialIcon.jsx";

function getPdfFilename(filename) {
  const safeName = filename || "study-material";

  if (/\.pdf$/i.test(safeName)) {
    return safeName;
  }

  return `${safeName.replace(/\.[^.]+$/, "") || "study-material"}.pdf`;
}

function DocumentViewerModal({ document, onClose }) {
  const [documentUrl, setDocumentUrl] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const closeButtonRef = useRef(null);
  const filename = document?.original_filename || "Untitled material";
  const downloadFilename = getPdfFilename(filename);

  useEffect(() => {
    if (!document?.document_id) {
      return undefined;
    }

    let active = true;
    let objectUrl = "";
    setDocumentUrl("");
    setErrorMessage("");

    getDocumentContent(document.document_id)
      .then((blob) => {
        if (!active) {
          return;
        }

        objectUrl = URL.createObjectURL(blob);
        setDocumentUrl(objectUrl);
      })
      .catch((error) => {
        if (active) {
          setErrorMessage(error.message);
        }
      });

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [document?.document_id, reloadKey]);

  useEffect(() => {
    const previousOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  if (!document) {
    return null;
  }

  return (
    <div className="vault-modal-layer document-viewer-layer">
      <button
        aria-label="Close document viewer"
        className="vault-modal-backdrop"
        onClick={onClose}
        type="button"
      />

      <section
        aria-labelledby="document-viewer-title"
        aria-modal="true"
        className="document-viewer-dialog"
        role="dialog"
      >
        <header className="document-viewer-header">
          <div className="document-viewer-title-icon" aria-hidden="true">
            <MaterialIcon name="document" size={22} />
          </div>
          <div className="document-viewer-title-group">
            <span>Private study preview</span>
            <h2 id="document-viewer-title" title={filename}>{filename}</h2>
            <p>{document.page_count ?? "—"} pages · Stored in your Knowledge Vault</p>
          </div>
          <div className="document-viewer-actions">
            {documentUrl && (
              <>
                <a
                  className="vault-button vault-button-secondary"
                  href={documentUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  <MaterialIcon name="external" size={16} />
                  <span>Open in new tab</span>
                </a>
                <a
                  className="vault-button vault-button-secondary"
                  download={downloadFilename}
                  href={documentUrl}
                >
                  <MaterialIcon name="download" size={16} />
                  <span>Download</span>
                </a>
              </>
            )}
            <button
              aria-label="Close document viewer"
              className="document-viewer-close"
              onClick={onClose}
              ref={closeButtonRef}
              type="button"
            >
              <MaterialIcon name="close" size={20} />
            </button>
          </div>
        </header>

        <div className="document-viewer-body">
          {!documentUrl && !errorMessage && (
            <div className="document-viewer-loading" role="status">
              <span className="vault-processing-spinner" aria-hidden="true" />
              <strong>Preparing your document…</strong>
              <p>The file is being loaded securely from your private library.</p>
            </div>
          )}

          {errorMessage && (
            <div className="document-viewer-error" role="alert">
              <MaterialIcon name="document" size={30} />
              <strong>The document could not be displayed</strong>
              <p>{errorMessage}</p>
              <button
                className="vault-button vault-button-primary"
                onClick={() => setReloadKey((value) => value + 1)}
                type="button"
              >
                Try again
              </button>
            </div>
          )}

          {documentUrl && (
            <iframe
              className="document-viewer-frame"
              src={`${documentUrl}#view=FitH`}
              title={`Preview of ${filename}`}
            />
          )}
        </div>

        <footer className="document-viewer-footer">
          <MaterialIcon name="shield" size={15} />
          Only your signed-in account can request this file. Images are displayed as the PDF copy created during OCR processing.
        </footer>
      </section>
    </div>
  );
}

export default DocumentViewerModal;
