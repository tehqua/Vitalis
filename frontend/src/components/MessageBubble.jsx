/**
 * MessageBubble.jsx
 *
 * Renders a single chat message from either the user or the assistant.
 * Handles pending state (thinking indicator), errors, image previews,
 * and metadata (source tags, confidence, next-step suggestions).
 */

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const s = {
  row: {
    display: "flex",
    gap: "0.875rem",
  },

  rowUser: {
    justifyContent: "flex-end",
  },

  avatar: {
    flexShrink: 0,
    width: "2rem",
    height: "2rem",
    borderRadius: "9999px",
    background: "rgba(204,251,241,0.8)",
    border: "1px solid rgba(20,184,166,0.2)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "flex-end",
    marginBottom: "0.125rem",
  },

  avatarIcon: {
    fontSize: "1rem",
    color: "#0d9488",
  },

  bubbleUser: {
    maxWidth: "78%",
    background: "#1e293b",
    color: "#f8fafc",
    padding: "0.8rem 1.1rem",
    borderRadius: "1.2rem 1.2rem 0.25rem 1.2rem",
    fontSize: "0.9375rem",
    lineHeight: 1.6,
    boxShadow: "0 2px 8px rgba(15,23,42,0.18)",
  },

  bubbleAssistant: {
    maxWidth: "85%",
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },

  card: {
    background: "rgba(255,255,255,0.65)",
    backdropFilter: "blur(10px)",
    WebkitBackdropFilter: "blur(10px)",
    border: "1px solid rgba(255,255,255,0.5)",
    borderRadius: "1.2rem 1.2rem 1.2rem 0.25rem",
    padding: "1.25rem 1.375rem",
    color: "#334155",
    fontSize: "0.9375rem",
    lineHeight: 1.7,
    boxShadow: "0 2px 12px rgba(15,23,42,0.06)",
  },

  tagsRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: "0.4rem",
    marginBottom: "0.875rem",
  },

  tag: {
    display: "inline-flex",
    alignItems: "center",
    gap: "0.3rem",
    padding: "0.25rem 0.625rem",
    borderRadius: "0.375rem",
    fontSize: "0.7rem",
    fontWeight: 600,
    letterSpacing: "0.02em",
  },

  tagSource: {
    background: "#eef2ff",
    color: "#4338ca",
    border: "1px solid #e0e7ff",
  },

  tagModel: {
    background: "#f0fdfa",
    color: "#0f766e",
    border: "1px solid #ccfbf1",
  },

  disclaimer: {
    background: "rgba(255,251,235,0.8)",
    border: "1px solid rgba(254,215,170,0.6)",
    borderRadius: "0.75rem",
    padding: "0.75rem 1rem",
    display: "flex",
    gap: "0.6rem",
    alignItems: "flex-start",
    marginTop: "0.75rem",
  },

  disclaimerIcon: {
    fontSize: "1.1rem",
    color: "#d97706",
    flexShrink: 0,
    marginTop: "0.1rem",
  },

  disclaimerTitle: {
    fontSize: "0.8125rem",
    fontWeight: 700,
    color: "#92400e",
    marginBottom: "0.2rem",
  },

  disclaimerText: {
    fontSize: "0.8125rem",
    color: "#92400e",
    lineHeight: 1.55,
  },

  // Confidence badge
  confidence: {
    fontSize: "0.8rem",
    color: "#64748b",
    marginTop: "0.375rem",
  },

  suggestionsRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: "0.5rem",
    paddingLeft: "0.125rem",
  },

  suggestionBtn: {
    padding: "0.45rem 0.9rem",
    borderRadius: "9999px",
    background: "rgba(255,255,255,0.65)",
    border: "1px solid rgba(226,232,240,0.8)",
    fontSize: "0.8125rem",
    color: "#475569",
    cursor: "pointer",
    fontFamily: "var(--font-body)",
    transition: "background 150ms ease, border-color 150ms ease, color 150ms ease",
    boxShadow: "0 1px 3px rgba(15,23,42,0.05)",
  },

  actionBtn: {
    padding: "0.5rem 1rem",
    borderRadius: "9999px",
    background: "#0d9488",
    border: "none",
    fontSize: "0.8125rem",
    fontWeight: 600,
    color: "#ffffff",
    cursor: "pointer",
    fontFamily: "var(--font-body)",
    display: "flex",
    alignItems: "center",
    gap: "0.4rem",
    boxShadow: "0 2px 8px rgba(13,148,136,0.32)",
    transition: "background 150ms ease, transform 150ms ease",
  },

  // Pending / typing indicator
  pendingDot: {
    width: "0.5rem",
    height: "0.5rem",
    borderRadius: "9999px",
    background: "#94a3b8",
  },

  dotsWrap: {
    display: "flex",
    alignItems: "center",
    gap: "0.3rem",
    padding: "0.25rem 0",
  },

  errorCard: {
    background: "rgba(254,242,242,0.8)",
    border: "1px solid rgba(254,202,202,0.7)",
    borderRadius: "1rem 1rem 1rem 0.25rem",
    padding: "0.875rem 1.125rem",
    color: "#dc2626",
    fontSize: "0.875rem",
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
  },

  imagePreview: {
    borderRadius: "0.875rem",
    overflow: "hidden",
    maxWidth: "260px",
    marginBottom: "0.375rem",
  },
};

function TypingDots() {
  return (
    <div style={{ ...s.card, padding: "0.875rem 1.25rem" }}>
      <div style={s.dotsWrap}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              ...s.pendingDot,
              animation: `pulse 1.2s ease ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function AssistantCard({ message }) {
  const meta = message.metadata || {};
  const isMultimodal = meta.input_type === "multimodal";
  const isAudio = meta.input_type === "audio";
  const confidence = meta.image_analysis?.confidence;
  const className = meta.image_analysis?.class_name;

  return (
    <>
      <div style={s.card}>
        {/* Source / model tags */}
        <div style={s.tagsRow}>
          {isMultimodal && (
            <span style={{ ...s.tag, ...s.tagModel }}>
              <span className="material-symbols-outlined" style={{ fontSize: "0.8rem" }}>
                view_in_ar
              </span>
            </span>
          )}
          {isAudio && (
            <span style={{ ...s.tag, ...s.tagSource }}>
              <span className="material-symbols-outlined" style={{ fontSize: "0.8rem" }}>
                record_voice_over
              </span>
            </span>
          )}
          {!isMultimodal && !isAudio && (
            <span style={{ ...s.tag, ...s.tagSource }}>
              <span className="material-symbols-outlined" style={{ fontSize: "0.8rem" }}>
                database
              </span>
            </span>
          )}
        </div>

        {/* Main response text — render as plain text preserving newlines */}
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
        
        {/* Image analysis confidence */}
        {confidence != null && (
          <p style={s.confidence}>
            {className
              ? `Classification: ${className.replace(/_/g, " ")} — Confidence: ${(confidence * 100).toFixed(0)}%`
              : `Confidence: ${(confidence * 100).toFixed(0)}%`}
          </p>
        )}

        {/* Medical disclaimer shown on every assistant reply */}
        <div style={s.disclaimer}>
          <span className="material-symbols-outlined" style={s.disclaimerIcon}>
            warning
          </span>
          <div>
            <div style={s.disclaimerTitle}>Disclaimer</div>
            <div style={s.disclaimerText}>
              I am an AI assistant. My analysis is for informational purposes
              only and does not replace a professional medical diagnosis. If
              you experience severe pain, swelling, or fever, please visit the
              ER immediately.
            </div>
          </div>
        </div>
      </div>

      {/* Quick-action buttons */}
    </>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div style={{ ...s.row, ...s.rowUser }}>
        <div style={s.bubbleUser}>
          {/* Image preview if attached */}
          {message.imageUrl && (
            <div style={s.imagePreview}>
              <img
                src={message.imageUrl}
                alt="Attached"
                style={{ width: "100%", maxHeight: "200px", objectFit: "cover", display: "block" }}
              />
            </div>
          )}
          {message.content && <span>{message.content}</span>}
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div style={s.row}>
      <div style={s.avatar}>
        <span className="material-symbols-outlined" style={s.avatarIcon}>
          smart_toy
        </span>
      </div>

      <div style={s.bubbleAssistant}>
        {message.pending ? (
          <TypingDots />
        ) : message.error ? (
          <div style={s.errorCard}>
            <span className="material-symbols-outlined" style={{ fontSize: "1rem" }}>
              error
            </span>
            {message.error}
          </div>
        ) : (
          <AssistantCard message={message} />
        )}
      </div>
    </div>
  );
}
