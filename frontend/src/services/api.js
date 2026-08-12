const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(message, status = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getErrorMessage(responseBody) {
  if (typeof responseBody?.detail === "string") {
    return responseBody.detail;
  }

  if (Array.isArray(responseBody?.detail)) {
    return responseBody.detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join(" ");
  }

  return "The request could not be completed. Please try again.";
}

async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetch(API_BASE_URL + path, options);
  } catch {
    throw new ApiError(
      "Could not connect to LearnMate. Make sure the backend is running.",
    );
  }

  const responseBody = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(getErrorMessage(responseBody), response.status);
  }

  return responseBody;
}

export function getDocuments() {
  return apiRequest("/documents");
}

export function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest("/documents/upload", {
    method: "POST",
    body: formData,
  });
}

export function deleteDocument(documentId) {
  return apiRequest("/documents/" + encodeURIComponent(documentId), {
    method: "DELETE",
  });
}
