import { useState, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Menu, Moon, Sun, Settings } from 'lucide-react';
import { getCurrentUser } from '@/api/authApi';
import { Sidebar } from '@/components/shared/Sidebar';
import { Loader } from '@/components/ui/Loader';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';
import { useTheme } from '@/theme/ThemeContext';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { NotificationBell } from '@/components/shared/NotificationDropdown';
import { getInitials } from '@/utils/formatters';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);
  const [user, setUser] = useState(null);
  
  const isMobile = useIsMobile();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    let active = true;
    async function checkSession() {
      try {
        const u = await getCurrentUser();
        if (active) {
          if (!u) navigate('/login', { replace: true });
          else setUser(u);
        }
      } catch {
        if (active) navigate('/login', { replace: true });
      } finally {
        if (active) setAuthChecking(false);
      }
    }
    checkSession();
    return () => { active = false; };
  }, [navigate]);

  if (authChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-fg-dark text-fg-text">
        <Loader size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-fg-dark text-fg-text relative">
      <Sidebar
        collapsed={false}
        onToggle={() => {}}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      {/* Floating Glass Utility Cluster */}
      {!isMobile && (
        <div className="fixed top-4 right-6 z-40 flex items-center gap-2 p-1.5 rounded-2xl bg-surface/40 backdrop-blur-md border border-border shadow-sm hover:shadow-fg-glow transition-all duration-300">
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-xl text-content-secondary hover:text-content hover:bg-surface-secondary transition-colors"
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun className="w-4.5 h-4.5" /> : <Moon className="w-4.5 h-4.5" />}
          </button>
          <LanguageSelector variant="adaptive" />
          <NotificationBell />
          <button
            onClick={() => navigate('/dashboard/profile')}
            className="flex items-center gap-2 pl-1 pr-3 py-1 rounded-xl hover:bg-surface-secondary transition-colors border-l border-border/50 ml-1"
          >
            <div className="w-7 h-7 rounded-full bg-fg-green/10 flex items-center justify-center text-[10px] font-bold text-fg-green border border-fg-green/20">
              {getInitials(user?.name || 'Dev1')}
            </div>
            <div className="hidden lg:block text-left">
              <p className="text-xs font-medium text-content leading-tight">{user?.name || 'Dev1'}</p>
            </div>
          </button>
        </div>
      )}

      <div className={cn(
        'transition-all duration-300 min-h-screen flex flex-col',
        isMobile ? 'ml-0' : 'ml-[200px]'
      )}>
        {isMobile && (
          <header className="sticky top-0 z-20 h-14 bg-fg-deep/90 backdrop-blur-md border-b border-white/[0.07] flex items-center px-4 justify-between md:hidden">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 rounded-lg text-fg-text-sec hover:text-fg-text hover:bg-white/[0.05]"
              title="Open Navigation Menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 flex items-center justify-center">
                <img src="/assets/fleetguard-logo.png" alt="FleetGuard" className="w-full h-full object-contain" />
              </div>
              <span className="text-sm font-bold text-fg-text">Fleet<span className="text-fg-green">Guard</span></span>
            </div>
          </header>
        )}
        <main className="p-4 md:p-6 lg:p-8 flex-1 fg-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
