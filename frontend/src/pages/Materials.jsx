import { useEffect, useMemo, useRef, useState } from "react";

import {
  deleteDocument,
  getDocuments,
  uploadDocument,
} from "../services/api.js";
import "./Materials.css";
import DeleteDocumentModal from "./materials/DeleteDocumentModal.jsx";
import KnowledgeSourceCard from "./materials/KnowledgeSourceCard.jsx";
import LibrarySkeleton from "./materials/LibrarySkeleton.jsx";
import MaterialIcon from "./materials/MaterialIcon.jsx";
import ProcessingJourney from "./materials/ProcessingJourney.jsx";
import UploadDropzone from "./materials/UploadDropzone.jsx";
import { getLibraryStats, validatePdf } from "./materials/materialsUtils.js";

function Materials() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);
  const [documentPendingDelete, setDocumentPendingDelete] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("idle");
  const [uploadFileName, setUploadFileName] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const fileInputRef = useRef(null);
  const libraryStats = useMemo(() => getLibraryStats(documents), [documents]);

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

  function selectFile(file) {
    const validationMessage = validatePdf(file);

    setSuccessMessage("");
    setErrorMessage(validationMessage);
    setUploadStatus("idle");
    setUploadFileName("");
    setSelectedFile(validationMessage ? null : file);

    if (validationMessage && fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleFileChange(event) {
    selectFile(event.target.files?.[0] || null);
  }

  function handleDragOver(event) {
    event.preventDefault();

    if (!isUploading) {
      event.dataTransfer.dropEffect = "copy";
      setIsDragging(true);
    }
  }

  function handleDragLeave(event) {
    if (!event.currentTarget.contains(event.relatedTarget)) {
      setIsDragging(false);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);

    if (!isUploading) {
      selectFile(event.dataTransfer.files?.[0] || null);
    }
  }

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function clearSelectedFile() {
    setSelectedFile(null);
    setUploadStatus("idle");
    setUploadFileName("");

    if (fileInputRef.current) {
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

    const currentFileName = selectedFile.name;
    setIsUploading(true);
    setUploadStatus("processing");
    setUploadFileName(currentFileName);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const result = await uploadDocument(selectedFile);
      clearSelectedFile();
      setUploadFileName(currentFileName);

      const refreshed = await loadDocuments(false);

      if (refreshed) {
        setUploadStatus("complete");
        setSuccessMessage(
          result.message || "Your PDF was uploaded and indexed successfully.",
        );
      }
    } catch (error) {
      setUploadStatus("error");
      setErrorMessage(error.message);
    } finally {
      setIsUploading(false);
    }
  }

  async function confirmDelete() {
    if (!documentPendingDelete) {
      return;
    }

    const filename = documentPendingDelete.original_filename || "This document";
    const documentId = documentPendingDelete.document_id;

    setDeletingDocumentId(documentId);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await deleteDocument(documentId);
      const refreshed = await loadDocuments(false);

      if (refreshed) {
        setSuccessMessage(`${filename} was removed from the Knowledge Vault.`);
      }
      setDocumentPendingDelete(null);
    } catch (error) {
      setErrorMessage(error.message);
      setDocumentPendingDelete(null);
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <div className="materials-page">
      <header className="vault-hero">
        <div className="vault-hero-copy">
          <p className="vault-eyebrow">Materials · Knowledge Vault</p>
          <h1>Turn course material into searchable knowledge.</h1>
          <p className="vault-hero-description">
            Add trusted course PDFs to create a private library of page-aware sections that LearnMate agents can retrieve when supporting your study.
          </p>
          <div className="vault-hero-trust">
            <span><MaterialIcon name="shield" size={16} /> Server-validated PDFs</span>
            <span><MaterialIcon name="search" size={16} /> Page references preserved</span>
          </div>
        </div>

        <div className="vault-knowledge-map" aria-label="Knowledge Vault statistics">
          <div className="vault-map-visual" aria-hidden="true">
            <span className="vault-map-ring vault-map-ring-one" />
            <span className="vault-map-ring vault-map-ring-two" />
            <span className="vault-map-line vault-map-line-one" />
            <span className="vault-map-line vault-map-line-two" />
            <span className="vault-map-node vault-map-node-one" />
            <span className="vault-map-node vault-map-node-two" />
            <span className="vault-map-node vault-map-node-three" />
            <span className="vault-map-core"><MaterialIcon name="search" size={22} /></span>
          </div>
          <div className="vault-stat-grid">
            <div>
              <span>{isLoading ? "—" : libraryStats.documents}</span>
              <small>Sources</small>
            </div>
            <div>
              <span>{isLoading ? "—" : libraryStats.pages}</span>
              <small>Pages</small>
            </div>
            <div>
              <span>{isLoading ? "—" : libraryStats.chunks}</span>
              <small>Searchable sections</small>
            </div>
          </div>
        </div>
      </header>

      <div className="vault-feedback-stack" aria-live="polite">
        {errorMessage && (
          <div className="vault-feedback vault-feedback-error" role="alert">
            <span className="vault-feedback-icon" aria-hidden="true"><MaterialIcon name="close" size={17} /></span>
            <div><strong>Something needs attention</strong><p>{errorMessage}</p></div>
            <button aria-label="Dismiss error" onClick={() => setErrorMessage("")} type="button"><MaterialIcon name="close" size={16} /></button>
          </div>
        )}

        {successMessage && (
          <div className="vault-feedback vault-feedback-success" role="status">
            <span className="vault-feedback-icon" aria-hidden="true"><MaterialIcon name="check" size={17} /></span>
            <div><strong>Knowledge Vault updated</strong><p>{successMessage}</p></div>
            <button aria-label="Dismiss success message" onClick={() => setSuccessMessage("")} type="button"><MaterialIcon name="close" size={16} /></button>
          </div>
        )}
      </div>

      <section className="vault-panel vault-upload-panel" aria-labelledby="vault-upload-heading">
        <div className="vault-section-heading">
          <div>
            <span className="vault-section-number">01</span>
            <div>
              <p className="vault-section-kicker">Add knowledge</p>
              <h2 id="vault-upload-heading">Upload a course PDF</h2>
            </div>
          </div>
          <span className="vault-security-label"><MaterialIcon name="shield" size={15} /> Backend validation remains authoritative</span>
        </div>

        <form className="vault-upload-form" onSubmit={handleUpload}>
          <UploadDropzone
            disabled={isUploading}
            fileInputRef={fileInputRef}
            isDragging={isDragging}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onFileChange={handleFileChange}
            onOpenPicker={openFilePicker}
            selectedFile={selectedFile}
          />

          <div className="vault-upload-actions">
            <p>
              Frontend checks improve feedback; the server still performs all security and PDF validation.
            </p>
            <div>
              {selectedFile && (
                <button className="vault-button vault-button-quiet" disabled={isUploading} onClick={clearSelectedFile} type="button">
                  Clear
                </button>
              )}
              <button className="vault-button vault-button-primary" disabled={!selectedFile || isUploading} type="submit">
                <MaterialIcon name="upload" size={18} />
                {isUploading ? "Uploading and processing…" : "Add to Knowledge Vault"}
              </button>
            </div>
          </div>
        </form>

        <ProcessingJourney fileName={uploadFileName} status={uploadStatus} />
      </section>

      <section className="vault-transparency" aria-labelledby="vault-transparency-heading">
        <div className="vault-transparency-icon" aria-hidden="true"><MaterialIcon name="search" size={23} /></div>
        <div>
          <p className="vault-section-kicker">How retrieval works</p>
          <h2 id="vault-transparency-heading">Grounded in your material, with page context.</h2>
          <p>
            LearnMate extracts text into searchable sections and keeps page references so Tutor and Quiz agents can retrieve relevant source material. Retrieval improves grounding, but it does not guarantee every AI response is correct—always check important answers against the original PDF.
          </p>
        </div>
        <div className="vault-pipeline" aria-label="Knowledge indexing pipeline">
          <span>PDF</span><i aria-hidden="true" /><span>Page-aware sections</span><i aria-hidden="true" /><span>Agent retrieval</span>
        </div>
      </section>

      <section className="vault-library-section" aria-labelledby="vault-library-heading">
        <div className="vault-library-heading">
          <div>
            <p className="vault-section-kicker">Indexed sources</p>
            <h2 id="vault-library-heading">Your knowledge library</h2>
            <p>Every card represents a real PDF currently available to retrieval.</p>
          </div>
          <button
            className="vault-button vault-button-secondary"
            disabled={isLoading || isUploading}
            onClick={() => loadDocuments()}
            type="button"
          >
            <MaterialIcon className={isLoading ? "vault-icon-spinning" : ""} name="refresh" size={17} />
            Refresh library
          </button>
        </div>

        {isLoading ? (
          <LibrarySkeleton />
        ) : documents.length === 0 ? (
          <div className="vault-empty-state">
            <div className="vault-empty-visual" aria-hidden="true">
              <span className="vault-empty-document"><MaterialIcon name="document" size={30} /></span>
              <span className="vault-empty-node vault-empty-node-one" />
              <span className="vault-empty-node vault-empty-node-two" />
              <span className="vault-empty-connection" />
            </div>
            <p className="vault-section-kicker">The vault is ready</p>
            <h3>Add your first knowledge source</h3>
            <p>Upload a text-based course PDF to make its page-aware sections available for semantic retrieval.</p>
            <button className="vault-button vault-button-primary" onClick={openFilePicker} type="button">
              <MaterialIcon name="upload" size={18} /> Choose your first PDF
            </button>
          </div>
        ) : (
          <div className="knowledge-source-grid">
            {documents.map((document) => (
              <KnowledgeSourceCard
                document={document}
                isDeleting={deletingDocumentId === document.document_id}
                key={document.document_id}
                onDelete={setDocumentPendingDelete}
              />
            ))}
          </div>
        )}
      </section>

      <DeleteDocumentModal
        document={documentPendingDelete}
        isDeleting={deletingDocumentId === documentPendingDelete?.document_id}
        onCancel={() => setDocumentPendingDelete(null)}
        onConfirm={confirmDelete}
      />
    </div>
  );
}

export default Materials;
