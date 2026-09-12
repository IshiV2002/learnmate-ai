export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

const ALLOWED_PDF_TYPES = ["application/pdf", "application/x-pdf"];

export function validatePdf(file) {
  if (!file) {
    return "Choose a PDF before uploading.";
  }

  const hasPdfExtension = file.name.toLowerCase().endsWith(".pdf");
  const hasAllowedType = file.type === "" || ALLOWED_PDF_TYPES.includes(file.type);

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
