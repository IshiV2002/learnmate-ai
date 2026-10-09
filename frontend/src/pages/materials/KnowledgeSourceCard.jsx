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

function KnowledgeSourceCard({ document, isDeleting, onDelete, onStudy }) {
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
            Indexed knowledge source
          </span>
          <h3 title={filename}>{filename}</h3>
          <p>Added {formatUploadDate(document.created_at)}</p>
        </div>
        <div className="source-card-actions">
          {onStudy && (
            <button
              aria-label={`Study ${filename} with Tutor`}
              className="source-study-button"
              onClick={() => onStudy(document)}
              type="button"
            >
              <MaterialIcon name="brain" size={16} />
              <span>Study</span>
            </button>
          )}
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
      </div>

      <dl className="source-metadata-grid">
        <MetadataItem icon="pages" label="Pages" value={document.page_count ?? "—"} />
        <MetadataItem icon="chunks" label="Searchable sections" value={document.chunk_count ?? "—"} />
        <MetadataItem icon="storage" label="File size" value={formatFileSize(document.file_size_bytes)} />
      </dl>

      <div className="source-grounding-note">
        <MaterialIcon name="search" size={16} />
        Available for grounded retrieval with preserved page references
      </div>
    </article>
  );
}

export default KnowledgeSourceCard;
