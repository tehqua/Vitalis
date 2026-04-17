import { ReactNode } from 'react';
import AdminSidebar from './AdminSidebar';

interface AdminLayoutProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  children: ReactNode;
  newForgotCount?: number;
  onLogout?: () => void;
}

const s = {
  wrapper: {
    display: 'flex',
    minHeight: '100vh',
    background: 'radial-gradient(ellipse at 0% 0%, #ecfdf5 0%, #f8fafc 50%, #eff6ff 100%)',
    fontFamily: '"DM Sans", system-ui, sans-serif',
  },
  main: {
    flex: 1,
    marginLeft: 240,
    minHeight: '100vh',
    overflow: 'auto' as const,
  },
};

export default function AdminLayout({ activeTab, onTabChange, children, newForgotCount = 0, onLogout }: AdminLayoutProps) {
  return (
    <div style={s.wrapper}>
      <AdminSidebar activeTab={activeTab} onTabChange={onTabChange} newForgotCount={newForgotCount} onLogout={onLogout} />
      <main style={s.main}>{children}</main>
    </div>
  );
}
