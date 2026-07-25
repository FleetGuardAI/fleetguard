import { useState, useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Truck, Users, Route, Fuel, Receipt, Bell, Settings,
  ChevronLeft, ChevronRight, LogOut, Shield, X, CreditCard, Wrench,
  FileText, AlertTriangle, BarChart3, User, UserCheck, Lock, History, Pin, PinOff,
  Disc, Cpu
} from 'lucide-react';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';
import { getInitials } from '@/utils/formatters';
import { useLanguage } from '@/i18n/LanguageContext';

const iconMap = {
  LayoutDashboard: <LayoutDashboard className="h-5 w-5" />,
  Truck: <Truck className="h-5 w-5" />,
  Users: <Users className="h-5 w-5" />,
  Route: <Route className="h-5 w-5" />,
  Fuel: <Fuel className="h-5 w-5" />,
  Receipt: <Receipt className="h-5 w-5" />,
  Bell: <Bell className="h-5 w-5" />,
  Settings: <Settings className="h-5 w-5" />,
  CreditCard: <CreditCard className="h-5 w-5" />,
  Wrench: <Wrench className="h-5 w-5" />,
  FileText: <FileText className="h-5 w-5" />,
  AlertTriangle: <AlertTriangle className="h-5 w-5" />,
  BarChart3: <BarChart3 className="h-5 w-5" />,
  User: <User className="h-5 w-5" />,
  UserCheck: <UserCheck className="h-5 w-5" />,
  Lock: <Lock className="h-5 w-5" />,
  History: <History className="h-5 w-5" />,
  Disc: <Disc className="h-5 w-5" />,
  Cpu: <Cpu className="h-5 w-5" />,
};

const navSections = [
  {
    section: 'Overview',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: 'LayoutDashboard' },
      { label: 'Reports & Analytics', path: '/dashboard/reports', icon: 'BarChart3' },
    ],
  },
  {
    section: 'Fleet',
    items: [
      { label: 'Vehicles', path: '/dashboard/vehicles', icon: 'Truck' },
      { label: 'Drivers', path: '/dashboard/drivers', icon: 'Users' },
      { label: 'Tyres', path: '/dashboard/tyres', icon: 'Disc' },
      { label: 'Hardware Assets', path: '/dashboard/assets', icon: 'Cpu' },
    ],
  },
  {
    section: 'Operations',
    items: [
      { label: 'Trips', path: '/dashboard/trips', icon: 'Route' },
      { label: 'Fuel Management', path: '/dashboard/fuel', icon: 'Fuel' },
      { label: 'Expense Management', path: '/dashboard/expenses', icon: 'Receipt' },
      { label: 'Payments', path: '/dashboard/payments', icon: 'CreditCard' },
      { label: 'Maintenance', path: '/dashboard/maintenance', icon: 'Wrench' },
      { label: 'Documents', path: '/dashboard/documents', icon: 'FileText' },
    ],
  },
  {
    section: 'System',
    items: [
      { label: 'Alerts', path: '/dashboard/alerts', icon: 'AlertTriangle' },
      { label: 'Notifications', path: '/dashboard/notifications', icon: 'Bell' },
      { label: 'Profile', path: '/dashboard/profile', icon: 'User' },
      { label: 'Settings', path: '/dashboard/settings', icon: 'Settings' },
    ],
  },
  {
    section: 'Admin (System)',
    items: [
      { label: 'User Management', path: '/dashboard/admin/users', icon: 'UserCheck' },
      { label: 'Roles & Permissions', path: '/dashboard/admin/roles', icon: 'Lock' },
      { label: 'Audit Logs', path: '/dashboard/admin/audit', icon: 'History' },
    ],
  },
];

import { logout } from '@/api/authApi';

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { t } = useLanguage();
  const [user, setUser] = useState({ name: 'User', role: 'Fleet Manager' });
  const [hovered, setHovered] = useState(false);

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

  // Determine if full sidebar content should be displayed (either because it is pinned/not collapsed OR temporarily hovered)
  const isFullyOpen = !collapsed || hovered;

  const sidebarContent = (
    <div className="flex flex-col h-full overflow-hidden select-none">
      {/* Logo */}
      <div className={cn(
        'flex items-center h-16 px-4 border-b border-white/5 transition-all duration-300',
        !isFullyOpen && !isMobile && 'justify-center px-2'
      )}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
            <img src="/assets/fleetguard-logo.png" alt="FleetGuard Logo" className="w-full h-full object-contain" />
          </div>
          <AnimatePresence initial={false}>
            {(isFullyOpen || isMobile) && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className="text-lg font-bold text-white whitespace-nowrap overflow-hidden"
              >
                Fleet<span className="text-brand-400">Guard</span>
              </motion.span>
            )}
          </AnimatePresence>
        </div>
        {isMobile && (
          <button onClick={onMobileClose} className="ml-auto p-1.5 rounded-lg hover:bg-white/10 text-gray-400">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6 scrollbar-thin">
        {navSections.map(section => (
          <div key={section.section} className="space-y-1">
            <AnimatePresence initial={false}>
              {(isFullyOpen || isMobile) && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 0.5, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-400 overflow-hidden whitespace-nowrap"
                >
                  {t(section.section)}
                </motion.p>
              )}
            </AnimatePresence>
            
            <div className="space-y-0.5">
              {section.items.map(item => {
                const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => isMobile && onMobileClose()}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 relative group',
                      !isFullyOpen && !isMobile && 'justify-center px-0',
                      isActive
                        ? 'bg-brand-600/15 text-brand-400'
                        : 'text-gray-400 hover:text-white hover:bg-white/[0.03]'
                    )}
                    title={!isFullyOpen ? t(item.label) : undefined}
                  >
                    <span className={cn(isActive && 'text-brand-400')}>{iconMap[item.icon]}</span>
                    
                    <AnimatePresence initial={false}>
                      {(isFullyOpen || isMobile) && (
                        <motion.span
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -10 }}
                          transition={{ type: 'spring', stiffness: 350, damping: 25 }}
                          className="whitespace-nowrap overflow-hidden"
                        >
                          {t(item.label)}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User block */}
      <div className={cn('border-t border-white/5 p-3 transition-all duration-300', !isFullyOpen && !isMobile && 'px-2')}>
        <div className={cn('flex items-center gap-3 px-3 py-2', !isFullyOpen && !isMobile && 'justify-center px-0')}>
          <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {user ? getInitials(user.name) : 'U'}
          </div>
          
          <AnimatePresence initial={false}>
            {(isFullyOpen || isMobile) && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="flex-1 min-w-0 overflow-hidden whitespace-nowrap"
              >
                <p className="text-sm font-medium text-white truncate">{user?.name}</p>
                <p className="text-[10px] text-gray-500 truncate uppercase tracking-wider">{user?.role}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {(isFullyOpen || isMobile) && (
            <button 
              onClick={handleLogout} 
              className="p-1.5 rounded-lg hover:bg-white/10 text-gray-500 hover:text-red-400 transition-colors" 
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
      
      {/* Pinned Indicator on hover expansion */}
      {collapsed && hovered && !isMobile && (
        <button
          onClick={onToggle}
          className="absolute right-3 bottom-3 p-1.5 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 transition-all duration-200"
          title="Pin Sidebar"
        >
          <Pin className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );

  // Mobile layout
  if (isMobile) {
    return (
      <>
        {mobileOpen && <div className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm" onClick={onMobileClose} />}
        <aside className={cn(
          'fixed top-0 left-0 bottom-0 w-[260px] bg-[#0c1017] z-50 transition-transform duration-300 shadow-elevated border-r border-white/5',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}>
          {sidebarContent}
        </aside>
      </>
    );
  }

  // Desktop Framer Motion Animated Sidebar with spring physics
  return (
    <motion.aside
      onMouseEnter={() => collapsed && setHovered(true)}
      onMouseLeave={() => collapsed && setHovered(false)}
      animate={{
        width: isFullyOpen ? 260 : 72,
      }}
      transition={{
        type: 'spring',
        stiffness: 280,
        damping: 26,
      }}
      className={cn(
        'fixed top-0 left-0 bottom-0 bg-[#0c1017] border-r border-white/5 z-30 flex flex-col',
        collapsed ? 'shadow-lg hover:shadow-2xl' : ''
      )}
    >
      {sidebarContent}

      {/* Floating Pin / Unpin trigger */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-slate-900 border border-white/10 shadow-card flex items-center justify-center text-gray-400 hover:text-white hover:bg-slate-800 transition-all duration-200"
      >
        {collapsed ? (
          <Pin className="h-3 w-3" />
        ) : (
          <PinOff className="h-3 w-3" />
        )}
      </button>
    </motion.aside>
  );
}
