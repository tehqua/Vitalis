import { useState } from 'react';

interface AdminSidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  newForgotCount?: number;
  onLogout?: () => void;
}

const navItems = [
  { id: 'overview', label: 'Overview', icon: 'dashboard' },
  { id: 'forgot-id', label: 'Forgot ID Requests', icon: 'help_center' },
];

const s = {
  sidebar: {
    width: 240,
    minWidth: 240,
    height: '100vh',
    background: 'rgba(255,255,255,0.72)',
    backdropFilter: 'blur(14px)',
    borderRight: '1px solid rgba(255,255,255,0.55)',
    display: 'flex',
    flexDirection: 'column' as const,
    position: 'fixed' as const,
    left: 0,
    top: 0,
    zIndex: 50,
  },
  logo: {
    padding: '1.5rem',
    borderBottom: '1px solid #e2e8f0',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  logoIcon: {
    width: 36,
    height: 36,
    borderRadius: '0.625rem',
    background: '#0d9488',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontSize: 20,
  },
  logoText: {
    fontFamily: '"DM Serif Display", Georgia, serif',
    fontSize: '1.125rem',
    color: '#1e293b',
    fontWeight: 400,
  },
  nav: {
    flex: 1,
    padding: '0.75rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.25rem',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.625rem 0.875rem',
    borderRadius: '0.625rem',
    cursor: 'pointer',
    transition: 'all 150ms ease',
    border: 'none',
    background: 'transparent',
    width: '100%',
    textAlign: 'left' as const,
    fontFamily: '"DM Sans", system-ui, sans-serif',
    fontSize: '0.875rem',
    color: '#64748b',
    position: 'relative' as const,
  },
  navItemActive: {
    background: '#f0fdfa',
    color: '#0d9488',
    fontWeight: 600,
    borderLeft: '3px solid #0d9488',
  },
  navItemHover: {
    background: '#f8fafc',
  },
  footer: {
    padding: '1rem 1.5rem',
    borderTop: '1px solid #e2e8f0',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: '9999px',
    background: '#0d9488',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.75rem',
    fontWeight: 600,
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  adminInfo: {
    flex: 1,
  },
  adminName: {
    fontSize: '0.8125rem',
    fontWeight: 600,
    color: '#1e293b',
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  adminRole: {
    fontSize: '0.6875rem',
    color: '#94a3b8',
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  logoutBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#94a3b8',
    padding: 4,
    borderRadius: '0.375rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'color 150ms ease',
  },
};

export default function AdminSidebar({ activeTab, onTabChange, newForgotCount = 0, onLogout }: AdminSidebarProps) {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  return (
    <aside style={s.sidebar}>
      <div style={s.logo}>
        <div style={s.logoIcon}>
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>health_and_safety</span>
        </div>
        <span style={s.logoText}>Vitalis Admin</span>
      </div>

      <nav style={s.nav}>
        {navItems.map(item => {
          const isActive = activeTab === item.id;
          const isHovered = hoveredItem === item.id;
          const isForgot = item.id === 'forgot-id';
          const showBadge = isForgot && newForgotCount > 0;
          return (
            <button
              key={item.id}
              style={{
                ...s.navItem,
                ...(isActive ? s.navItemActive : {}),
                ...(!isActive && isHovered ? s.navItemHover : {}),
              }}
              onClick={() => onTabChange(item.id)}
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>{item.icon}</span>
              <span style={{ flex: 1, textAlign: 'left' }}>{item.label}</span>
              {showBadge && (
                <span style={{
                  background: '#dc2626',
                  color: '#fff',
                  borderRadius: '9999px',
                  fontSize: '0.625rem',
                  fontWeight: 700,
                  minWidth: 18,
                  height: 18,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0 5px',
                }}>
                  {newForgotCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div style={s.footer}>
        <div style={s.avatar}>AD</div>
        <div style={s.adminInfo}>
          <div style={s.adminName}>Dr. Admin</div>
          <div style={s.adminRole}>Administrator</div>
        </div>
        <button
          style={s.logoutBtn}
          title="Logout"
          onClick={onLogout}
          onMouseEnter={e => (e.currentTarget.style.color = '#dc2626')}
          onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>logout</span>
        </button>
      </div>
    </aside>
  );
}
