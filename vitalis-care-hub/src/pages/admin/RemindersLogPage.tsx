import { useState, useEffect, useCallback } from 'react';
import AdminTopBar from '../../components/admin/AdminTopBar';
import StatusBadge from '../../components/admin/StatusBadge';
import { fetchReminderLogs, ReminderLog } from '../../lib/api';

const filters = ['All', 'Delivered', 'Failed', 'Pending'];

const s = {
  content: { padding: '0 2rem 2rem' },
  statsStrip: { display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' as const },
  statPill: {
    background: 'rgba(255,255,255,0.72)', backdropFilter: 'blur(14px)',
    border: '1px solid rgba(255,255,255,0.55)', borderRadius: '0.875rem',
    padding: '0.875rem 1.25rem', boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)',
    flex: 1, minWidth: 160,
  },
  statLabel: { fontSize: '0.75rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif', marginBottom: 2 },
  statValue: { fontSize: '1.125rem', fontWeight: 700, color: '#1e293b', fontFamily: '"DM Sans", system-ui, sans-serif' },
  statSub: { fontSize: '0.75rem', color: '#dc2626', fontFamily: '"DM Sans", system-ui, sans-serif' },
  toolbar: { display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' as const, marginBottom: '1rem' },
  searchInput: { padding: '0.5rem 0.875rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none', width: 260, transition: 'border-color 150ms ease' },
  filterBtn: (active: boolean) => ({ padding: '0.375rem 0.875rem', border: active ? '1px solid #0d9488' : '1px solid #e2e8f0', borderRadius: '9999px', background: active ? '#f0fdfa' : 'transparent', color: active ? '#0d9488' : '#64748b', fontSize: '0.8125rem', cursor: 'pointer', fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: active ? 600 : 400, transition: 'all 150ms ease' }),
  section: { background: 'rgba(255,255,255,0.72)', backdropFilter: 'blur(14px)', border: '1px solid rgba(255,255,255,0.55)', borderRadius: '0.875rem', boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)', overflow: 'hidden' },
  table: { width: '100%', borderCollapse: 'collapse' as const, fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.8125rem' },
  th: { textAlign: 'left' as const, padding: '0.625rem 1.25rem', color: '#94a3b8', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase' as const, letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' },
  td: { padding: '0.625rem 1.25rem', color: '#334155', borderBottom: '1px solid #f1f5f9' },
};

export default function RemindersLogPage() {
  const [logs, setLogs] = useState<ReminderLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');

  const load = useCallback(async () => {
    setLoading(true);
    try { setLogs(await fetchReminderLogs()); }
    catch { /* show empty state */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Derive stats from actual data
  const delivered = logs.filter(l => l.status === 'Delivered').length;
  const failed = logs.filter(l => l.status === 'Failed').length;
  const total = logs.length;
  const successRate = total > 0 ? ((delivered / total) * 100).toFixed(1) : '—';

  const filtered = logs.filter(l => {
    const matchSearch = l.patient_name.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'All' || l.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <>
      <AdminTopBar title="Reminders Log" subtitle="Email reminder delivery history" />
      <div style={s.content}>
        <div style={s.statsStrip}>
          <div style={s.statPill}>
            <p style={s.statLabel}>Total Logs</p>
            <span style={s.statValue}>{total} sent</span>
            {failed > 0 && <span style={{ ...s.statSub, marginLeft: 8 }}>{failed} failed</span>}
          </div>
          <div style={s.statPill}>
            <p style={s.statLabel}>Delivered</p>
            <span style={s.statValue}>{delivered}</span>
          </div>
          <div style={s.statPill}>
            <p style={s.statLabel}>Success Rate</p>
            <span style={{ ...s.statValue, color: '#22c55e' }}>{successRate}{total > 0 ? '%' : ''}</span>
          </div>
        </div>

        <div style={s.toolbar}>
          <input style={s.searchInput} placeholder="Search by patient name..."
            value={search} onChange={e => setSearch(e.target.value)}
            onFocus={e => (e.target.style.borderColor = '#0d9488')}
            onBlur={e => (e.target.style.borderColor = '#e2e8f0')} />
          {filters.map(f => (
            <button key={f} style={s.filterBtn(filter === f)} onClick={() => setFilter(f)}>{f}</button>
          ))}
        </div>

        <div style={s.section}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Time</th>
                <th style={s.th}>Patient</th>
                <th style={s.th}>Medication</th>
                <th style={s.th}>Email</th>
                <th style={s.th}>Status</th>
                <th style={s.th}>Error</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>Loading...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>No logs found.</td></tr>
              ) : filtered.map(l => (
                <tr key={l.id} style={{ transition: 'background 150ms ease' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(240,253,250,0.5)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <td style={s.td}>{l.sent_at}</td>
                  <td style={s.td}>{l.patient_name}</td>
                  <td style={s.td}>{l.medication}</td>
                  <td style={{ ...s.td, fontFamily: 'monospace', fontSize: '0.75rem' }}>{l.email_masked}</td>
                  <td style={s.td}><StatusBadge status={l.status} /></td>
                  <td style={{ ...s.td, color: l.error ? '#dc2626' : '#94a3b8' }}>{l.error ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
