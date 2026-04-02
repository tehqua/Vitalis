/**
 * api.js
 *
 * Centralised API service layer.
 * All network calls go through this module so the rest of the app
 * stays decoupled from HTTP details.
 *
 * Base URL is /api — Vite's dev proxy forwards this to http://localhost:8000/api.
 * In production, configure your reverse proxy accordingly.
 */

const BASE = "/api";

// ---------- helpers ----------

/**
 * Returns the stored JWT token, or null if the user is not logged in.
 */
function getToken() {
  return sessionStorage.getItem("access_token");
}

/**
 * Builds the standard Authorization header object.
 */
function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Thin wrapper around fetch that throws a structured error when the
 * HTTP response is not 2xx.
 */
async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse errors
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  // 204 No Content — return null
  if (res.status === 204) return null;
  return res.json();
}

// ---------- auth ----------

/**
 * Logs in with a Patient ID.
 * Stores the returned token and session_id in sessionStorage.
 *
 * @param {string} patientId
 * @returns {Promise<{access_token, session_id, patient_id, expires_in}>}
 */
export async function login(patientId) {
  const data = await request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id: patientId }),
  });

  sessionStorage.setItem("access_token", data.access_token);
  sessionStorage.setItem("session_id", data.session_id);
  sessionStorage.setItem("patient_id", data.patient_id);

  return data;
}

/**
 * Logs out by invalidating the current session on the server
 * then clearing local storage.
 */
export async function logout() {
  const sessionId = sessionStorage.getItem("session_id");
  if (sessionId) {
    try {
      await request(`/auth/logout?session_id=${sessionId}`, { method: "POST" });
    } catch {
      // best-effort — still clear local state
    }
  }
  sessionStorage.clear();
}

// ---------- chat ----------

/**
 * Sends a plain-text message.
 *
 * @param {string} message
 * @returns {Promise<{response, session_id, timestamp, metadata}>}
 */
export async function sendMessage(message) {
  return request("/chat/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
}

/**
 * Sends a message together with an image file attachment.
 *
 * @param {string|null} message
 * @param {File} imageFile
 * @returns {Promise<{response, session_id, timestamp, metadata}>}
 */
export async function sendMessageWithImage(message, imageFile) {
  const form = new FormData();
  if (message) form.append("message", message);
  form.append("image", imageFile);

  return request("/chat/message-with-image", {
    method: "POST",
    body: form,
    // Do NOT set Content-Type — let the browser set the multipart boundary.
  });
}

/**
 * Sends an audio recording for transcription and response.
 *
 * @param {File} audioFile
 * @returns {Promise<{response, session_id, timestamp, metadata}>}
 */
export async function sendAudioMessage(audioFile) {
  const form = new FormData();
  form.append("audio", audioFile);

  return request("/chat/message-with-audio", {
    method: "POST",
    body: form,
  });
}

/**
 * Fetches the full conversation history for the current session.
 *
 * @param {number} limit - max messages to return (default 50)
 * @returns {Promise<{session_id, patient_id, messages, total_messages}>}
 */
export async function getHistory(limit = 50) {
  return request(`/chat/history?limit=${limit}`);
}

/**
 * Fetches all chat sessions for the current patient (newest first).
 * Each item: { session_id, first_message, started_at, last_activity, message_count }
 *
 * @param {number} limit
 * @returns {Promise<{patient_id, sessions, total}>}
 */
export async function getSessions(limit = 20) {
  return request(`/chat/sessions?limit=${limit}`);
}

/**
 * Fetches the full message list for a specific past session.
 *
 * @param {string} sessionId
 * @param {number} limit
 * @returns {Promise<{session_id, patient_id, messages, total_messages}>}
 */
export async function getSessionHistory(sessionId, limit = 100) {
  return request(`/chat/history/${sessionId}?limit=${limit}`);
}

/**
 * Clears the in-memory conversation context on the server (current session).
 */
export async function clearHistory() {
  return request("/chat/history", { method: "DELETE" });
}

/**
 * Deletes all messages for a specific past session from the database.
 *
 * @param {string} sessionId
 * @returns {Promise<{message, session_id, deleted_count}>}
 */
export async function deleteSessionHistory(sessionId) {
  return request(`/chat/history/${sessionId}`, { method: "DELETE" });
}

/**
 * Fetches the full structured patient medical record report.
 * Parsed directly from the patient's FHIR bundle — no LLM involved.
 *
 * @returns {Promise<{patient_id, patient_name, report_text, sections, generated_at}>}
 */
export async function getPatientRecord() {
  return request("/chat/patient-record");
}

// ---------- health ----------

/**
 * Pings the backend health endpoint.
 * Useful to detect if the server is reachable before login.
 */
export async function healthCheck() {
  return request("/health");
}

// ---------- utils ----------

/**
 * Checks whether the user currently has a stored token.
 * Does NOT validate the token server-side.
 */
export function isAuthenticated() {
  return Boolean(getToken());
}

/**
 * Returns the stored patient_id shorthand for display.
 */
export function getStoredPatientId() {
  return sessionStorage.getItem("patient_id") || "";
}

/**
 * Derives a display-friendly short ID from the full patient_id.
 * Example: "Adam631_Cronin387_aff8f143..." -> "PID-Adam631"
 */
export function shortPatientId(fullId) {
  if (!fullId) return "";
  const first = fullId.split("_")[0];
  return `PID-${first}`;
}

/**
 * Derives initials from the patient_id for the avatar.
 * Example: "Adam631_Cronin387_..." -> "AC"
 */
export function patientInitials(fullId) {
  if (!fullId) return "?";
  const parts = fullId.split("_");
  const a = parts[0]?.[0] ?? "";
  const b = parts[1]?.[0] ?? "";
  return (a + b).toUpperCase();
}
