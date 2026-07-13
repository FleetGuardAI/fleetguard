import { useState, useEffect } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Truck, Users, Route, Fuel, Receipt, Bell, Settings,
  ChevronLeft, ChevronRight, LogOut, Shield, X, CreditCard, Wrench,
  FileText, AlertTriangle, BarChart3, User, UserCheck, Lock, History
} from 'lucide-react';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';
import { getInitials } from '@/utils/formatters';

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

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const [user, setUser] = useState({ name: 'Suryansh Chaudhary', role: 'COO' });

  useEffect(() => {
    const cached = localStorage.getItem('fleetguard_user');
    if (cached) {
      setUser(JSON.parse(cached));
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('fleetguard_user');
  };
  
  const location = useLocation();
  const navigate = useNavigate();
  const isMobile = useIsMobile();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className={cn('flex items-center h-16 px-4 border-b border-white/10', collapsed && !isMobile && 'justify-center px-2')}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center flex-shrink-0">
            <Shield className="h-4.5 w-4.5 text-white" />
          </div>
          {(!collapsed || isMobile) && (
            <span className="text-lg font-bold text-white">
              Fleet<span className="text-brand-400">Guard</span>
            </span>
          )}
        </div>
        {isMobile && (
          <button onClick={onMobileClose} className="ml-auto p-1.5 rounded-lg hover:bg-white/10 text-gray-400">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {navSections.map(section => (
          <div key={section.section}>
            {(!collapsed || isMobile) && (
              <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                {section.section}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map(item => {
                const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => isMobile && onMobileClose()}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                      collapsed && !isMobile && 'justify-center px-2',
                      isActive
                        ? 'bg-brand-600/20 text-brand-400'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <span className={cn(isActive && 'text-brand-400')}>{iconMap[item.icon]}</span>
                    {(!collapsed || isMobile) && item.label}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User */}
      <div className={cn('border-t border-white/10 p-3', collapsed && !isMobile && 'px-2')}>
        <div className={cn('flex items-center gap-3 px-3 py-2', collapsed && !isMobile && 'justify-center px-0')}>
          <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {user ? getInitials(user.name) : 'U'}
          </div>
          {(!collapsed || isMobile) && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.role}</p>
            </div>
          )}
          {(!collapsed || isMobile) && (
            <button onClick={handleLogout} className="p-1.5 rounded-lg hover:bg-white/10 text-gray-500 hover:text-red-400 transition-colors" title="Logout">
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Collapse toggle (desktop only) */}
      {!isMobile && (
        <button
          onClick={onToggle}
          className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-surface border border-border shadow-card flex items-center justify-center text-content-muted hover:text-content transition-colors"
        >
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      )}
    </div>
  );

  if (isMobile) {
    return (
      <>
        {mobileOpen && <div className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm" onClick={onMobileClose} />}
        <aside className={cn(
          'fixed top-0 left-0 bottom-0 w-[280px] bg-slate-900 z-50 transition-transform duration-300 shadow-elevated',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}>
          {sidebarContent}
        </aside>
      </>
    );
  }

  return (
    <aside className={cn(
      'fixed top-0 left-0 bottom-0 bg-slate-900 z-30 transition-all duration-300',
      collapsed ? 'w-[72px]' : 'w-[260px]'
    )}>
      {sidebarContent}
    </aside>
  );
}
