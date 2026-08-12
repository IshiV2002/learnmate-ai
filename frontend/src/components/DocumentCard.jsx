function formatFileSize(fileSizeBytes) {
  const size = Number(fileSizeBytes);

  if (!Number.isFinite(size) || size < 0) {
    return "Size unavailable";
  }

  if (size === 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  const unitIndex = Math.min(
    Math.floor(Math.log(size) / Math.log(1024)),
    units.length - 1,
  );
  const readableSize = size / 1024 ** unitIndex;
  const decimalPlaces = unitIndex === 0 ? 0 : 1;

  return readableSize.toFixed(decimalPlaces) + " " + units[unitIndex];
}

function formatUploadDate(createdAt) {
  if (!createdAt) {
    return "Date unavailable";
  }

  const uploadDate = new Date(createdAt);

  if (Number.isNaN(uploadDate.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(uploadDate);
}

function DocumentCard({ document, isDeleting, onDelete }) {
  return (
    <article className="document-card">
      <div className="pdf-badge" aria-hidden="true">
        PDF
      </div>

      <div className="document-details">
        <h3 title={document.original_filename}>
          {document.original_filename || "Untitled PDF"}
        </h3>
        <p className="upload-date">
          Uploaded {formatUploadDate(document.created_at)}
        </p>

        <dl className="document-metadata">
          <div>
            <dt>Pages</dt>
            <dd>{document.page_count ?? "—"}</dd>
          </div>
          <div>
            <dt>Search chunks</dt>
            <dd>{document.chunk_count ?? "—"}</dd>
          </div>
          <div>
            <dt>File size</dt>
            <dd>{formatFileSize(document.file_size_bytes)}</dd>
          </div>
        </dl>
      </div>

      <button
        className="button button-danger"
        type="button"
        onClick={() => onDelete(document)}
        disabled={isDeleting}
        aria-label={"Delete " + (document.original_filename || "document")}
      >
        {isDeleting ? "Deleting…" : "Delete"}
      </button>
    </article>
  );
}

export default DocumentCard;
