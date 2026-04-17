type BadgeVariant = 'active' | 'pending' | 'inactive' | 'failed' | 'delivered' | 'used'
  | 'revoked' | 'paused' | 'completed' | 'new' | 'in progress' | 'resolved';

const colorMap: Record<BadgeVariant, { bg: string; color: string }> = {
  active:    { bg: '#f0fdfa', color: '#0d9488' },
  delivered: { bg: '#f0fdfa', color: '#0d9488' },
  used:      { bg: '#f0fdfa', color: '#0d9488' },
  resolved:  { bg: '#f0fdfa', color: '#0d9488' },
  completed: { bg: '#f1f5f9', color: '#64748b' },
  pending:   { bg: '#fffbeb', color: '#d97706' },
  paused:    { bg: '#fffbeb', color: '#d97706' },
  'in progress': { bg: '#fffbeb', color: '#d97706' },
  new:       { bg: '#fff7ed', color: '#c2410c' },
  inactive:  { bg: '#f1f5f9', color: '#64748b' },
  revoked:   { bg: '#f1f5f9', color: '#64748b' },
  failed:    { bg: '#fef2f2', color: '#dc2626' },
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const key = status.toLowerCase() as BadgeVariant;
  const colors = colorMap[key] || colorMap.inactive;
  return (
    <span style={{
      display: 'inline-block',
      padding: '0.1875rem 0.625rem',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: 600,
      background: colors.bg,
      color: colors.color,
      fontFamily: '"DM Sans", system-ui, sans-serif',
      textTransform: 'capitalize',
    }}>
      {status}
    </span>
  );
}
