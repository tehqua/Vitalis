import { useState, useEffect, useCallback } from 'react';
import AdminTopBar from '../../components/admin/AdminTopBar';
import StatusBadge from '../../components/admin/StatusBadge';
import Modal from '../../components/admin/Modal';
import { fetchPatients, Patient } from '../../lib/api';

const filters = ['All', 'Active', 'Pending', 'Inactive'];

const s = {
  content: { padding: '0 2rem 2rem' },
  toolbar: {
    display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' as const, marginBottom: '1rem',
  },
  searchInput: {
    padding: '0.5rem 0.875rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem',
    fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none',
    width: 260, transition: 'border-color 150ms ease',
  },
  filterBtn: (active: boolean) => ({
    padding: '0.375rem 0.875rem', border: active ? '1px solid #0d9488' : '1px solid #e2e8f0',
    borderRadius: '9999px', background: active ? '#f0fdfa' : 'transparent',
    color: active ? '#0d9488' : '#64748b', fontSize: '0.8125rem', cursor: 'pointer',
    fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: active ? 600 : 400,
    transition: 'all 150ms ease',
  }),
  primaryBtn: {
    padding: '0.5rem 1rem', background: '#0d9488', color: '#fff', border: 'none',
    borderRadius: '0.625rem', fontSize: '0.8125rem', cursor: 'pointer',
    fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: 600, display: 'flex',
    alignItems: 'center', gap: '0.375rem', transition: 'background 150ms ease',
    marginLeft: 'auto',
  },
  section: {
    background: 'rgba(255,255,255,0.72)', backdropFilter: 'blur(14px)',
    border: '1px solid rgba(255,255,255,0.55)', borderRadius: '0.875rem',
    boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)', overflow: 'hidden',
  },
  table: { width: '100%', borderCollapse: 'collapse' as const, fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.8125rem' },
  th: { textAlign: 'left' as const, padding: '0.625rem 1.25rem', color: '#94a3b8', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase' as const, letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' },
  td: { padding: '0.625rem 1.25rem', color: '#334155', borderBottom: '1px solid #f1f5f9' },
  avatar: {
    width: 32, height: 32, borderRadius: '9999px', background: '#0d9488', color: '#fff',
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6875rem',
    fontWeight: 600, marginRight: 8, verticalAlign: 'middle', fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  patientId: { fontSize: '0.6875rem', color: '#94a3b8', fontFamily: 'monospace' },
  iconBtn: {
    background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 4,
    borderRadius: '0.375rem', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    transition: 'color 150ms ease',
  },
  // Drawer styles
  drawerOverlay: {
    position: 'fixed' as const, inset: 0, background: 'rgba(15,23,42,0.3)', zIndex: 90,
  },
  drawer: {
    position: 'fixed' as const, top: 0, right: 0, width: 400, height: '100vh',
    background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(14px)',
    boxShadow: '-4px 0 24px rgba(15,23,42,0.1)', zIndex: 91, padding: '1.5rem',
    overflow: 'auto', transition: 'transform 300ms ease',
  },
  drawerTitle: { fontFamily: '"DM Serif Display", Georgia, serif', fontSize: '1.25rem', color: '#1e293b', marginBottom: 4 },
  drawerSub: { fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace', marginBottom: '1.5rem' },
  drawerSection: { marginBottom: '1.25rem' },
  drawerSectionTitle: { fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' as const, letterSpacing: '0.05em', marginBottom: '0.5rem', fontWeight: 500, fontFamily: '"DM Sans", system-ui, sans-serif' },
  formGroup: { marginBottom: '1rem' },
  label: { display: 'block', fontSize: '0.8125rem', color: '#475569', marginBottom: 4, fontWeight: 500, fontFamily: '"DM Sans", system-ui, sans-serif' },
  input: { width: '100%', padding: '0.5rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none', boxSizing: 'border-box' as const },
};

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [showAdd, setShowAdd] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setPatients(await fetchPatients()); }
    catch { /* show empty */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = patients.filter(p => {
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || p.id.includes(search.toLowerCase());
    const matchFilter = filter === 'All' || p.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <>
      <AdminTopBar title="Patients" subtitle={loading ? 'Loading...' : `${patients.length} total patients`} />
      <div style={s.content}>
        <div style={s.toolbar}>
          <input style={s.searchInput} placeholder="Search by name or patient ID..."
            value={search} onChange={e => setSearch(e.target.value)}
            onFocus={e => (e.target.style.borderColor = '#0d9488')}
            onBlur={e => (e.target.style.borderColor = '#e2e8f0')} />
          {filters.map(f => (
            <button key={f} style={s.filterBtn(filter === f)} onClick={() => setFilter(f)}>{f}</button>
          ))}
          <button style={s.primaryBtn} onClick={() => setShowAdd(true)}
            onMouseEnter={e => (e.currentTarget.style.background = '#0f766e')}
            onMouseLeave={e => (e.currentTarget.style.background = '#0d9488')}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>add</span>
            Add Patient
          </button>
        </div>

        <div style={s.section}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Patient</th>
                <th style={s.th}>Status</th>
                <th style={s.th}>Consented</th>
                <th style={s.th}>Last Session</th>
                <th style={s.th}>Sessions</th>
                <th style={s.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>Loading...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>No patients found.</td></tr>
              ) : filtered.map(p => (
                <tr key={p.id} style={{ transition: 'background 150ms ease', cursor: 'pointer' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(240,253,250,0.5)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  onClick={() => setSelectedPatient(p)}>
                  <td style={s.td}>
                    <span style={s.avatar}>{p.name.split(' ').map(n => n[0]).join('')}</span>
                    <span>{p.name}</span>
                    <br /><span style={s.patientId}>{p.id}</span>
                  </td>
                  <td style={s.td}><StatusBadge status={p.status} /></td>
                  <td style={s.td}>{p.consented ? <span style={{ color: '#22c55e' }}>✅ {p.consentDate}</span> : <span style={{ color: '#dc2626' }}>❌ No</span>}</td>
                  <td style={s.td}>{p.lastSession}</td>
                  <td style={s.td}>{p.sessions}</td>
                  <td style={s.td} onClick={e => e.stopPropagation()}>
                    <button style={s.iconBtn} title="View"><span className="material-symbols-outlined" style={{ fontSize: 18 }}>visibility</span></button>
                    <button style={s.iconBtn} title="Generate code"><span className="material-symbols-outlined" style={{ fontSize: 18 }}>key</span></button>
                    <button style={s.iconBtn} title="More"><span className="material-symbols-outlined" style={{ fontSize: 18 }}>more_vert</span></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Patient Drawer */}
      {selectedPatient && (
        <>
          <div style={s.drawerOverlay} onClick={() => setSelectedPatient(null)} />
          <div style={s.drawer}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={s.drawerTitle}>{selectedPatient.name}</h2>
                <p style={s.drawerSub}>{selectedPatient.id}</p>
              </div>
              <button style={s.iconBtn} onClick={() => setSelectedPatient(null)}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div style={s.drawerSection}>
              <p style={s.drawerSectionTitle}>Status</p>
              <StatusBadge status={selectedPatient.status} />
            </div>
            <div style={s.drawerSection}>
              <p style={s.drawerSectionTitle}>Consent</p>
              <p style={{ fontSize: '0.875rem', color: '#334155', margin: 0 }}>
                {selectedPatient.consented ? `Consented on ${selectedPatient.consentDate}` : 'Not yet consented'}
              </p>
            </div>
            <div style={s.drawerSection}>
              <p style={s.drawerSectionTitle}>Recent Sessions</p>
              {selectedPatient.sessions > 0 ? (
                <p style={{ fontSize: '0.875rem', color: '#334155', margin: 0 }}>{selectedPatient.sessions} sessions — last {selectedPatient.lastSession}</p>
              ) : (
                <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>No sessions yet</p>
              )}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
              <button style={{ ...s.primaryBtn, marginLeft: 0, flex: 1, justifyContent: 'center' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>key</span>
                Create Activation Code
              </button>
              <button style={{ ...s.primaryBtn, marginLeft: 0, flex: 1, justifyContent: 'center', background: '#f0fdfa', color: '#0d9488' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>medication</span>
                Schedule Medication
              </button>
            </div>
          </div>
        </>
      )}

      {/* Add Patient Modal */}
      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add New Patient">
        <div style={s.formGroup}>
          <label style={s.label}>Full Name</label>
          <input style={s.input} placeholder="e.g. Nguyen Van A" />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Email</label>
          <input style={s.input} type="email" placeholder="patient@email.com" />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Phone</label>
          <input style={s.input} placeholder="+84..." />
        </div>
        <button style={{ ...s.primaryBtn, marginLeft: 0, width: '100%', justifyContent: 'center', marginTop: 8 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 16 }}>add</span>
          Add Patient
        </button>
      </Modal>
    </>
  );
}
