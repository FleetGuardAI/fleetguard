import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Bell, Sun, Moon, User, Settings, LogOut } from 'lucide-react';
import { useLocalStorage } from '@/hooks/useLocalStorage';
import { Dropdown } from '@/components/ui/Dropdown';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { NotificationBell } from '@/components/shared/NotificationDropdown';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { getInitials } from '@/utils/formatters';
import { cn } from '@/utils/cn';

export function TopNavbar({ sidebarCollapsed, isMobile, onMenuClick }) {
  const [user, setUser] = useState({ name: 'Suryansh Chaudhary', role: 'COO' });

  useEffect(() => {
    const cached = localStorage.getItem('fleetguard_user');
    if (cached) {
      setUser(JSON.parse(cached));
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('fleetguard_user');
    localStorage.removeItem('fleetguard_token');
  };

  const navigate = useNavigate();
  const [theme, setTheme] = useLocalStorage('fleetguard_theme', 'light');

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    document.documentElement.classList.toggle('dark', next === 'dark');
  };

  const handleLogout = () => { logout(); navigate('/login'); };

  const userMenuItems = [
    { label: 'Profile', icon: <User className="h-4 w-4" />, onClick: () => navigate('/profile') },
    { label: 'Settings', icon: <Settings className="h-4 w-4" />, onClick: () => navigate('/settings') },
    { divider: true, label: '' },
    { label: 'Sign Out', icon: <LogOut className="h-4 w-4" />, onClick: handleLogout, danger: true },
  ];

  return (
    <header className="sticky top-0 z-20 h-16 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md border-b border-border flex items-center px-4 md:px-6 gap-4 transition-all duration-300">
      <button onClick={onMenuClick} className="p-2 rounded-lg hover:bg-surface-secondary transition-colors text-content-secondary md:hidden">
        <Menu className="h-5 w-5" />
      </button>

      <Breadcrumbs className="hidden md:flex flex-1" />
      <div className="flex-1 md:hidden" />

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-surface-secondary transition-colors text-content-secondary"
          title={theme === 'light' ? 'Dark mode' : 'Light mode'}
        >
          {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        </button>

        {/* Language */}
        <LanguageSelector variant="adaptive" />

        {/* Notifications */}
        <NotificationBell />

        {/* User menu */}
        <Dropdown
          trigger={
            <div className="flex items-center gap-2.5 pl-2 cursor-pointer">
              <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold text-white">
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
