import { useEffect, useRef, useState } from "react";

import DocumentCard from "../components/DocumentCard.jsx";
import {
  deleteDocument,
  getDocuments,
  uploadDocument,
} from "../services/api.js";

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_PDF_TYPES = ["application/pdf", "application/x-pdf"];

function validatePdf(file) {
  if (!file) {
    return "Choose a PDF before uploading.";
  }

  const hasPdfExtension = file.name.toLowerCase().endsWith(".pdf");
  const hasAllowedType =
    file.type === "" || ALLOWED_PDF_TYPES.includes(file.type);

  if (!hasPdfExtension || !hasAllowedType) {
    return "Only PDF files are supported.";
  }

  if (file.size === 0) {
    return "The selected PDF is empty.";
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "The PDF must be 10 MB or smaller.";
  }

  return "";
}

function Materials() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const fileInputRef = useRef(null);

  async function loadDocuments(showLoading = true) {
    if (showLoading) {
      setIsLoading(true);
    }

    setErrorMessage("");

    try {
      const documentList = await getDocuments();
      setDocuments(Array.isArray(documentList) ? documentList : []);
      return true;
    } catch (error) {
      setErrorMessage(error.message);
      return false;
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  function handleFileChange(event) {
    const file = event.target.files?.[0] || null;
    const validationMessage = validatePdf(file);

    setSuccessMessage("");
    setErrorMessage(validationMessage);
    setSelectedFile(validationMessage ? null : file);

    if (validationMessage && fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  async function handleUpload(event) {
    event.preventDefault();

    const validationMessage = validatePdf(selectedFile);

    if (validationMessage) {
      setErrorMessage(validationMessage);
      return;
    }

    setIsUploading(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const result = await uploadDocument(selectedFile);

      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      const refreshed = await loadDocuments(false);

      if (refreshed) {
        setSuccessMessage(
          result.message || "Your PDF was uploaded successfully.",
        );
      }
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(document) {
    const filename = document.original_filename || "this document";
    const confirmed = window.confirm(
      "Delete “" + filename + "”? This removes the PDF and its search data.",
    );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(document.document_id);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await deleteDocument(document.document_id);
      const refreshed = await loadDocuments(false);

      if (refreshed) {
        setSuccessMessage(filename + " was deleted successfully.");
      }
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <div className="page-container">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Materials Library</p>
          <h1>My Learning Materials</h1>
          <p>
            Upload course PDFs so LearnMate can organize their content for
            semantic search and future learning activities.
          </p>
        </div>
        <span className="document-count">
          {documents.length} {documents.length === 1 ? "document" : "documents"}
        </span>
      </section>

      {errorMessage && (
        <div className="feedback feedback-error" role="alert">
          <strong>Something needs attention.</strong>
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="feedback feedback-success" role="status">
          <strong>Success.</strong>
          <span>{successMessage}</span>
        </div>
      )}

      <section className="panel upload-panel" aria-labelledby="upload-heading">
        <div className="panel-heading">
          <div>
            <h2 id="upload-heading">Upload a new PDF</h2>
            <p>Choose one text-based PDF up to 10 MB.</p>
          </div>
          <span className="step-badge">Step 1</span>
        </div>

        <form className="upload-form" onSubmit={handleUpload}>
          <label className="file-picker" htmlFor="material-file">
            <span className="file-picker-icon" aria-hidden="true">
              ↑
            </span>
            <span>
              <strong>
                {selectedFile ? selectedFile.name : "Choose a learning PDF"}
              </strong>
              <small>
                {selectedFile
                  ? "Ready to upload"
                  : "PDF format only · Maximum size 10 MB"}
              </small>
            </span>
            <span className="button button-secondary" aria-hidden="true">
              Browse
            </span>
          </label>
          <input
            ref={fileInputRef}
            className="visually-hidden"
            id="material-file"
            name="material-file"
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={isUploading}
          />

          <button
            className="button button-primary"
            type="submit"
            disabled={!selectedFile || isUploading}
          >
            {isUploading ? "Uploading and processing…" : "Upload PDF"}
          </button>
        </form>
      </section>

      <section className="panel library-panel" aria-labelledby="library-heading">
        <div className="panel-heading">
          <div>
            <h2 id="library-heading">Your uploaded materials</h2>
            <p>Recently uploaded documents appear first.</p>
          </div>
          <button
            className="button button-quiet"
            type="button"
            onClick={() => loadDocuments()}
            disabled={isLoading || isUploading}
          >
            Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="state-card" role="status">
            <span className="spinner" aria-hidden="true" />
            <h3>Loading your materials</h3>
            <p>Please wait while LearnMate checks your library.</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="state-card">
            <span className="empty-icon" aria-hidden="true">
              PDF
            </span>
            <h3>Your library is empty</h3>
            <p>Upload your first PDF to start building your learning library.</p>
          </div>
        ) : (
          <div className="document-list">
            {documents.map((document) => (
              <DocumentCard
                key={document.document_id}
                document={document}
                isDeleting={deletingDocumentId === document.document_id}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Materials;
