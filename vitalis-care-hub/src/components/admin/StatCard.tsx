interface StatCardProps {
  icon: string;
  value: string | number;
  label: string;
  trend?: string;
}

const s = {
  card: {
    background: 'rgba(255,255,255,0.72)',
    backdropFilter: 'blur(14px)',
    border: '1px solid rgba(255,255,255,0.55)',
    borderRadius: '0.875rem',
    padding: '1.25rem',
    boxShadow: '0 4px 24px -4px rgba(15,23,42,0.08)',
    flex: 1,
    minWidth: 180,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '0.75rem',
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: '9999px',
    background: '#f0fdfa',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#0d9488',
  },
  trend: {
    fontSize: '0.75rem',
    color: '#22c55e',
    fontWeight: 600,
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  value: {
    fontSize: '1.75rem',
    fontWeight: 700,
    color: '#1e293b',
    fontFamily: '"DM Sans", system-ui, sans-serif',
    margin: 0,
    lineHeight: 1.2,
  },
  label: {
    fontSize: '0.8125rem',
    color: '#94a3b8',
    marginTop: 2,
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
};

export default function StatCard({ icon, value, label, trend }: StatCardProps) {
  return (
    <div style={s.card}>
      <div style={s.header}>
        <div style={s.iconWrap}>
          <span className="material-symbols-outlined" style={{ fontSize: 22 }}>{icon}</span>
        </div>
        {trend && <span style={s.trend}>{trend}</span>}
      </div>
      <p style={s.value}>{value}</p>
      <p style={s.label}>{label}</p>
    </div>
  );
}
