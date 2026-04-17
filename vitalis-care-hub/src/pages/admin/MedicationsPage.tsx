import { useState, useEffect, useCallback } from 'react';
import AdminTopBar from '../../components/admin/AdminTopBar';
import StatusBadge from '../../components/admin/StatusBadge';
import Modal from '../../components/admin/Modal';
import { fetchMedications, deleteMedication, updateMedicationStatus, MedicationSchedule } from '../../lib/api';

const filters = ['All', 'Active', 'Completed', 'Paused'];
const frequencies = ['Once daily', 'Twice daily', 'Three times daily', 'Weekly', 'Custom'];

const s = {
  content: { padding: '0 2rem 2rem' },
  toolbar: { display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' as const, marginBottom: '1rem' },
  searchInput: { padding: '0.5rem 0.875rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none', width: 280, transition: 'border-color 150ms ease' },
  filterBtn: (active: boolean) => ({ padding: '0.375rem 0.875rem', border: active ? '1px solid #0d9488' : '1px solid #e2e8f0', borderRadius: '9999px', background: active ? '#f0fdfa' : 'transparent', color: active ? '#0d9488' : '#64748b', fontSize: '0.8125rem', cursor: 'pointer', fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: active ? 600 : 400, transition: 'all 150ms ease' }),
  primaryBtn: { padding: '0.5rem 1rem', background: '#0d9488', color: '#fff', border: 'none', borderRadius: '0.625rem', fontSize: '0.8125rem', cursor: 'pointer', fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', transition: 'background 150ms ease', marginLeft: 'auto' },
  section: { background: 'rgba(255,255,255,0.72)', backdropFilter: 'blur(14px)', border: '1px solid rgba(255,255,255,0.55)', borderRadius: '0.875rem', boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)', overflow: 'hidden' },
  table: { width: '100%', borderCollapse: 'collapse' as const, fontFamily: '"DM Sans", system-ui, sans-serif', fontSize: '0.8125rem' },
  th: { textAlign: 'left' as const, padding: '0.625rem 1rem', color: '#94a3b8', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase' as const, letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' },
  td: { padding: '0.625rem 1rem', color: '#334155', borderBottom: '1px solid #f1f5f9' },
  avatar: { width: 28, height: 28, borderRadius: '9999px', background: '#0d9488', color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.625rem', fontWeight: 600, marginRight: 6, verticalAlign: 'middle', fontFamily: '"DM Sans", system-ui, sans-serif' },
  iconBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 4, borderRadius: '0.375rem', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'color 150ms ease' },
  progress: { background: '#e2e8f0', borderRadius: '9999px', height: 4, width: 60, display: 'inline-block', verticalAlign: 'middle', marginLeft: 6 },
  formGroup: { marginBottom: '1rem' },
  label: { display: 'block', fontSize: '0.8125rem', color: '#475569', marginBottom: 4, fontWeight: 500, fontFamily: '"DM Sans", system-ui, sans-serif' },
  input: { width: '100%', padding: '0.5rem 0.75rem', border: '1px solid #e2e8f0', borderRadius: '0.625rem', fontSize: '0.8125rem', fontFamily: '"DM Sans", system-ui, sans-serif', outline: 'none', boxSizing: 'border-box' as const },
  radioGroup: { display: 'flex', gap: '0.5rem', flexWrap: 'wrap' as const },
  radioBtn: (active: boolean) => ({ padding: '0.375rem 0.75rem', border: active ? '1px solid #0d9488' : '1px solid #e2e8f0', borderRadius: '9999px', background: active ? '#f0fdfa' : '#fff', color: active ? '#0d9488' : '#64748b', fontSize: '0.8125rem', cursor: 'pointer', fontFamily: '"DM Sans", system-ui, sans-serif', fontWeight: active ? 600 : 400 }),
};

export default function MedicationsPage() {
  const [meds, setMeds] = useState<MedicationSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');
  const [showNew, setShowNew] = useState(false);
  const [freq, setFreq] = useState('Once daily');

  const load = useCallback(async () => {
    setLoading(true);
    try { setMeds(await fetchMedications()); }
    catch { /* show empty state */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this schedule?')) return;
    try { await deleteMedication(id); load(); }
    catch (e: any) { alert(e?.message); }
  };

  const handlePause = async (m: MedicationSchedule) => {
    const next = m.status === 'Paused' ? 'Active' : 'Paused';
    try { await updateMedicationStatus(m.id, next); load(); }
    catch (e: any) { alert(e?.message); }
  };

  const filtered = meds.filter(m => {
    const matchSearch = m.patient_name.toLowerCase().includes(search.toLowerCase()) || m.medication.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'All' || m.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <>
      <AdminTopBar title="Medications" subtitle="Manage medication reminder schedules" />
      <div style={s.content}>
        <div style={s.toolbar}>
          <input style={s.searchInput} placeholder="Search by patient or medication..."
            value={search} onChange={e => setSearch(e.target.value)}
            onFocus={e => (e.target.style.borderColor = '#0d9488')}
            onBlur={e => (e.target.style.borderColor = '#e2e8f0')} />
          {filters.map(f => (
            <button key={f} style={s.filterBtn(filter === f)} onClick={() => setFilter(f)}>{f}</button>
          ))}
          <button style={s.primaryBtn} onClick={() => setShowNew(true)}
            onMouseEnter={e => (e.currentTarget.style.background = '#0f766e')}
            onMouseLeave={e => (e.currentTarget.style.background = '#0d9488')}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>add</span>
            New Schedule
          </button>
        </div>

        <div style={s.section}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Patient</th>
                <th style={s.th}>Medication</th>
                <th style={s.th}>Frequency</th>
                <th style={s.th}>Times</th>
                <th style={s.th}>Period</th>
                <th style={s.th}>Reminders</th>
                <th style={s.th}>Status</th>
                <th style={s.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>Loading...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontFamily: '"DM Sans", system-ui, sans-serif' }}>No schedules found.</td></tr>
              ) : filtered.map(m => (
                <tr key={m.id} style={{ transition: 'background 150ms ease' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(240,253,250,0.5)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <td style={s.td}>
                    <span style={s.avatar}>{m.patient_name.split(' ').map(n => n[0]).join('')}</span>
                    {m.patient_name}
                  </td>
                  <td style={{ ...s.td, fontWeight: 500 }}>{m.medication} {m.dosage}</td>
                  <td style={s.td}>{m.frequency}</td>
                  <td style={s.td}>{m.times.join(', ')}</td>
                  <td style={s.td}>{m.start_date}{m.end_date ? ` → ${m.end_date}` : ''}</td>
                  <td style={s.td}>
                    {m.reminders_sent}/{m.reminders_total}
                    <span style={s.progress}>
                      <span style={{ display: 'block', height: '100%', borderRadius: '9999px', background: '#0d9488', width: `${m.reminders_total ? (m.reminders_sent / m.reminders_total) * 100 : 0}%` }} />
                    </span>
                  </td>
                  <td style={s.td}><StatusBadge status={m.status} /></td>
                  <td style={s.td}>
                    <button style={s.iconBtn} title="Edit"><span className="material-symbols-outlined" style={{ fontSize: 18 }}>edit</span></button>
                    <button style={s.iconBtn} title={m.status === 'Paused' ? 'Resume' : 'Pause'} onClick={() => handlePause(m)}><span className="material-symbols-outlined" style={{ fontSize: 18 }}>{m.status === 'Paused' ? 'play_circle' : 'pause_circle'}</span></button>
                    <button style={{ ...s.iconBtn, color: '#dc2626' }} title="Delete" onClick={() => handleDelete(m.id)}><span className="material-symbols-outlined" style={{ fontSize: 18 }}>delete</span></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal open={showNew} onClose={() => setShowNew(false)} title="New Medication Schedule">
        <div style={s.formGroup}>
          <label style={s.label}>Patient</label>
          <input style={s.input} placeholder="Search patient..." />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Medication Name</label>
          <input style={s.input} placeholder="e.g. Metformin" />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Dosage</label>
          <input style={s.input} placeholder="e.g. 500mg" />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Frequency</label>
          <div style={s.radioGroup}>
            {frequencies.map(f => (
              <button key={f} style={s.radioBtn(freq === f)} onClick={() => setFreq(f)}>{f}</button>
            ))}
          </div>
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Reminder Time(s)</label>
          <input style={s.input} type="time" defaultValue="08:00" />
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <div style={{ ...s.formGroup, flex: 1 }}>
            <label style={s.label}>Start Date</label>
            <input style={s.input} type="date" />
          </div>
          <div style={{ ...s.formGroup, flex: 1 }}>
            <label style={s.label}>End Date</label>
            <input style={s.input} type="date" />
          </div>
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Patient Email</label>
          <input style={s.input} type="email" placeholder="patient@email.com" />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>Notes (optional)</label>
          <textarea style={{ ...s.input, minHeight: 60, resize: 'vertical' as const }} placeholder="Additional instructions..." />
        </div>
        <button style={{ ...s.primaryBtn, marginLeft: 0, width: '100%', justifyContent: 'center', marginTop: 8 }}
          onMouseEnter={e => (e.currentTarget.style.background = '#0f766e')}
          onMouseLeave={e => (e.currentTarget.style.background = '#0d9488')}>
          Create Schedule
        </button>
      </Modal>
    </>
  );
}
