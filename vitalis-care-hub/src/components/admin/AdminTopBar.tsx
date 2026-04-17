import { ReactNode } from 'react';

interface AdminTopBarProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

const s = {
  bar: {
    padding: '1.5rem 2rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  titleGroup: {},
  title: {
    fontFamily: '"DM Serif Display", Georgia, serif',
    fontSize: '1.5rem',
    color: '#1e293b',
    margin: 0,
  },
  subtitle: {
    fontSize: '0.8125rem',
    color: '#94a3b8',
    marginTop: 2,
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  actions: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
  },
};

export default function AdminTopBar({ title, subtitle, actions }: AdminTopBarProps) {
  return (
    <div style={s.bar}>
      <div style={s.titleGroup}>
        <h1 style={s.title}>{title}</h1>
        {subtitle && <p style={s.subtitle}>{subtitle}</p>}
      </div>
      {actions && <div style={s.actions}>{actions}</div>}
    </div>
  );
}
