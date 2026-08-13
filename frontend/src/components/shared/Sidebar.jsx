import { useState, useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Truck, Users, Route, Fuel, Receipt, Bell, Settings,
  LogOut, CreditCard, Wrench, FileText, AlertTriangle, BarChart3, User,
  Disc, Cpu, MessageSquare, X
} from 'lucide-react';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';
import { getInitials } from '@/utils/formatters';
import { useLanguage } from '@/i18n/LanguageContext';
import { logout } from '@/api/authApi';

const iconMap = {
  LayoutDashboard: <LayoutDashboard className="h-[18px] w-[18px]" />,
  MessageSquare: <MessageSquare className="h-[18px] w-[18px]" />,
  BarChart3: <BarChart3 className="h-[18px] w-[18px]" />,
  Truck: <Truck className="h-[18px] w-[18px]" />,
  Users: <Users className="h-[18px] w-[18px]" />,
  Disc: <Disc className="h-[18px] w-[18px]" />,
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
};

const navSections = [
  {
    section: 'OVERVIEW',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: 'LayoutDashboard' },
      { label: 'Chat Box', path: '/dashboard/chatbox', icon: 'MessageSquare' },
      { label: 'Reports & Analytics', path: '/dashboard/reports', icon: 'BarChart3' },
    ],
  },
  {
    section: 'FLEET',
    items: [
      { label: 'Vehicles', path: '/dashboard/vehicles', icon: 'Truck' },
      { label: 'Drivers', path: '/dashboard/drivers', icon: 'Users' },
      { label: 'Tyres', path: '/dashboard/tyres', icon: 'Disc' },
      { label: 'Hardware Assets', path: '/dashboard/assets', icon: 'Cpu' },
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
      <div className="flex items-center h-16 px-5 border-b border-white/[0.07] flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
            <img src="/assets/fleetguard-logo.png" alt="FleetGuard Logo" className="w-full h-full object-contain" />
          </div>
          <span className="text-[15px] font-bold text-fg-text whitespace-nowrap">
            Fleet<span className="text-fg-green">Guard</span>
          </span>
        </div>
        {isMobile && (
          <button onClick={onMobileClose} className="ml-auto p-1.5 rounded-lg hover:bg-white/10 text-fg-text-sec">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-5 px-3 space-y-6 fg-scrollbar">
        {navSections.map(section => (
          <div key={section.section} className="space-y-0.5">
            <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-fg-text-sec/60">
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
                    'flex items-center gap-3 px-3 py-2 rounded-[10px] text-[13px] font-medium transition-all duration-300 relative group',
                    isActive
                      ? 'bg-fg-green/10 text-fg-green shadow-[0_0_15px_rgba(25,184,106,0.15)] border border-fg-green/20'
                      : 'text-content-secondary hover:text-content hover:bg-surface-secondary/50 border border-transparent'
                  )}
                >
                  <span className={cn(
                    'transition-colors duration-200',
                    isActive ? 'text-fg-green' : 'text-content-muted group-hover:text-content'
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
    </div>
  );

  // Mobile layout
  if (isMobile) {
    return (
      <>
        {mobileOpen && <div className="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm" onClick={onMobileClose} />}
        <aside className={cn(
          'fixed top-0 left-0 bottom-0 w-[200px] bg-fg-deep z-50 transition-transform duration-300 border-r border-white/[0.07]',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}>
          {sidebarContent}
        </aside>
      </>
    );
  }

  // Desktop — fixed 200px sidebar, no collapse
  return (
    <aside className="fixed top-0 left-0 bottom-0 w-[200px] bg-gradient-to-b from-surface/80 to-surface/40 backdrop-blur-xl border-r border-border/60 z-30 flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.05)]">
      {sidebarContent}
    </aside>
  );
}
