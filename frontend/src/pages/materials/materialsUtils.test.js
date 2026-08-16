import assert from "node:assert/strict";
import test from "node:test";

import {
  MAX_FILE_SIZE_BYTES,
  formatFileSize,
  getLibraryStats,
  validatePdf,
} from "./materialsUtils.js";

function file(overrides = {}) {
  return {
    name: "lecture.pdf",
    type: "application/pdf",
    size: 1024,
    ...overrides,
  };
}

test("validates a supported PDF", () => {
  assert.equal(validatePdf(file()), "");
});

test("rejects unsupported, empty, and oversized uploads", () => {
  assert.equal(validatePdf(file({ name: "notes.txt" })), "Only PDF files are supported.");
  assert.equal(validatePdf(file({ size: 0 })), "The selected PDF is empty.");
  assert.equal(
    validatePdf(file({ size: MAX_FILE_SIZE_BYTES + 1 })),
    "The PDF must be 10 MB or smaller.",
  );
});

test("formats file sizes and totals only real document metadata", () => {
  assert.equal(formatFileSize(1536), "1.5 KB");
  assert.deepEqual(
    getLibraryStats([
      { page_count: 10, chunk_count: 24 },
      { page_count: 4, chunk_count: 9 },
    ]),
    { documents: 2, pages: 14, chunks: 33 },
  );
});
