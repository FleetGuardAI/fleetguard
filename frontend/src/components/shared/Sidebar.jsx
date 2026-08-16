import { useState, useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Truck, Users, Route, Fuel, Receipt, Bell, Settings,
  LogOut, CreditCard, Wrench, FileText, AlertTriangle, BarChart3, User,
  Cpu, MessageSquare, X, QrCode
} from 'lucide-react';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';
import { getInitials } from '@/utils/formatters';
import { useLanguage } from '@/i18n/LanguageContext';
import { logout } from '@/api/authApi';

const SIDEBAR_WIDTH = 240;

const iconMap = {
  LayoutDashboard: <LayoutDashboard className="h-[18px] w-[18px]" />,
  MessageSquare: <MessageSquare className="h-[18px] w-[18px]" />,
  BarChart3: <BarChart3 className="h-[18px] w-[18px]" />,
  Truck: <Truck className="h-[18px] w-[18px]" />,
  Users: <Users className="h-[18px] w-[18px]" />,
  Cpu: <Cpu className="h-[18px] w-[18px]" />,
  Route: <Route className="h-[18px] w-[18px]" />,
  Fuel: <Fuel className="h-[18px] w-[18px]" />,
  Receipt: <Receipt className="h-[18px] w-[18px]" />,
  CreditCard: <CreditCard className="h-[18px] w-[18px]" />,
  Wrench: <Wrench className="h-[18px] w-[18px]" />,
  FileText: <FileText className="h-[18px] w-[18px]" />,
  AlertTriangle: <AlertTriangle className="h-[18px] w-[18px]" />,
  Bell: <Bell className="h-[18px] w-[18px]" />,
  User: <User className="h-[18px] w-[18px]" />,
  Settings: <Settings className="h-[18px] w-[18px]" />,
  QrCode: <QrCode className="h-[18px] w-[18px]" />,
};

const navSections = [
  {
    section: 'OVERVIEW',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: 'LayoutDashboard' },
      { label: 'Reports & Analytics', path: '/dashboard/reports', icon: 'BarChart3' },
    ],
  },
  {
    section: 'FLEET',
    items: [
      { label: 'Vehicles', path: '/dashboard/vehicles', icon: 'Truck' },
      { label: 'Drivers', path: '/dashboard/drivers', icon: 'Users' },
      { label: 'Hardware Assets', path: '/dashboard/assets', icon: 'Cpu' },
      { label: 'Documents', path: '/dashboard/documents', icon: 'FileText' },
    ],
  },
  {
    section: 'OPERATIONS',
    items: [
      { label: 'Trips', path: '/dashboard/trips', icon: 'Route' },
      { label: 'Fuel Management', path: '/dashboard/fuel', icon: 'Fuel' },
      { label: 'Expense Management', path: '/dashboard/expenses', icon: 'Receipt' },
      { label: 'Payments', path: '/dashboard/payments', icon: 'CreditCard' },
      { label: 'Maintenance', path: '/dashboard/maintenance', icon: 'Wrench' },
    ],
  },
  {
    section: 'SYSTEM',
    items: [
      { label: 'System Users', path: '/dashboard/admin/users', icon: 'Users' },
      { label: 'Audit Logs', path: '/dashboard/admin/audit', icon: 'FileText' },
      { label: 'Settings', path: '/dashboard/settings', icon: 'Settings' },
    ],
  },
];

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { t } = useLanguage();
  const [user, setUser] = useState({ name: 'Dev1', role: 'Company Admin' });

  useEffect(() => {
    const handleUserUpdate = () => {
      const cached = localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user');
      if (cached) {
        setUser(JSON.parse(cached));
      }
    };
    handleUserUpdate();
    window.addEventListener('storage', handleUserUpdate);
    return () => window.removeEventListener('storage', handleUserUpdate);
  }, []);

  const location = useLocation();
  const navigate = useNavigate();
  const isMobile = useIsMobile();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const sidebarContent = (
    <div className="flex flex-col h-full overflow-hidden select-none">
      {/* Logo */}
      <div className="flex items-center h-16 px-5 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
            <img src="/assets/fleetguard-logo.png" alt="FleetGuard Logo" className="w-full h-full object-contain" />
          </div>
          <span className="text-[15px] font-bold text-content whitespace-nowrap">
            Fleet<span className="text-brand-500">Guard</span>
          </span>
        </div>
        {isMobile && (
          <button onClick={onMobileClose} className="ml-auto p-1.5 rounded-lg hover:bg-surface-tertiary text-content-secondary" aria-label="Close navigation">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-5 px-3 space-y-6 fg-scrollbar" role="navigation" aria-label="Main navigation">
        {navSections.map(section => (
          <div key={section.section} className="space-y-0.5">
            <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-content-muted">
              {t(section.section)}
            </p>
            {section.items.map(item => {
              const isActive = item.path === '/dashboard'
                ? location.pathname === '/dashboard'
                : location.pathname === item.path || location.pathname.startsWith(item.path + '/');
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => isMobile && onMobileClose()}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-[10px] text-[13px] font-medium transition-all duration-200 relative group',
                    isActive
                      ? 'bg-brand-50 text-brand-600 border border-brand-200'
                      : 'text-content-secondary hover:text-content hover:bg-surface-tertiary border border-transparent'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <span className={cn(
                    'transition-colors duration-200',
                    isActive ? 'text-brand-500' : 'text-content-muted group-hover:text-content'
                  )}>
                    {iconMap[item.icon]}
                  </span>
                  <span>{t(item.label)}</span>
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Support & Logout Action */}
      <div className="p-4 mt-auto border-t border-border space-y-2">
        <button
          onClick={() => navigate('/dashboard/support')}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-surface-tertiary hover:bg-brand-50 border border-border text-sm font-medium text-content-secondary hover:text-brand-600 transition-all duration-200 group"
          aria-label="Open support"
        >
          <Settings className="w-4 h-4 group-hover:rotate-45 transition-transform duration-300" />
          {t("Support")}
        </button>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl hover:bg-red-50 text-sm font-medium text-content-secondary hover:text-red-600 transition-all duration-200 group"
          aria-label="Log out"
        >
          <LogOut className="w-4 h-4 group-hover:-translate-x-1 transition-transform duration-300" />
          {t("Log out")}
        </button>
      </div>
    </div>
  );

  // Mobile layout
  if (isMobile) {
    return (
      <>
        {mobileOpen && <div className="fixed inset-0 bg-black/40 z-40 backdrop-blur-sm" onClick={onMobileClose} aria-hidden="true" />}
        <aside
          className={cn(
            `fixed top-0 left-0 bottom-0 bg-white z-50 transition-transform duration-300 border-r border-border`,
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          )}
          style={{ width: `${SIDEBAR_WIDTH}px` }}
          role="navigation"
          aria-label="Sidebar navigation"
        >
          {sidebarContent}
        </aside>
      </>
    );
  }

  // Desktop — fixed sidebar
  return (
    <aside
      className="fixed top-0 left-0 bottom-0 bg-white border-r border-border z-30 flex flex-col shadow-card"
      style={{ width: `${SIDEBAR_WIDTH}px` }}
      role="navigation"
      aria-label="Sidebar navigation"
    >
      {sidebarContent}
    </aside>
  );
}
