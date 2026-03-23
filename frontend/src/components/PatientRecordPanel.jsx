/**
 * PatientRecordPanel.jsx
 *
 * Renders the comprehensive patient medical record report.
 * Each of the 8 FHIR-parsed sections appears as a separate card.
 * Displayed when the user clicks "Personal Records" in the Sidebar.
 */

import React, { useState } from "react";

// ─── Section metadata ────────────────────────────────────────────────────────
const SECTION_META = [
  { key: "demographics",  icon: "person",          label: "Personal Information",        color: "#0d9488" },
  { key: "conditions",    icon: "stethoscope",      label: "Diagnoses & Conditions",      color: "#ea580c" },
  { key: "encounters",    icon: "calendar_month",   label: "Encounter History",           color: "#2563eb" },
  { key: "medications",   icon: "medication",       label: "Medications",                 color: "#9333ea" },
  { key: "vitals",        icon: "monitor_heart",    label: "Vital Signs & Observations",  color: "#dc2626" },
  { key: "immunizations", icon: "vaccines",         label: "Immunizations",               color: "#16a34a" },
  { key: "devices",       icon: "settings",         label: "Implanted Devices",           color: "#64748b" },
  { key: "billing",       icon: "payments",         label: "Insurance & Billing",         color: "#4f46e5" },
];

// ─── Styles ──────────────────────────────────────────────────────────────────
const s = {
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    overflowY: "auto",
    background: "linear-gradient(160deg, #f0fdf9 0%, #f8fafc 50%, #eff6ff 100%)",
  },

  // Top bar
  topBar: {
    position: "sticky",
    top: 0,
    zIndex: 10,
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
    padding: "0.875rem 1.5rem",
    background: "rgba(255,255,255,0.82)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    borderBottom: "1px solid rgba(226,232,240,0.7)",
    boxShadow: "0 1px 6px rgba(15,23,42,0.06)",
  },

  backBtn: {
    display: "flex",
    alignItems: "center",
    gap: "0.35rem",
    padding: "0.45rem 0.875rem",
    borderRadius: "9999px",
    border: "1px solid rgba(226,232,240,0.9)",
    background: "rgba(255,255,255,0.8)",
    cursor: "pointer",
    fontSize: "0.8125rem",
    fontFamily: "var(--font-body)",
    fontWeight: 500,
    color: "#475569",
    transition: "background 150ms ease, color 150ms ease",
  },

  topBarTitle: {
    flex: 1,
    fontFamily: "var(--font-display)",
    fontSize: "1.125rem",
    color: "#0f172a",
    fontWeight: 400,
  },

  topBarSub: {
    fontSize: "0.75rem",
    color: "#64748b",
  },

  // Content grid
  content: {
    padding: "1.5rem",
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 480px), 1fr))",
    gap: "1rem",
    maxWidth: "1100px",
    margin: "0 auto",
    width: "100%",
  },

  // Patient header card (spans full width)
  headerCard: {
    gridColumn: "1 / -1",
    background: "linear-gradient(135deg, #0f766e 0%, #0d9488 60%, #14b8a6 100%)",
    borderRadius: "1.25rem",
    padding: "1.5rem 2rem",
    color: "#ffffff",
    boxShadow: "0 4px 20px rgba(13,148,136,0.28)",
    display: "flex",
    alignItems: "center",
    gap: "1.25rem",
    flexWrap: "wrap",
  },

  headerIcon: {
    width: "3.5rem",
    height: "3.5rem",
    borderRadius: "1rem",
    background: "rgba(255,255,255,0.2)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },

  headerName: {
    fontFamily: "var(--font-display)",
    fontSize: "1.75rem",
    fontWeight: 400,
    letterSpacing: "-0.01em",
  },

  headerMeta: {
    fontSize: "0.8125rem",
    color: "rgba(255,255,255,0.8)",
    marginTop: "0.25rem",
  },

  // Section card
  card: {
    background: "rgba(255,255,255,0.82)",
    backdropFilter: "blur(10px)",
    WebkitBackdropFilter: "blur(10px)",
    border: "1px solid rgba(255,255,255,0.75)",
    borderRadius: "1.125rem",
    overflow: "hidden",
    boxShadow: "0 2px 12px rgba(15,23,42,0.07)",
    transition: "box-shadow 200ms ease, transform 200ms ease",
  },

  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
    padding: "1rem 1.25rem 0.75rem",
    borderBottom: "1px solid rgba(241,245,249,0.9)",
  },

  cardIconWrap: {
    width: "2.25rem",
    height: "2.25rem",
    borderRadius: "0.625rem",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },

  cardTitle: {
    fontFamily: "var(--font-display)",
    fontSize: "0.9375rem",
    fontWeight: 400,
    color: "#0f172a",
  },

  cardBody: {
    padding: "1rem 1.25rem",
    fontFamily: "var(--font-body, 'Inter', monospace)",
    fontSize: "0.8125rem",
    lineHeight: 1.75,
    color: "#334155",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    maxHeight: "320px",
    overflowY: "auto",
  },

  // Loading skeleton
  skeletonCard: {
    background: "rgba(255,255,255,0.72)",
    border: "1px solid rgba(226,232,240,0.7)",
    borderRadius: "1.125rem",
    padding: "1rem 1.25rem",
    animation: "shimmer 1.6s ease-in-out infinite",
  },

  skeletonLine: (width) => ({
    height: "0.75rem",
    borderRadius: "9999px",
    background: "linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)",
    backgroundSize: "200% 100%",
    marginBottom: "0.625rem",
    width,
  }),

  // Error state
  errorCard: {
    gridColumn: "1 / -1",
    background: "rgba(254,242,242,0.9)",
    border: "1px solid #fecaca",
    borderRadius: "1.125rem",
    padding: "2rem",
    textAlign: "center",
    color: "#dc2626",
  },

  emptyNote: {
    color: "#94a3b8",
    fontStyle: "italic",
  },
};

// ─── Skeleton loading placeholder ────────────────────────────────────────────
function SkeletonCards() {
  return (
    <>
      {[100, 60, 80, 100, 70, 90].map((w, i) => (
        <div key={i} style={s.skeletonCard}>
          <div style={s.skeletonLine(`${w}%`)} />
          <div style={s.skeletonLine("80%")} />
          <div style={s.skeletonLine("60%")} />
        </div>
      ))}
    </>
  );
}

// ─── Individual section card ──────────────────────────────────────────────────
function SectionCard({ meta, text }) {
  const [hovered, setHovered] = useState(false);

  // Strip leading section header line (already shown in cardTitle)
  const body = (text || "")
    .split("\n")
    .slice(2) // skip "📋  I. ..." and "─────..." lines
    .join("\n")
    .trim();

  const isEmpty = !body || body === "No conditions recorded." || body.length < 3;

  return (
    <div
      style={{
        ...s.card,
        ...(hovered
          ? { boxShadow: "0 6px 24px rgba(15,23,42,0.12)", transform: "translateY(-1px)" }
          : {}),
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={s.cardHeader}>
        <div
          style={{
            ...s.cardIconWrap,
            background: `${meta.color}18`,
            border: `1px solid ${meta.color}30`,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: "1.25rem", color: meta.color }}
          >
            {meta.icon}
          </span>
        </div>
        <span style={s.cardTitle}>{meta.label}</span>
      </div>

      <div style={s.cardBody}>
        {isEmpty ? (
          <span style={s.emptyNote}>No data recorded.</span>
        ) : (
          body
        )}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
/**
 * @param {object}   props
 * @param {object}   props.data         - API response from GET /api/chat/patient-record
 * @param {boolean}  props.loading      - true while fetching
 * @param {string}   props.error        - error message, or null
 * @param {function} props.onClose      - callback to return to chat view
 */
export default function PatientRecordPanel({ data, loading, error, onClose }) {
  return (
    <div style={s.root}>
      {/* ── Sticky top bar ── */}
      <div style={s.topBar}>
        <button
          style={s.backBtn}
          onClick={onClose}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(204,251,241,0.5)";
            e.currentTarget.style.color = "#0f766e";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.8)";
            e.currentTarget.style.color = "#475569";
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: "1rem" }}>
            arrow_back
          </span>
          Back to Chat
        </button>

        <div>
          <div style={s.topBarTitle}>Personal Records</div>
          {data && (
            <div style={s.topBarSub}>
              Generated: {data.generated_at
                ? new Date(data.generated_at).toLocaleString("vi-VN")
                : "—"}
            </div>
          )}
        </div>
      </div>

      {/* ── Content ── */}
      <div style={s.content}>
        {/* Loading */}
        {loading && <SkeletonCards />}

        {/* Error */}
        {!loading && error && (
          <div style={s.errorCard}>
            <span
              className="material-symbols-outlined"
              style={{ fontSize: "2.5rem", display: "block", marginBottom: "0.75rem" }}
            >
              folder_off
            </span>
            <p style={{ fontWeight: 600, marginBottom: "0.375rem" }}>
              Medical record not found
            </p>
            <p style={{ fontSize: "0.875rem", color: "#ef4444" }}>{error}</p>
          </div>
        )}

        {/* Report */}
        {!loading && !error && data && (
          <>
            {/* Patient header card */}
            <div style={s.headerCard}>
              <div style={s.headerIcon}>
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: "2rem", color: "#ffffff" }}
                >
                  assignment_ind
                </span>
              </div>
              <div>
                <div style={s.headerName}>{data.patient_name}</div>
                <div style={s.headerMeta}>
                  Patient ID: {data.patient_id}
                </div>
              </div>
            </div>

            {/* Section cards */}
            {SECTION_META.map((meta) => (
              <SectionCard
                key={meta.key}
                meta={meta}
                text={data.sections?.[meta.key] || ""}
              />
            ))}
          </>
        )}
      </div>

      {/* Shimmer keyframe */}
      <style>{`
        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position:  200% 0; }
        }
      `}</style>
    </div>
  );
}
