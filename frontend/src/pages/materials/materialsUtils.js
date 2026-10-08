export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

const ALLOWED_MATERIAL_TYPES = {
  ".jpeg": ["image/jpeg", "image/jpg"],
  ".jpg": ["image/jpeg", "image/jpg"],
  ".pdf": ["application/pdf", "application/x-pdf"],
  ".png": ["image/png"],
};

function getFileExtension(filename = "") {
  const normalizedFilename = filename.toLowerCase();
  return Object.keys(ALLOWED_MATERIAL_TYPES).find((extension) =>
    normalizedFilename.endsWith(extension),
  );
}

export function validateMaterial(file) {
  if (!file) {
    return "Choose a PDF or image before uploading.";
  }

  const extension = getFileExtension(file.name);
  const hasAllowedType =
    extension &&
    (file.type === "" || ALLOWED_MATERIAL_TYPES[extension].includes(file.type));

  if (!extension || !hasAllowedType) {
    return "Only PDF, PNG, JPG, and JPEG files are supported.";
  }

  if (file.size === 0) {
    return "The selected file is empty.";
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "The file must be 10 MB or smaller.";
  }

  return "";
}

export function getMaterialType(filename) {
  const extension = getFileExtension(filename);
  return extension === ".png" || extension === ".jpg" || extension === ".jpeg"
    ? "Image"
    : "PDF";
}

export function formatFileSize(fileSizeBytes) {
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

  return `${readableSize.toFixed(decimalPlaces)} ${units[unitIndex]}`;
}

export function formatUploadDate(createdAt) {
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

export function getLibraryStats(documents) {
  return documents.reduce(
    (stats, document) => ({
      documents: stats.documents + 1,
      pages: stats.pages + (Number(document.page_count) || 0),
      chunks: stats.chunks + (Number(document.chunk_count) || 0),
    }),
    { documents: 0, pages: 0, chunks: 0 },
  );
}
