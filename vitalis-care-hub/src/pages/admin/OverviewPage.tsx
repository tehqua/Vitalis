import { useState, useEffect, useCallback } from 'react';
import AdminTopBar from '../../components/admin/AdminTopBar';
import StatCard from '../../components/admin/StatCard';
import StatusBadge from '../../components/admin/StatusBadge';
import { fetchOverviewStats, fetchRecentActivity, fetchSystemStatus, OverviewStats, ActivityItem, SystemService } from '../../lib/api';

const statusColor: Record<string, string> = {
  Operational: '#22c55e',
  Degraded: '#d97706',
  Down: '#dc2626',
};

const s = {
  content: { padding: '0 2rem 2rem' },
  statsRow: { display: 'flex', gap: '1rem', flexWrap: 'wrap' as const },
  section: {
    background: 'rgba(255,255,255,0.72)', backdropFilter: 'blur(14px)',
    border: '1px solid rgba(255,255,255,0.55)', borderRadius: '0.875rem',
    boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)', marginTop: '1.5rem', overflow: 'hidden',
  },
  sectionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.25rem', borderBottom: '1px solid #e2e8f0' },
  sectionTitle: { fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.9375rem', fontWeight: 600, color: '#1e293b', margin: 0 },
  refreshBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.75rem', fontFamily: '"DM Sans", system-ui, sans-serif', padding: '0.25rem 0.5rem', borderRadius: '0.375rem', transition: 'color 150ms ease' },
  table: { width: '100%', borderCollapse: 'collapse' as const, fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.8125rem' },
  th: { textAlign: 'left' as const, padding: '0.625rem 1.25rem', color: '#94a3b8', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase' as const, letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' },
  td: { padding: '0.625rem 1.25rem', color: '#334155', borderBottom: '1px solid #f1f5f9' },
  systemStrip: { display: 'flex', gap: '1.5rem', padding: '1rem 1.25rem', flexWrap: 'wrap' as const },
  statusDot: (color: string) => ({ width: 8, height: 8, borderRadius: '9999px', background: color, display: 'inline-block', marginRight: 6 }),
  statusItem: { display: 'flex', alignItems: 'center', fontSize: '0.8125rem', color: '#475569', fontFamily: '"DM Sans", system-ui, sans-serif' },
  emptyRow: { textAlign: 'center' as const, padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' },
};

export default function OverviewPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemService[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, a, sys] = await Promise.allSettled([
        fetchOverviewStats(),
        fetchRecentActivity(),
        fetchSystemStatus(),
      ]);
      if (s.status === 'fulfilled') setStats(s.value);
      if (a.status === 'fulfilled') setActivity(a.value);
      if (sys.status === 'fulfilled') setSystemStatus(sys.value);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const statCards = stats ? [
    { icon: 'group', value: stats.active_patients, label: 'Patients currently using Vitalis', trend: '' },
    { icon: 'chat_bubble', value: stats.sessions_today, label: 'Chat sessions in last 24h', trend: '' },
    { icon: 'notifications', value: stats.reminders_sent_today, label: 'Email reminders sent today', trend: '' },
    { icon: 'pending', value: stats.pending_codes, label: 'Pending activation codes', trend: '' },
  ] : [];

  return (
    <>
      <AdminTopBar title="Overview" subtitle="System dashboard at a glance" />
      <div style={s.content}>
        {loading && !stats ? (
          <div style={{ color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.875rem', padding: '1rem 0' }}>Loading dashboard...</div>
        ) : (
          <div style={s.statsRow}>
            {statCards.map((st, i) => (
              <StatCard key={i} icon={st.icon} value={st.value} label={st.label} trend={st.trend} />
            ))}
          </div>
        )}

        <div style={s.section}>
          <div style={s.sectionHeader}>
            <h3 style={s.sectionTitle}>Recent Activity</h3>
            <button style={s.refreshBtn} onClick={load}
              onMouseEnter={e => (e.currentTarget.style.color = '#0d9488')}
              onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>refresh</span>
              Refresh
            </button>
          </div>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Time</th>
                <th style={s.th}>Type</th>
                <th style={s.th}>Patient</th>
                <th style={s.th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {activity.length === 0 ? (
                <tr><td colSpan={4} style={s.emptyRow}>{loading ? 'Loading...' : 'No recent activity.'}</td></tr>
              ) : activity.map((a, i) => (
                <tr key={i} style={{ transition: 'background 150ms ease' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(240,253,250,0.5)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <td style={s.td}>{a.time}</td>
                  <td style={s.td}>{a.type}</td>
                  <td style={s.td}>{a.patient}</td>
                  <td style={s.td}><StatusBadge status={a.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={s.section}>
          <h3 style={{ ...s.sectionTitle, padding: '1rem 1.25rem', borderBottom: '1px solid #e2e8f0' }}>System Status</h3>
          <div style={s.systemStrip}>
            {systemStatus.length === 0 ? (
              <span style={{ color: '#94a3b8', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif' }}>
                {loading ? 'Loading...' : 'Status unavailable.'}
              </span>
            ) : systemStatus.map((sys, i) => (
              <div key={i} style={s.statusItem}>
                <span style={s.statusDot(statusColor[sys.status] ?? '#94a3b8')} />
                {sys.name} — {sys.status}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
