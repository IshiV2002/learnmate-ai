import MaterialIcon from "./MaterialIcon.jsx";
import { formatFileSize } from "./materialsUtils.js";

function UploadDropzone({
  disabled,
  fileInputRef,
  isDragging,
  onDragLeave,
  onDragOver,
  onDrop,
  onFileChange,
  onOpenPicker,
  selectedFile,
}) {
  return (
    <div
      aria-describedby="upload-requirements"
      aria-disabled={disabled}
      className={`vault-dropzone ${isDragging ? "vault-dropzone-dragging" : ""} ${selectedFile ? "vault-dropzone-selected" : ""}`}
      onDragLeave={onDragLeave}
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      <input
        accept=".pdf,application/pdf"
        className="visually-hidden"
        disabled={disabled}
        id="material-file"
        name="material-file"
        onChange={onFileChange}
        ref={fileInputRef}
        type="file"
      />

      <span className="vault-upload-orbit" aria-hidden="true">
        <span className="vault-upload-icon"><MaterialIcon name={selectedFile ? "check" : "upload"} size={26} /></span>
        <span className="vault-orbit-dot vault-orbit-dot-one" />
        <span className="vault-orbit-dot vault-orbit-dot-two" />
      </span>

      <div className="vault-dropzone-copy">
        <p className="vault-dropzone-label">
          {selectedFile ? "Knowledge source selected" : "Drop your course PDF into the vault"}
        </p>
        <p className="vault-dropzone-detail">
          {selectedFile
            ? `${selectedFile.name} · ${formatFileSize(selectedFile.size)}`
            : "Drag and drop a text-based PDF here, or choose one from your device."}
        </p>
      </div>

      <button
        className="vault-button vault-button-secondary"
        disabled={disabled}
        onClick={onOpenPicker}
        type="button"
      >
        {selectedFile ? "Choose another" : "Browse PDF"}
      </button>

      <p className="vault-upload-requirements" id="upload-requirements">
        PDF only <span aria-hidden="true">•</span> Maximum 10 MB <span aria-hidden="true">•</span> Text-based files work best
      </p>
    </div>
  );
}

export default UploadDropzone;
