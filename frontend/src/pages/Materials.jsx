import { useEffect, useMemo, useRef, useState } from "react";

import {
  deleteDocument,
  getDocuments,
  uploadDocument,
} from "../services/api.js";
import "./Materials.css";
import DeleteDocumentModal from "./materials/DeleteDocumentModal.jsx";
import KnowledgeSourceCard from "./materials/KnowledgeSourceCard.jsx";
import LibraryGraphic from "./materials/LibraryGraphic.jsx";
import LibrarySkeleton from "./materials/LibrarySkeleton.jsx";
import MaterialIcon from "./materials/MaterialIcon.jsx";
import ProcessingJourney from "./materials/ProcessingJourney.jsx";
import UploadDropzone from "./materials/UploadDropzone.jsx";
import {
  filterAndSortMaterials,
  getLibraryStats,
  validateMaterial,
} from "./materials/materialsUtils.js";

function Materials({ onStudyDocument, onStudyWithTutor = null }) {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);
  const [documentPendingDelete, setDocumentPendingDelete] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("idle");
  const [uploadFileName, setUploadFileName] = useState("");
  const [lastUploadedDoc, setLastUploadedDoc] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [recentlyUploadedDocument, setRecentlyUploadedDocument] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("newest");
  const fileInputRef = useRef(null);
  const libraryStats = useMemo(() => getLibraryStats(documents), [documents]);
  const visibleDocuments = useMemo(
    () => filterAndSortMaterials(documents, searchQuery, typeFilter, sortOrder),
    [documents, searchQuery, sortOrder, typeFilter],
  );

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
    const validationMessage = validateMaterial(file);

    setSuccessMessage("");
    setRecentlyUploadedDocument(null);
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

    const validationMessage = validateMaterial(selectedFile);

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
      setLastUploadedDoc({
        document_id: result.document_id,
        original_filename: currentFileName,
      });

      if (result.document) {
        setDocuments((currentDocuments) => [
          result.document,
          ...currentDocuments.filter(
            (document) => document.document_id !== result.document.document_id,
          ),
        ]);
      }

      await loadDocuments(false);
      setUploadStatus("complete");
      setRecentlyUploadedDocument(result.document || null);
      setSuccessMessage(
        result.message || "Your material was uploaded and indexed successfully.",
      );
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
        setSuccessMessage(`${filename} was removed from your course library.`);
        if (recentlyUploadedDocument?.document_id === documentId) {
          setRecentlyUploadedDocument(null);
          setUploadStatus("idle");
        }
      }
      setDocumentPendingDelete(null);
    } catch (error) {
      setErrorMessage(error.message);
      setDocumentPendingDelete(null);
    } finally {
      setDeletingDocumentId(null);
    }
  }

  function continueWithDocument(document, destination) {
    if (document && onStudyDocument) {
      onStudyDocument(document, destination);
    }
  }

  return (
    <div className="materials-page">
      <header className="vault-hero">
        <div className="vault-hero-copy">
          <p className="vault-eyebrow">Course materials</p>
          <h1>Keep your study sources organised.</h1>
          <p className="vault-hero-description">
            Build a clear library of lecture notes, readings and diagrams. Choose any source when you want an explanation or a practice quiz.
          </p>
          <div className="vault-hero-trust">
            <span><MaterialIcon name="shield" size={16} /> Private to your account</span>
            <span><MaterialIcon name="pages" size={16} /> Page references included</span>
          </div>
        </div>

        <div className="vault-library-overview" aria-label="Course library statistics">
          <LibraryGraphic />
          <div className="vault-stat-grid">
            <div>
              <span>{isLoading ? "—" : libraryStats.documents}</span>
              <small>Materials</small>
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
            <div><strong>Course library updated</strong><p>{successMessage}</p></div>
            <button aria-label="Dismiss success message" onClick={() => setSuccessMessage("")} type="button"><MaterialIcon name="close" size={16} /></button>
          </div>
        )}
      </div>

      <section className="vault-panel vault-upload-panel" aria-labelledby="vault-upload-heading">
        <div className="vault-section-heading">
          <div>
            <span className="vault-section-icon"><MaterialIcon name="upload" size={20} /></span>
            <div>
              <p className="vault-section-kicker">Add a material</p>
              <h2 id="vault-upload-heading">Upload lecture notes or a diagram</h2>
            </div>
          </div>
          <span className="vault-security-label"><MaterialIcon name="shield" size={15} /> Files are checked before they are added</span>
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
              Supported formats: PDF, PNG, JPG and JPEG. Maximum file size: 10 MB.
            </p>
            <div>
              {selectedFile && (
                <button className="vault-button vault-button-quiet" disabled={isUploading} onClick={clearSelectedFile} type="button">
                  Clear
                </button>
              )}
              <button className="vault-button vault-button-primary" disabled={!selectedFile || isUploading} type="submit">
                <MaterialIcon name="upload" size={18} />
                {isUploading ? "Uploading and preparing…" : "Upload material"}
              </button>
            </div>
          </div>
        </form>

        <ProcessingJourney
          fileName={uploadFileName}
          onStudy={lastUploadedDoc && onStudyDocument ? () => continueWithDocument(lastUploadedDoc, "tutor") : null}
          status={uploadStatus}
        />

        {uploadStatus === "complete" && recentlyUploadedDocument && (
          <section className="vault-next-step" aria-labelledby="vault-next-step-heading">
            <span className="vault-next-step-icon" aria-hidden="true">
              <MaterialIcon name="check" size={24} />
            </span>
            <div className="vault-next-step-copy">
              <p className="vault-section-kicker">Your material is ready</p>
              <h3 id="vault-next-step-heading">What would you like to do next?</h3>
              <p>
                <strong>{recentlyUploadedDocument.original_filename}</strong> is selected. Use the Tutor to understand it, or make a quiz to check your memory and unlock recommendations.
              </p>
            </div>
            <div className="vault-next-step-actions">
              <button
                className="vault-button vault-button-primary"
                onClick={() => continueWithDocument(recentlyUploadedDocument, "tutor")}
                type="button"
              >
                <MaterialIcon name="tutor" size={18} />
                Study with Tutor
              </button>
              <button
                className="vault-button vault-button-secondary"
                onClick={() => continueWithDocument(recentlyUploadedDocument, "quiz")}
                type="button"
              >
                <MaterialIcon name="quiz" size={18} />
                Make a Quiz
              </button>
            </div>
          </section>
        )}
      </section>

      <section className="vault-transparency" aria-labelledby="vault-transparency-heading">
        <div className="vault-transparency-icon" aria-hidden="true"><MaterialIcon name="pages" size={23} /></div>
        <div>
          <p className="vault-section-kicker">Source-based study</p>
          <h2 id="vault-transparency-heading">Your original material stays at the centre.</h2>
          <p>
            Tutor explanations and generated quizzes use sections from your selected source. Page references help you return to the original notes and verify important answers.
          </p>
        </div>
        <div className="vault-study-uses" aria-label="Ways to use an uploaded material">
          <span><MaterialIcon name="tutor" size={16} /> Tutor explanations</span>
          <span><MaterialIcon name="quiz" size={16} /> Practice quizzes</span>
          <span><MaterialIcon name="pages" size={16} /> Page references</span>
        </div>
      </section>

      <section className="vault-library-section" aria-labelledby="vault-library-heading">
        <div className="vault-library-heading">
          <div>
            <p className="vault-section-kicker">Your library</p>
            <h2 id="vault-library-heading">Course materials</h2>
            <p>Find a source, then choose how you want to study it.</p>
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

        {documents.length > 0 && (
          <div className="vault-library-toolbar">
            <label className="vault-library-search">
              <span className="visually-hidden">Search course materials</span>
              <MaterialIcon name="search" size={17} />
              <input
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search by file name"
                type="search"
                value={searchQuery}
              />
            </label>

            <div className="vault-type-filters" aria-label="Filter materials by file type">
              {["all", "pdf", "image"].map((filter) => (
                <button
                  aria-pressed={typeFilter === filter}
                  className={typeFilter === filter ? "vault-filter-active" : ""}
                  key={filter}
                  onClick={() => setTypeFilter(filter)}
                  type="button"
                >
                  {filter === "all" ? "All" : filter === "pdf" ? "PDFs" : "Images"}
                </button>
              ))}
            </div>

            <label className="vault-library-sort">
              <span>Sort</span>
              <select onChange={(event) => setSortOrder(event.target.value)} value={sortOrder}>
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="name">File name</option>
              </select>
            </label>
          </div>
        )}

        {!isLoading && documents.length > 0 && (
          <p className="vault-library-result-count" aria-live="polite">
            Showing {visibleDocuments.length} of {documents.length} materials
          </p>
        )}

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
            <p className="vault-section-kicker">Start your course library</p>
            <h3>Add your first study material</h3>
            <p>Upload lecture notes, a reading or a clear image that you want to study.</p>
            <button className="vault-button vault-button-primary" onClick={openFilePicker} type="button">
              <MaterialIcon name="upload" size={18} /> Choose a file
            </button>
          </div>
        ) : visibleDocuments.length === 0 ? (
          <div className="vault-filter-empty">
            <MaterialIcon name="search" size={24} />
            <h3>No matching materials</h3>
            <p>Try a different file name or show all file types.</p>
            <button
              className="vault-button vault-button-secondary"
              onClick={() => {
                setSearchQuery("");
                setTypeFilter("all");
              }}
              type="button"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="knowledge-source-grid">
            {visibleDocuments.map((document) => (
              <KnowledgeSourceCard
                document={document}
                isDeleting={deletingDocumentId === document.document_id}
                key={document.document_id}
                onDelete={setDocumentPendingDelete}
                onQuiz={(selectedDocument) => continueWithDocument(selectedDocument, "quiz")}
                onTutor={(selectedDocument) => continueWithDocument(selectedDocument, "tutor")}
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
