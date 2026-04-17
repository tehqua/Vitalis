import { useState } from 'react';

interface AdminLoginProps {
  onLogin: (token: string) => void;
}

const s = {
  page: {
    minHeight: '100vh',
    background: 'radial-gradient(ellipse at 0% 0%, #ecfdf5 0%, #f8fafc 50%, #eff6ff 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  card: {
    background: 'rgba(255,255,255,0.85)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255,255,255,0.6)',
    borderRadius: '1.25rem',
    boxShadow: '0 8px 40px -8px rgba(15,23,42,0.12)',
    padding: '2.5rem',
    width: '100%',
    maxWidth: 400,
  },
  logoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '2rem',
  },
  logoIcon: {
    width: 44,
    height: 44,
    borderRadius: '0.75rem',
    background: '#0d9488',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontSize: 24,
  },
  logoText: {
    fontFamily: '"DM Serif Display", Georgia, serif',
    fontSize: '1.25rem',
    color: '#1e293b',
  },
  title: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1e293b',
    marginBottom: '0.25rem',
  },
  subtitle: {
    fontSize: '0.8125rem',
    color: '#94a3b8',
    marginBottom: '1.5rem',
  },
  label: {
    display: 'block',
    fontSize: '0.8125rem',
    color: '#475569',
    fontWeight: 500,
    marginBottom: '0.375rem',
  },
  input: {
    width: '100%',
    padding: '0.625rem 0.875rem',
    border: '1.5px solid #e2e8f0',
    borderRadius: '0.625rem',
    fontSize: '0.875rem',
    fontFamily: '"DM Sans", system-ui, sans-serif',
    outline: 'none',
    boxSizing: 'border-box' as const,
    transition: 'border-color 150ms ease',
    letterSpacing: '0.05em',
  },
  btn: {
    width: '100%',
    padding: '0.75rem',
    background: '#0d9488',
    color: '#fff',
    border: 'none',
    borderRadius: '0.625rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontFamily: '"DM Sans", system-ui, sans-serif',
    marginTop: '1.25rem',
    transition: 'background 150ms ease',
  },
  error: {
    background: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '0.5rem',
    padding: '0.625rem 0.875rem',
    fontSize: '0.8125rem',
    color: '#dc2626',
    marginTop: '0.875rem',
  },
  hint: {
    fontSize: '0.75rem',
    color: '#94a3b8',
    marginTop: '1rem',
    textAlign: 'center' as const,
    lineHeight: 1.6,
  },
};

export default function AdminLogin({ onLogin }: AdminLoginProps) {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim()) {
      setError('Please enter the Admin Secret Key.');
      return;
    }
    setLoading(true);
    setError('');

    // Verify token against backend
    try {
      const apiBase = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';
      const res = await fetch(`${apiBase}/api/admin/stats`, {
        headers: { Authorization: `Bearer ${key.trim()}` },
      });
      if (res.ok) {
        sessionStorage.setItem('admin_token', key.trim());
        onLogin(key.trim());
      } else if (res.status === 403 || res.status === 401) {
        setError('Incorrect Admin Secret Key. Please check backend/.env → ADMIN_SECRET_KEY.');
      } else {
        setError(`Backend returned ${res.status}. Make sure the backend server is running.`);
      }
    } catch {
      setError('Cannot reach backend at http://localhost:8000. Is the server running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logoRow}>
          <div style={s.logoIcon}>
            <span className="material-symbols-outlined" style={{ fontSize: 24 }}>health_and_safety</span>
          </div>
          <span style={s.logoText}>Vitalis Admin</span>
        </div>

        <p style={s.title}>Admin Access</p>
        <p style={s.subtitle}>Enter your Admin Secret Key to continue.</p>

        <form onSubmit={handleSubmit}>
          <label style={s.label} htmlFor="admin-key">Admin Secret Key</label>
          <input
            id="admin-key"
            type="password"
            style={s.input}
            placeholder="Paste key from backend/.env"
            value={key}
            onChange={e => setKey(e.target.value)}
            onFocus={e => (e.target.style.borderColor = '#0d9488')}
            onBlur={e => (e.target.style.borderColor = '#e2e8f0')}
            autoComplete="off"
          />
          <button
            type="submit"
            style={{ ...s.btn, opacity: loading ? 0.7 : 1 }}
            disabled={loading}
            onMouseEnter={e => (e.currentTarget.style.background = '#0f766e')}
            onMouseLeave={e => (e.currentTarget.style.background = '#0d9488')}
          >
            {loading ? 'Verifying...' : 'Sign in to Admin Panel'}
          </button>
        </form>

        {error && <div style={s.error}>{error}</div>}

        <p style={s.hint}>
          Key is set in <code style={{ background: '#f1f5f9', padding: '1px 4px', borderRadius: 3 }}>backend/.env</code> →{' '}
          <code style={{ background: '#f1f5f9', padding: '1px 4px', borderRadius: 3 }}>ADMIN_SECRET_KEY</code>
        </p>
      </div>
    </div>
  );
}
