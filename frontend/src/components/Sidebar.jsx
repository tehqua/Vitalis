/**
 * Sidebar.jsx
 *
 * Left navigation panel.
 * - "Previous Consults" load lịch sử chat thật từ backend
 * - Recent History hiện các tin nhắn thật của user (truyền từ ChatPage)
 */

import React from "react";

const s = {
  aside: {
    width: "15rem",
    flexShrink: 0,
    display: "flex",
    flexDirection: "column",
    height: "100%",
    borderRight: "1px solid rgba(226,232,240,0.7)",
    background: "rgba(255,255,255,0.52)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
  },

  header: {
    height: "3.75rem",
    display: "flex",
    alignItems: "center",
    padding: "0 1.25rem",
    borderBottom: "1px solid rgba(241,245,249,0.8)",
    flexShrink: 0,
  },

  logoText: {
    fontFamily: "var(--font-display)",
    fontSize: "1.1rem",
    fontWeight: 400,
    color: "#0f766e",
    letterSpacing: "-0.01em",
  },

  logoIcon: {
    fontSize: "1.5rem",
    color: "#0f766e",
    marginRight: "0.5rem",
  },

  nav: {
    flex: 1,
    overflowY: "auto",
    padding: "1.25rem 0.625rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.125rem",
  },

  navBtn: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: "0.625rem",
    padding: "0.625rem 0.75rem",
    borderRadius: "0.625rem",
    border: "none",
    background: "transparent",
    cursor: "pointer",
    fontSize: "0.875rem",
    fontFamily: "var(--font-body)",
    fontWeight: 500,
    color: "#475569",
    textAlign: "left",
    transition: "background 160ms ease, color 160ms ease",
  },

  navBtnActive: {
    background: "rgba(255,255,255,0.85)",
    color: "#0f766e",
    boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
    border: "1px solid rgba(226,232,240,0.6)",
  },

  sectionLabel: {
    padding: "1.25rem 0.75rem 0.375rem",
    fontSize: "0.6875rem",
    fontWeight: 700,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "#94a3b8",
  },

  historyLink: {
    display: "flex",
    flexDirection: "column",
    gap: "0.15rem",
    padding: "0.45rem 0.75rem",
    borderRadius: "0.5rem",
    fontSize: "0.8125rem",
    color: "#64748b",
    cursor: "pointer",
    background: "none",
    border: "none",
    width: "100%",
    textAlign: "left",
    fontFamily: "var(--font-body)",
    transition: "color 140ms ease, background 140ms ease",
  },

  historyTitle: {
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    fontSize: "0.8125rem",
    color: "#334155",
  },

  historyDate: {
    fontSize: "0.7rem",
    color: "#94a3b8",
  },

  emptyHistory: {
    padding: "0.5rem 0.75rem",
    fontSize: "0.8rem",
    color: "#94a3b8",
    fontStyle: "italic",
  },

  historySpinner: {
    padding: "0.5rem 0.75rem",
    fontSize: "0.8rem",
    color: "#94a3b8",
    display: "flex",
    alignItems: "center",
    gap: "0.4rem",
  },

  footer: {
    padding: "0.75rem 0.625rem",
    borderTop: "1px solid rgba(241,245,249,0.8)",
    flexShrink: 0,
  },
};

export default function Sidebar({
  onNewConsult,
  onLogout,
  onViewHistory,
  historyItems = [],
  historyLoading = false,
}) {
  const [active, setActive] = React.useState("personal");

  function navItem(key, icon, label, onClick) {
    const isActive = active === key;
    return (
      <button
        key={key}
        style={{ ...s.navBtn, ...(isActive ? s.navBtnActive : {}) }}
        onClick={() => {
          setActive(key);
          if (onClick) onClick();
        }}
        onMouseEnter={(e) => {
          if (!isActive) {
            e.currentTarget.style.background = "rgba(255,255,255,0.55)";
            e.currentTarget.style.color = "#0d9488";
          }
        }}
        onMouseLeave={(e) => {
          if (!isActive) {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "#475569";
          }
        }}
      >
        <span
          className="material-symbols-outlined"
          style={{ fontSize: "1.25rem", color: isActive ? "#0d9488" : "inherit" }}
        >
          {icon}
        </span>
        {label}
      </button>
    );
  }

  return (
    <aside style={s.aside}>
      {/* Brand */}
      <div style={s.header}>
        <span className="material-symbols-outlined" style={s.logoIcon}>
          medical_services
        </span>
        <span style={s.logoText}>MedScreening</span>
      </div>

      <nav style={s.nav}>
        {/* New consultation CTA */}
        <button
          style={{ ...s.navBtn, color: "#0d9488", fontWeight: 500 }}
          onClick={onNewConsult}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(204,251,241,0.35)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: "1.25rem" }}>
            add_circle
          </span>
          New Consultation
        </button>

        {/* Shortcuts */}
        <div style={s.sectionLabel}>Shortcuts</div>

        {/* Personal Records — không có action đặc biệt */}
        {navItem("personal", "assignment_ind", "Personal Records")}

        {/* Previous Consults — load history vào feed */}
        {navItem("consults", "history", "Previous Consults", onViewHistory)}

        {/* Recent History — dùng data thật từ backend */}
        <div style={s.sectionLabel}>Recent History</div>

        {historyLoading ? (
          <div style={s.historySpinner}>
            <span
              className="material-symbols-outlined"
              style={{ fontSize: "0.875rem", animation: "spin 1s linear infinite" }}
            >
              progress_activity
            </span>
            Loading…
          </div>
        ) : historyItems.length === 0 ? (
          <div style={s.emptyHistory}>No history yet</div>
        ) : (
          historyItems.map((item, idx) => (
            <button
              key={idx}
              style={s.historyLink}
              title={item.title}
              onClick={() => {
                setActive("consults");
                if (onViewHistory) onViewHistory();
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#0d9488";
                e.currentTarget.style.background = "rgba(255,255,255,0.45)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "#64748b";
                e.currentTarget.style.background = "none";
              }}
            >
              <span style={s.historyTitle}>{item.title}</span>
              <span style={s.historyDate}>{item.dateKey}</span>
            </button>
          ))
        )}
      </nav>

      {/* Footer actions */}
      <div style={s.footer}>
        <button
          style={{ ...s.navBtn }}
          onClick={onLogout}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(254,242,242,0.6)";
            e.currentTarget.style.color = "#dc2626";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "#475569";
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: "1.25rem" }}>
            logout
          </span>
          Sign Out
        </button>
      </div>
    </aside>
  );
}