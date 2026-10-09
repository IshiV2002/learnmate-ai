import MaterialIcon from "./MaterialIcon.jsx";
import { formatFileSize, formatUploadDate, getMaterialType } from "./materialsUtils.js";

function MetadataItem({ icon, label, value }) {
  return (
    <div className="source-metadata-item">
      <MaterialIcon name={icon} size={16} />
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function KnowledgeSourceCard({ document, isDeleting, onDelete, onQuiz, onTutor }) {
  const filename = document.original_filename || "Untitled material";
  const materialType = getMaterialType(filename);

  return (
    <article className="knowledge-source-card">
      <div className="source-card-accent" aria-hidden="true" />
      <div className="source-card-heading">
        <span className="source-document-icon" aria-hidden="true">
          <MaterialIcon name="document" size={24} />
          <small>{materialType}</small>
        </span>
        <div className="source-title-group">
          <span className="source-indexed-label">
            <span className="source-ready-dot" aria-hidden="true" />
            Ready to study
          </span>
          <h3 title={filename}>{filename}</h3>
          <p>Added {formatUploadDate(document.created_at)}</p>
        </div>
        <button
          aria-label={`Delete ${filename}`}
          className="source-delete-button"
          disabled={isDeleting}
          onClick={() => onDelete(document)}
          type="button"
        >
          <MaterialIcon name="trash" size={18} />
          <span>{isDeleting ? "Deleting…" : "Delete"}</span>
        </button>
      </div>

      <dl className="source-metadata-grid">
        <MetadataItem icon="pages" label="Pages" value={document.page_count ?? "—"} />
        <MetadataItem icon="chunks" label="Searchable sections" value={document.chunk_count ?? "—"} />
        <MetadataItem icon="storage" label="File size" value={formatFileSize(document.file_size_bytes)} />
      </dl>

      <div
        aria-label={`Study actions for ${filename}`}
        className="source-card-actions"
        role="group"
      >
        <button
          className="source-action-button source-action-primary"
          onClick={() => onTutor(document)}
          type="button"
        >
          <MaterialIcon name="tutor" size={17} />
          Study with Tutor
        </button>
        <button
          className="source-action-button"
          onClick={() => onQuiz(document)}
          type="button"
        >
          <MaterialIcon name="quiz" size={17} />
          Make a Quiz
        </button>
      </div>
    </article>
  );
}

export default KnowledgeSourceCard;
