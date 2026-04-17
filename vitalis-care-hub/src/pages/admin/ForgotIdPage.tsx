import { useState, useEffect, useCallback } from 'react';
import AdminTopBar from '../../components/admin/AdminTopBar';
import StatusBadge from '../../components/admin/StatusBadge';
import Modal from '../../components/admin/Modal';
import { fetchForgotRequests, updateForgotRequestStatus, ForgotRequest } from '../../lib/api';

const filters = ['All', 'New', 'In Progress', 'Resolved'];

const s = {
  content: { padding: '0 2rem 2rem' },
  alertBanner: {
    background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: '0.625rem',
    padding: '0.875rem 1rem', fontSize: '0.8125rem', color: '#c2410c', marginBottom: '1rem',
    display: 'flex', alignItems: 'center', gap: '0.5rem',
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  toolbar: { display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' as const, marginBottom: '1rem' },
  searchInput: {
    padding: '0.5rem 0.875rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem',
    fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif',
    outline: 'none', width: 280, transition: 'border-color 150ms ease',
  },
  filterBtn: (active: boolean) => ({
    padding: '0.375rem 0.875rem', border: active ? '1px solid #0d9488' : '1px solid #e2e8f0',
    borderRadius: '9999px', background: active ? '#f0fdfa' : 'transparent',
    color: active ? '#0d9488' : '#64748b', fontSize: '0.8125rem', cursor: 'pointer',
    fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: active ? 600 : 400,
    transition: 'all 150ms ease',
  }),
  section: {
    background: 'rgba(255,255,255,0.72)', backdropFilter: 'blur(14px)',
    border: '1px solid rgba(255,255,255,0.55)', borderRadius: '0.875rem',
    boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)', overflow: 'hidden',
  },
  table: { width: '100%', borderCollapse: 'collapse' as const, fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.8125rem' },
  th: { textAlign: 'left' as const, padding: '0.625rem 1.25rem', color: '#94a3b8', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase' as const, letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' },
  td: { padding: '0.625rem 1.25rem', color: '#334155', borderBottom: '1px solid #f1f5f9', verticalAlign: 'top' as const },
  iconBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 4, borderRadius: '0.375rem', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'color 150ms ease' },
  reqId: { fontFamily: 'monospace', fontSize: '0.75rem', color: '#94a3b8' },
  primaryBtn: { padding: '0.5rem 1rem', background: '#0d9488', color: '#fff', border: 'none', borderRadius: '0.625rem', fontSize: '0.8125rem', cursor: 'pointer', fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', transition: 'background 150ms ease' },
  detailRow: { display: 'flex', flexDirection: 'column' as const, gap: '0.25rem', marginBottom: '1rem' },
  detailLabel: { fontSize: '0.6875rem', color: '#94a3b8', textTransform: 'uppercase' as const, letterSpacing: '0.05em', fontWeight: 500, fontFamily: '"DM Sans", system-ui, sans-serif' },
  detailValue: { fontSize: '0.875rem', color: '#1e293b', fontFamily: '"DM Sans", system-ui, sans-serif' },
  notesBox: { background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '0.5rem', padding: '0.75rem', fontSize: '0.8125rem', color: '#475569', fontFamily: '"DM Sans", system-ui, sans-serif', fontStyle: 'italic' as const },
  statusSelect: { padding: '0.5rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none', width: '100%', marginTop: '0.25rem' },
  emptyCell: { textAlign: 'center' as const, padding: '3rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.875rem' },
  loadingCell: { textAlign: 'center' as const, padding: '3rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.875rem' },
};

export default function ForgotIdPage() {
  const [requests, setRequests] = useState<ForgotRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');
  const [selected, setSelected] = useState<ForgotRequest | null>(null);
  const [savingStatus, setSavingStatus] = useState(false);
  const [pendingStatus, setPendingStatus] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchForgotRequests();
      setRequests(data);
    } catch (err: any) {
      setError(err?.message ?? 'Failed to load requests');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSaveStatus = async () => {
    if (!selected || !pendingStatus) return;
    setSavingStatus(true);
    try {
      await updateForgotRequestStatus(selected.id, pendingStatus);
      setRequests(prev => prev.map(r => r.id === selected.id ? { ...r, status: pendingStatus as ForgotRequest['status'] } : r));
      setSelected(prev => prev ? { ...prev, status: pendingStatus as ForgotRequest['status'] } : null);
    } catch (err: any) {
      alert(`Failed to update status: ${err?.message}`);
    } finally {
      setSavingStatus(false);
    }
  };

  const filtered = requests.filter(r => {
    const matchSearch = r.name.toLowerCase().includes(search.toLowerCase())
      || r.id.toLowerCase().includes(search.toLowerCase())
      || r.email.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'All' || r.status === filter;
    return matchSearch && matchFilter;
  });

  const newCount = requests.filter(r => r.status === 'New').length;

  return (
    <>
      <AdminTopBar title="Forgot ID Requests" subtitle="Patients who need help recovering their Patient ID" />
      <div style={s.content}>
        {!loading && !error && newCount > 0 && (
          <div style={s.alertBanner}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>warning</span>
            <span>
              <strong>{newCount} new request{newCount > 1 ? 's' : ''}</strong> waiting for admin action.
              Please contact the patient(s) to help them recover their Patient ID.
            </span>
          </div>
        )}

        {error && (
          <div style={{ ...s.alertBanner, background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', marginBottom: '1rem' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>error</span>
            {error} —&nbsp;
            <button onClick={load} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', textDecoration: 'underline', fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.8125rem' }}>Retry</button>
          </div>
        )}

        <div style={s.toolbar}>
          <input style={s.searchInput} placeholder="Search by name, email, or request ID..."
            value={search} onChange={e => setSearch(e.target.value)}
            onFocus={e => (e.target.style.borderColor = '#0d9488')}
            onBlur={e => (e.target.style.borderColor = '#e2e8f0')} />
          {filters.map(f => (
            <button key={f} style={s.filterBtn(filter === f)} onClick={() => setFilter(f)}>
              {f}
              {f === 'New' && newCount > 0 && (
                <span style={{ marginLeft: 4, background: '#c2410c', color: '#fff', borderRadius: '9999px', fontSize: '0.625rem', padding: '0 5px', fontWeight: 700 }}>
                  {newCount}
                </span>
              )}
            </button>
          ))}
          <button style={{ ...s.primaryBtn, marginLeft: 'auto' }} onClick={load}
            onMouseEnter={e => (e.currentTarget.style.background = '#0f766e')}
            onMouseLeave={e => (e.currentTarget.style.background = '#0d9488')}>
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>refresh</span>
            Refresh
          </button>
        </div>

        <div style={s.section}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Request ID</th>
                <th style={s.th}>Patient Name</th>
                <th style={s.th}>Contact</th>
                <th style={s.th}>Visit Date</th>
                <th style={s.th}>Department</th>
                <th style={s.th}>Submitted</th>
                <th style={s.th}>Status</th>
                <th style={s.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} style={s.loadingCell}>
                  <span className="material-symbols-outlined" style={{ fontSize: 24, display: 'block', margin: '0 auto 0.5rem' }}>hourglass_empty</span>
                  Loading requests...
                </td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={8} style={s.emptyCell}>
                  <span className="material-symbols-outlined" style={{ fontSize: 36, display: 'block', margin: '0 auto 0.5rem', color: '#cbd5e1' }}>inbox</span>
                  {error ? 'Could not load data.' : 'No requests found.'}
                </td></tr>
              ) : filtered.map(r => (
                <tr key={r.id}
                  style={{ transition: 'background 150ms ease', cursor: 'pointer' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(240,253,250,0.5)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  onClick={() => { setSelected(r); setPendingStatus(r.status); }}>
                  <td style={s.td}><span style={s.reqId}>{r.id}</span></td>
                  <td style={s.td}>
                    <strong style={{ fontWeight: 600 }}>{r.name}</strong>
                    {r.status === 'New' && (
                      <span style={{ marginLeft: 6, background: '#fff7ed', color: '#c2410c', borderRadius: '9999px', fontSize: '0.625rem', padding: '1px 6px', fontWeight: 700, verticalAlign: 'middle' }}>NEW</span>
                    )}
                  </td>
                  <td style={s.td}>
                    <div style={{ fontSize: '0.8125rem' }}>{r.phone}</div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{r.email}</div>
                  </td>
                  <td style={s.td}>{r.visit_date}</td>
                  <td style={s.td}>{r.department}</td>
                  <td style={{ ...s.td, fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'nowrap' }}>{r.submitted_at}</td>
                  <td style={s.td}><StatusBadge status={r.status} /></td>
                  <td style={s.td} onClick={e => e.stopPropagation()}>
                    <button style={s.iconBtn} title="View details"
                      onClick={() => { setSelected(r); setPendingStatus(r.status); }}
                      onMouseEnter={e => (e.currentTarget.style.color = '#0d9488')}
                      onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}>
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>open_in_new</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal open={!!selected} onClose={() => setSelected(null)} title={`Request ${selected?.id ?? ''} — ${selected?.name ?? ''}`}>
        {selected && (
          <>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, fontFamily: '"DM Sans", system-ui, sans-serif', marginBottom: '0.75rem' }}>
              Information provided by patient
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem 1.5rem', marginBottom: '1rem' }}>
              <div style={s.detailRow}><span style={s.detailLabel}>Full Name</span><span style={s.detailValue}>{selected.name}</span></div>
              <div style={s.detailRow}><span style={s.detailLabel}>Date of Birth</span><span style={s.detailValue}>{selected.dob}</span></div>
              <div style={s.detailRow}><span style={s.detailLabel}>Phone</span><span style={s.detailValue}>{selected.phone}</span></div>
              <div style={s.detailRow}><span style={s.detailLabel}>Email</span><span style={s.detailValue}>{selected.email}</span></div>
              <div style={s.detailRow}><span style={s.detailLabel}>Approximate Visit Date</span><span style={s.detailValue}>{selected.visit_date}</span></div>
              <div style={s.detailRow}><span style={s.detailLabel}>Department Visited</span><span style={s.detailValue}>{selected.department}</span></div>
            </div>
            {selected.notes && (
              <div style={{ marginBottom: '1.25rem' }}>
                <span style={s.detailLabel}>Additional Notes</span>
                <div style={{ ...s.notesBox, marginTop: 4 }}>{selected.notes}</div>
              </div>
            )}
            <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '1rem 0' }} />
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, fontFamily: '"DM Sans", system-ui, sans-serif', marginBottom: '0.75rem' }}>Admin action</p>
            <p style={{ fontSize: '0.8125rem', color: '#475569', fontFamily: '"DM Sans", system-ui, sans-serif', marginBottom: '1rem', lineHeight: 1.6 }}>
              Look up this patient in the <strong>Patients</strong> tab, retrieve their Patient ID, and contact them via phone or email.
            </p>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ ...s.detailLabel, display: 'block', marginBottom: 4 }}>Update Status</label>
              <select style={s.statusSelect} value={pendingStatus} onChange={e => setPendingStatus(e.target.value)}>
                <option value="New">New</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                style={{ ...s.primaryBtn, flex: 1, justifyContent: 'center', opacity: savingStatus ? 0.7 : 1 }}
                onClick={handleSaveStatus}
                disabled={savingStatus}
                onMouseEnter={e => (e.currentTarget.style.background = '#0f766e')}
                onMouseLeave={e => (e.currentTarget.style.background = '#0d9488')}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{savingStatus ? 'hourglass_empty' : 'save'}</span>
                {savingStatus ? 'Saving...' : 'Save Status'}
              </button>
              <button style={{ ...s.primaryBtn, flex: 1, justifyContent: 'center', background: '#f0fdfa', color: '#0d9488', border: '1px solid #ccfbf1' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>group</span>
                Go to Patients
              </button>
            </div>
          </>
        )}
      </Modal>
    </>
  );
}
