import { useState, useEffect, useCallback } from 'react';
import AdminTopBar from '../../components/admin/AdminTopBar';
import StatusBadge from '../../components/admin/StatusBadge';
import Modal from '../../components/admin/Modal';
import { fetchPatientCodes, revokePatientCode, PatientCode } from '../../lib/api';

const filters = ['All', 'Active', 'Used', 'Revoked'];

const s = {
  content: { padding: '0 2rem 2rem' },
  infoBanner: {
    background: '#f0fdfa', border: '1px solid #ccfbf1', borderRadius: '0.625rem',
    padding: '0.875rem 1rem', fontSize: '0.8125rem', color: '#0f766e', marginBottom: '1rem',
    display: 'flex', alignItems: 'center', gap: '0.5rem',
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  toolbar: { display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' as const, marginBottom: '1rem' },
  searchInput: { padding: '0.5rem 0.875rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none', width: 260, transition: 'border-color 150ms ease' },
  filterBtn: (active: boolean) => ({ padding: '0.375rem 0.875rem', border: active ? '1px solid #0d9488' : '1px solid #e2e8f0', borderRadius: '9999px', background: active ? '#f0fdfa' : 'transparent', color: active ? '#0d9488' : '#64748b', fontSize: '0.8125rem', cursor: 'pointer', fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: active ? 600 : 400, transition: 'all 150ms ease' }),
  primaryBtn: { padding: '0.5rem 1rem', background: '#0d9488', color: '#fff', border: 'none', borderRadius: '0.625rem', fontSize: '0.8125rem', cursor: 'pointer', fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', transition: 'background 150ms ease', marginLeft: 'auto' },
  section: { background: 'rgba(255,255,255,0.72)', backdropFilter: 'blur(14px)', border: '1px solid rgba(255,255,255,0.55)', borderRadius: '0.875rem', boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)', overflow: 'hidden' },
  table: { width: '100%', borderCollapse: 'collapse' as const, fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.8125rem' },
  th: { textAlign: 'left' as const, padding: '0.625rem 1.25rem', color: '#94a3b8', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase' as const, letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' },
  td: { padding: '0.625rem 1.25rem', color: '#334155', borderBottom: '1px solid #f1f5f9' },
  codeText: { fontFamily: 'monospace', fontSize: '0.875rem', fontWeight: 600, color: '#1e293b', letterSpacing: '0.025em' },
  iconBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 4, borderRadius: '0.375rem', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'color 150ms ease' },
  formGroup: { marginBottom: '1rem' },
  label: { display: 'block', fontSize: '0.8125rem', color: '#475569', marginBottom: 4, fontWeight: 500, fontFamily: '"DM Sans", system-ui, sans-serif' },
  input: { width: '100%', padding: '0.5rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none', boxSizing: 'border-box' as const },
  generatedCode: {
    background: '#f0fdfa', border: '1px solid #ccfbf1', borderRadius: '0.625rem',
    padding: '1.25rem', textAlign: 'center' as const, marginTop: '1rem',
  },
  bigCode: { fontFamily: 'monospace', fontSize: '1.5rem', fontWeight: 700, color: '#0d9488', letterSpacing: '0.05em' },
};

export default function ActivationCodesPage() {
  const [codes, setCodes] = useState<PatientCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');
  const [showGen, setShowGen] = useState(false);
  const [generated, setGenerated] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setCodes(await fetchPatientCodes()); }
    catch { /* show empty */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleRevoke = async (patientId: string) => {
    if (!confirm('Revoke this Patient ID? The patient will no longer be able to log in.')) return;
    try { await revokePatientCode(patientId); load(); }
    catch (e: any) { alert(e?.message); }
  };

  const filtered = codes.filter(c => {
    const matchSearch = c.patient_id.toLowerCase().includes(search.toLowerCase()) || c.patient_name.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'All' || c.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <>
      <AdminTopBar title="Activation Codes" subtitle="Manage patient activation codes" />
      <div style={s.content}>
        <div style={s.infoBanner}>
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>info</span>
          The <strong>Patient ID</strong> is the login code. After a patient completes their visit, copy their Patient ID from the system and hand it to them. They use it directly to log in to Vitalis.
        </div>

        <div style={s.toolbar}>
          <input style={s.searchInput} placeholder="Search by code or patient..."
            value={search} onChange={e => setSearch(e.target.value)}
            onFocus={e => (e.target.style.borderColor = '#0d9488')}
            onBlur={e => (e.target.style.borderColor = '#e2e8f0')} />
          {filters.map(f => (
            <button key={f} style={s.filterBtn(filter === f)} onClick={() => setFilter(f)}>{f}</button>
          ))}
          <button style={s.primaryBtn} onClick={() => { setShowGen(true); setGenerated(false); }}
            onMouseEnter={e => (e.currentTarget.style.background = '#0f766e')}
            onMouseLeave={e => (e.currentTarget.style.background = '#0d9488')}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>add</span>
            Generate Code
          </button>
        </div>

        <div style={s.section}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Patient ID (Login Code)</th>
                <th style={s.th}>Patient Name</th>
                <th style={s.th}>Issued</th>
                <th style={s.th}>Status</th>
                <th style={s.th}>First Login</th>
                <th style={s.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>Loading...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>No codes found.</td></tr>
              ) : filtered.map((c, i) => (
                <tr key={i} style={{ transition: 'background 150ms ease' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(240,253,250,0.5)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <td style={s.td}>
                    <span style={{ ...s.codeText, fontSize: '0.75rem', letterSpacing: '0.01em' }}>
                      {c.patient_id}
                    </span>
                  </td>
                  <td style={s.td}>{c.patient_name}</td>
                  <td style={s.td}>{c.issued_at}</td>
                  <td style={s.td}><StatusBadge status={c.status} /></td>
                  <td style={s.td}>{c.first_login_at ?? '—'}</td>
                  <td style={s.td}>
                    <button style={s.iconBtn} title="Copy Patient ID"
                      onClick={() => navigator.clipboard?.writeText(c.patient_id)}>
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>content_copy</span>
                    </button>
                    {c.status === 'Active' && (
                      <button style={{ ...s.iconBtn, color: '#dc2626' }} title="Revoke"
                        onClick={() => handleRevoke(c.patient_id)}>
                        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>block</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal open={showGen} onClose={() => setShowGen(false)} title="Generate Activation Code">
        {!generated ? (
          <>
            <div style={s.formGroup}>
              <label style={s.label}>Patient</label>
              <input style={s.input} placeholder="Search patient by name..." />
            </div>
            <div style={s.formGroup}>
              <label style={s.label}>Department Visited</label>
              <select style={s.input}>
                <option>Cardiology</option>
                <option>Internal Medicine</option>
                <option>Dermatology</option>
                <option>Neurology</option>
                <option>General</option>
              </select>
            </div>
            <div style={s.formGroup}>
              <label style={s.label}>Visit Date</label>
              <input style={s.input} type="date" />
            </div>
            <button style={{ ...s.primaryBtn, marginLeft: 0, width: '100%', justifyContent: 'center', marginTop: 8 }} onClick={() => setGenerated(true)}>
              Generate Code
            </button>
          </>
        ) : (
          <div style={s.generatedCode}>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', margin: '0 0 0.75rem', fontFamily: '"DM Sans", system-ui, sans-serif' }}>Activation Code Generated</p>
            <p style={s.bigCode}>VTL-2026-X9F3</p>
            <button style={{ ...s.primaryBtn, marginLeft: 0, marginTop: '1rem', justifyContent: 'center', width: '100%' }}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>content_copy</span>
              Copy Code
            </button>
          </div>
        )}
      </Modal>
    </>
  );
}
