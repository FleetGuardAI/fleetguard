import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Bell, User, Settings, LogOut } from 'lucide-react';
import { Dropdown } from '@/components/ui/Dropdown';

import { NotificationBell } from '@/components/shared/NotificationDropdown';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { getInitials } from '@/utils/formatters';
import { cn } from '@/utils/cn';

import { logout } from '@/api/authApi';

export function TopNavbar({ sidebarCollapsed, isMobile, onMenuClick }) {
  const [user, setUser] = useState({ name: 'User', role: 'Fleet Manager' });

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

  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const userMenuItems = [
    { label: 'Profile', icon: <User className="h-4 w-4" />, onClick: () => navigate('/dashboard/profile') },
    { label: 'Settings', icon: <Settings className="h-4 w-4" />, onClick: () => navigate('/dashboard/settings') },
    { divider: true, label: '' },
    { label: 'Sign Out', icon: <LogOut className="h-4 w-4" />, onClick: handleLogout, danger: true },
  ];

  return (
    <header className="sticky top-0 z-20 h-16 bg-white/80 backdrop-blur-md border-b border-border flex items-center px-4 md:px-6 gap-4 transition-all duration-300">
      <button onClick={onMenuClick} className="p-2 rounded-lg hover:bg-surface-tertiary transition-colors text-content-secondary md:hidden">
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex-1" />
      <div className="flex items-center gap-2">
        {/* Language */}
        <LanguageSelector variant="adaptive" />

        {/* Notifications */}
        <NotificationBell />

        {/* User menu */}
        <Dropdown
          trigger={
            <div className="flex items-center gap-2.5 pl-2 cursor-pointer">
              <div className="w-8 h-8 rounded-full bg-brand-50 flex items-center justify-center text-xs font-bold text-brand-600 border border-brand-200">
                {user ? getInitials(user.name) : 'U'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-content leading-tight">{user?.name}</p>
                <p className="text-xs text-content-muted capitalize">{user?.role}</p>
              </div>
            </div>
          }
          items={userMenuItems}
          align="right"
        />
      </div>
    </header>
  );
}
