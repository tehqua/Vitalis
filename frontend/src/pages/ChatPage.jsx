/**
 * ChatPage.jsx
 *
 * Main patient dashboard.
 * Layout: Sidebar (left) + main area (header + scrollable messages + compose bar).
 */

import React, { useEffect, useRef, useState, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import MessageBubble from "../components/MessageBubble";
import ChatInput from "../components/ChatInput";
import PatientRecordPanel from "../components/PatientRecordPanel";
import { useChat } from "../hooks/useChat";
import { getSessions, getSessionHistory, getPatientRecord, deleteSessionHistory } from "../services/api";

const s = {
  root: {
    display: "flex",
    width: "100%",
    height: "100%",
    overflow: "hidden",
  },

  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    position: "relative",
    height: "100%",
    minWidth: 0,
  },

  feed: {
    flex: 1,
    overflowY: "auto",
    padding: "1.5rem 1.5rem 9rem",
    display: "flex",
    flexDirection: "column",
    gap: "1.25rem",
  },

  // Empty state / welcome
  welcome: {
    textAlign: "center",
    padding: "3.5rem 1rem 1rem",
  },

  welcomeIcon: {
    width: "3.5rem",
    height: "3.5rem",
    borderRadius: "1rem",
    background: "rgba(255,255,255,0.85)",
    border: "1px solid rgba(204,251,241,0.6)",
    boxShadow: "0 2px 8px rgba(15,23,42,0.06)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 1rem",
  },

  welcomeTitle: {
    fontFamily: "var(--font-display)",
    fontSize: "2rem",
    fontWeight: 400,
    color: "#1e293b",
    marginBottom: "0.5rem",
  },

  welcomeSub: {
    fontSize: "0.9375rem",
    color: "#64748b",
    marginBottom: "2rem",
  },

  quickRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: "0.625rem",
    justifyContent: "center",
    maxWidth: "32rem",
    margin: "0 auto",
  },

  quickBtn: {
    padding: "0.55rem 1rem",
    borderRadius: "9999px",
    border: "1px solid rgba(226,232,240,0.8)",
    background: "rgba(255,255,255,0.7)",
    backdropFilter: "blur(6px)",
    fontSize: "0.875rem",
    color: "#475569",
    cursor: "pointer",
    fontFamily: "var(--font-body)",
    transition: "background 150ms ease, color 150ms ease, border-color 150ms ease",
    boxShadow: "0 1px 3px rgba(15,23,42,0.05)",
  },
};

const QUICK_PROMPTS = [
  "Check my recent blood test results",
  "I have chest tightness",
  "What are my active prescriptions?",
  "Explain my last diagnosis",
];

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function getFirstName(patientId) {
  if (!patientId) return "";
  const segment = patientId.split("_")[0] || "";
  return segment.replace(/\d+$/, "");
}

/**
 * Build sidebar history items from the sessions API response.
 * Each session becomes one clickable entry.
 */
function buildHistoryItems(sessions) {
  if (!sessions || sessions.length === 0) return [];

  return sessions.map((s) => {
    const date = s.started_at ? new Date(s.started_at) : new Date();
    const dateKey = date.toLocaleDateString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
    });
    const title =
      s.first_message && s.first_message.length > 40
        ? s.first_message.slice(0, 40) + "…"
        : s.first_message || "(empty session)";

    return {
      session_id: s.session_id,
      title,
      dateKey,
      message_count: s.message_count,
      timestamp: s.started_at,
    };
  });
}

export default function ChatPage({ patientId, onLogout }) {
  const { messages, loading, sendText, sendImage, sendAudio, clearMessages, loadMessages } =
    useChat();
  const feedRef = useRef(null);

  // Sidebar history
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // ----- Patient record panel state -----
  // view: "chat" | "record"
  const [view, setView] = useState("chat");
  const [recordData, setRecordData] = useState(null);    // cached API response
  const [recordLoading, setRecordLoading] = useState(false);
  const [recordError, setRecordError] = useState(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch history when component mounts
  useEffect(() => {
    fetchHistory();
  }, []);

  // After each successful message send, refresh sidebar history
  useEffect(() => {
    if (!loading && messages.length > 0) {
      fetchHistory();
    }
  }, [loading]);

  async function fetchHistory() {
    try {
      setHistoryLoading(true);
      const data = await getSessions(20);
      const items = buildHistoryItems(data.sessions || []);
      setHistoryItems(items);
    } catch (err) {
      console.warn("Could not load sessions:", err.message);
      setHistoryItems([]);
    } finally {
      setHistoryLoading(false);
    }
  }

  /**
   * When user clicks a session item in the Sidebar:
   * Load that session's full message history into the main feed.
   */
  const handleSelectSession = useCallback(async (sessionId) => {
    try {
      const data = await getSessionHistory(sessionId);
      const msgs = data.messages || [];
      if (msgs.length === 0) return;

      const formatted = msgs.map((m, idx) => ({
        id: `hist-${sessionId}-${idx}`,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
        metadata: m.metadata || {},
        pending: false,
      }));
      loadMessages(formatted);
    } catch (err) {
      console.error("Failed to load session history:", err.message);
    }
  }, [loadMessages]);

  /**
   * When user clicks "Previous Consults" nav button:
   * Refresh session list in sidebar (already loaded, but force refresh).
   */
  const handleViewHistory = useCallback(async () => {
    await fetchHistory();
  }, []);

  /**
   * When user clicks the trash icon on a session item:
   * Calls the API to delete that session from DB, then refreshes the sidebar.
   * If the deleted session's messages are currently shown in the feed, clear them.
   */
  const handleDeleteSession = useCallback(async (sessionId) => {
    try {
      await deleteSessionHistory(sessionId);
      await fetchHistory();
    } catch (err) {
      console.error("Failed to delete session:", err.message);
      alert(`Không thể xóa cuộc trò chuyện: ${err.message}`);
    }
  }, []);

  function handleNewConsult() {
    clearMessages();
    setView("chat");   // return to chat when starting a new consult
  }

  /**
   * Triggered when user clicks "Personal Records" in the Sidebar.
   * Fetches the FHIR-based report on first click; subsequent clicks use the cache.
   */
  const handleViewRecord = useCallback(async () => {
    setView("record");
    if (recordData) return;          // already loaded — use cached data
    setRecordLoading(true);
    setRecordError(null);
    try {
      const data = await getPatientRecord();
      setRecordData(data);
    } catch (err) {
      setRecordError(err.message || "Failed to load medical record.");
    } finally {
      setRecordLoading(false);
    }
  }, [recordData]);

  /** Return from the record panel back to the chat feed. */
  const handleCloseRecord = useCallback(() => {
    setView("chat");
  }, []);

  const firstName = getFirstName(patientId) || "there";
  const showWelcome = messages.length === 0 && view === "chat";

  return (
    <div style={s.root}>
      <Sidebar
        onNewConsult={handleNewConsult}
        onLogout={onLogout}
        onViewHistory={handleViewHistory}
        onSelectSession={handleSelectSession}
        onViewRecord={handleViewRecord}
        onDeleteSession={handleDeleteSession}
        historyItems={historyItems}
        historyLoading={historyLoading}
      />

      <main style={s.main}>
        <TopBar patientId={patientId} />

        {/* Patient Record Panel — replaces feed when active */}
        {view === "record" ? (
          <PatientRecordPanel
            data={recordData}
            loading={recordLoading}
            error={recordError}
            onClose={handleCloseRecord}
          />
        ) : (
          <>
            <div style={s.feed} ref={feedRef}>
              {showWelcome && (
                <div style={s.welcome}>
                  <div style={s.welcomeIcon}>
                    <span
                      className="material-symbols-outlined"
                      style={{ fontSize: "1.75rem", color: "#0d9488" }}
                    >
                      health_and_safety
                    </span>
                  </div>
                  <h1 style={s.welcomeTitle}>
                    {getGreeting()}, {firstName}.
                  </h1>
                  <p style={s.welcomeSub}>
                    How can MedScreening assist you with your health today?
                  </p>

                  <div style={s.quickRow}>
                    {QUICK_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        style={s.quickBtn}
                        onClick={() => sendText(prompt)}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "rgba(204,251,241,0.45)";
                          e.currentTarget.style.color = "#0f766e";
                          e.currentTarget.style.borderColor = "rgba(20,184,166,0.35)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "rgba(255,255,255,0.7)";
                          e.currentTarget.style.color = "#475569";
                          e.currentTarget.style.borderColor = "rgba(226,232,240,0.8)";
                        }}
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </div>

            <ChatInput
              onSendText={sendText}
              onSendImage={sendImage}
              onSendAudio={sendAudio}
              disabled={loading}
            />
          </>
        )}
      </main>
    </div>
  );
}