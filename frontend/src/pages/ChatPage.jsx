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
import { useChat } from "../hooks/useChat";
import { getHistory } from "../services/api";

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
 * Convert conversation history from backend into a list of "sessions" for Sidebar.
 * Backend returns messages like: [{role:"user", content, timestamp}, {role:"assistant", ...}]
 * Group by date and use the first user message as the title.
 */
function buildHistoryItems(messages) {
  if (!messages || messages.length === 0) return [];

  // Get user messages, use content as title
  const userMessages = messages.filter((m) => m.role === "user");

  // Deduplicate by date + content, take maximum 8 most recent items
  const seen = new Set();
  const items = [];

  for (const msg of [...userMessages].reverse()) {
    const date = new Date(msg.timestamp);
    const dateKey = date.toLocaleDateString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
    });

    // Truncate title if too long
    const title =
      msg.content.length > 40
        ? msg.content.slice(0, 40) + "…"
        : msg.content;

    const key = `${dateKey}-${title}`;
    if (!seen.has(key)) {
      seen.add(key);
      items.push({ title, dateKey, timestamp: msg.timestamp });
    }

    if (items.length >= 8) break;
  }

  return items;
}

export default function ChatPage({ patientId, onLogout }) {
  const { messages, loading, sendText, sendImage, sendAudio, clearMessages, loadMessages } =
    useChat();
  const feedRef = useRef(null);

  // History to show in Sidebar
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

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
      const data = await getHistory(50);
      const items = buildHistoryItems(data.messages || []);
      setHistoryItems(items);
    } catch (err) {
      // If no history or error, leave empty
      console.warn("Could not load history:", err.message);
      setHistoryItems([]);
    } finally {
      setHistoryLoading(false);
    }
  }

  /**
   * When user clicks "Previous Consults" in Sidebar:
   * Load the entire history into the main feed.
   */
  const handleViewHistory = useCallback(async () => {
    try {
      const data = await getHistory(50);
      const msgs = data.messages || [];

      if (msgs.length === 0) {
        // No history, do nothing
        return;
      }

      // Convert backend format → useChat messages format
      // Backend: [{role, content, timestamp, metadata?}]
      const formatted = msgs.map((m, idx) => ({
        id: `history-${idx}`,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
        metadata: m.metadata || {},
        pending: false,
      }));

      loadMessages(formatted);
    } catch (err) {
      console.error("Failed to load history:", err.message);
    }
  }, [loadMessages]);

  function handleNewConsult() {
    clearMessages();
  }

  const firstName = getFirstName(patientId) || "there";
  const showWelcome = messages.length === 0;

  return (
    <div style={s.root}>
      <Sidebar
        onNewConsult={handleNewConsult}
        onLogout={onLogout}
        onViewHistory={handleViewHistory}
        historyItems={historyItems}
        historyLoading={historyLoading}
      />

      <main style={s.main}>
        <TopBar patientId={patientId} />

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
      </main>
    </div>
  );
}