import assert from "node:assert/strict";
import test from "node:test";

import {
  MAX_FILE_SIZE_BYTES,
  filterAndSortMaterials,
  formatFileSize,
  getMaterialType,
  getLibraryStats,
  validateMaterial,
} from "./materialsUtils.js";

function file(overrides = {}) {
  return {
    name: "lecture.pdf",
    type: "application/pdf",
    size: 1024,
    ...overrides,
  };
}

test("validates supported PDFs and images", () => {
  assert.equal(validateMaterial(file()), "");
  assert.equal(validateMaterial(file({ name: "diagram.png", type: "image/png" })), "");
  assert.equal(validateMaterial(file({ name: "notes.jpg", type: "image/jpeg" })), "");
  assert.equal(validateMaterial(file({ name: "notes.jpeg", type: "image/jpeg" })), "");
});

test("rejects unsupported, empty, and oversized uploads", () => {
  assert.equal(
    validateMaterial(file({ name: "notes.txt" })),
    "Only PDF, PNG, JPG, and JPEG files are supported.",
  );
  assert.equal(
    validateMaterial(file({ name: "fake.png", type: "application/pdf" })),
    "Only PDF, PNG, JPG, and JPEG files are supported.",
  );
  assert.equal(validateMaterial(file({ size: 0 })), "The selected file is empty.");
  assert.equal(
    validateMaterial(file({ size: MAX_FILE_SIZE_BYTES + 1 })),
    "The file must be 10 MB or smaller.",
  );
});

test("identifies the material type from its filename", () => {
  assert.equal(getMaterialType("lecture.pdf"), "PDF");
  assert.equal(getMaterialType("diagram.PNG"), "Image");
  assert.equal(getMaterialType("photo.jpeg"), "Image");
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

test("filters materials by name and type and sorts the visible library", () => {
  const documents = [
    {
      document_id: "doc-1",
      original_filename: "Algorithms Lecture.pdf",
      created_at: "2026-10-08T09:00:00Z",
    },
    {
      document_id: "doc-2",
      original_filename: "Network Diagram.png",
      created_at: "2026-10-09T09:00:00Z",
    },
    {
      document_id: "doc-3",
      original_filename: "Database Notes.pdf",
      created_at: "2026-10-07T09:00:00Z",
    },
  ];

  assert.deepEqual(
    filterAndSortMaterials(documents, "notes", "pdf", "newest").map(
      (document) => document.document_id,
    ),
    ["doc-3"],
  );
  assert.deepEqual(
    filterAndSortMaterials(documents, "", "all", "name").map(
      (document) => document.document_id,
    ),
    ["doc-1", "doc-3", "doc-2"],
  );
  assert.deepEqual(
    filterAndSortMaterials(documents, "", "all", "oldest").map(
      (document) => document.document_id,
    ),
    ["doc-3", "doc-1", "doc-2"],
  );
});
