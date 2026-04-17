import { useState, useEffect } from 'react';
import AdminLayout from '../components/admin/AdminLayout';
import AdminLogin from '../components/admin/AdminLogin';
import OverviewPage from './admin/OverviewPage';
import PatientsPage from './admin/PatientsPage';
import ActivationCodesPage from './admin/ActivationCodesPage';
import MedicationsPage from './admin/MedicationsPage';
import RemindersLogPage from './admin/RemindersLogPage';
import ForgotIdPage from './admin/ForgotIdPage';

const pages: Record<string, () => JSX.Element> = {
  'overview': OverviewPage,
  'patients': PatientsPage,
  'activation-codes': ActivationCodesPage,
  'medications': MedicationsPage,
  'reminders-log': RemindersLogPage,
  'forgot-id': ForgotIdPage,
};

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [token, setToken] = useState<string | null>(null);
  const [newForgotCount, setNewForgotCount] = useState(0);

  // On mount, restore session
  useEffect(() => {
    const saved = sessionStorage.getItem('admin_token');
    if (saved) setToken(saved);
  }, []);

  // Poll for new forgot-id requests count every 30s
  useEffect(() => {
    if (!token) return;

    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

    const fetchCount = async () => {
      try {
        const res = await fetch(`${apiBase}/api/admin/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setNewForgotCount(data.new_forgot_requests ?? 0);
        }
      } catch { /* silent */ }
    };

    fetchCount();
    const interval = setInterval(fetchCount, 30_000);
    return () => clearInterval(interval);
  }, [token]);

  const handleLogin = (tok: string) => setToken(tok);

  const handleLogout = () => {
    sessionStorage.removeItem('admin_token');
    setToken(null);
  };

  if (!token) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  const PageComponent = pages[activeTab] || OverviewPage;

  return (
    <AdminLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      newForgotCount={newForgotCount}
      onLogout={handleLogout}
    >
      <PageComponent />
    </AdminLayout>
  );
}
