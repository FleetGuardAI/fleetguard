import { useState, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { getCurrentUser } from '@/api/authApi';
import { Sidebar } from '@/components/shared/Sidebar';
import { Loader } from '@/components/ui/Loader';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { NotificationBell } from '@/components/shared/NotificationDropdown';
import { getInitials } from '@/utils/formatters';

const SIDEBAR_WIDTH = 240;

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);
  const [user, setUser] = useState(null);
  
  const isMobile = useIsMobile();
  const navigate = useNavigate();

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
      <div className="flex items-center justify-center min-h-screen bg-white text-content">
        <Loader size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-base text-content relative overflow-x-hidden">
      <Sidebar
        collapsed={false}
        onToggle={() => {}}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      {/* Floating Utility Cluster — pinned top-right */}
      {!isMobile && (
        <div
          className="fixed top-4 right-6 z-40 flex items-center gap-2 p-1.5 rounded-2xl bg-white/80 backdrop-blur-xl border border-border shadow-card hover:shadow-elevated transition-all duration-300"
          role="toolbar"
          aria-label="Utility toolbar"
        >
          <LanguageSelector variant="adaptive" />
          <NotificationBell />
          <button
            onClick={() => navigate('/dashboard/profile')}
            className="flex items-center gap-2 pl-1 pr-3 py-1 rounded-xl hover:bg-surface-tertiary transition-colors border-l border-border/50 ml-1"
            aria-label="View profile"
          >
            <div className="w-7 h-7 rounded-full bg-brand-50 flex items-center justify-center text-[10px] font-bold text-brand-600 border border-brand-200">
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
        isMobile ? 'ml-0' : `ml-[${SIDEBAR_WIDTH}px]`
      )}
        style={!isMobile ? { marginLeft: `${SIDEBAR_WIDTH}px` } : undefined}
      >
        {isMobile && (
          <header className="sticky top-0 z-20 h-14 bg-white/90 backdrop-blur-md border-b border-border flex items-center px-4 justify-between md:hidden">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 rounded-lg text-content-secondary hover:text-content hover:bg-surface-tertiary"
              title="Open Navigation Menu"
              aria-label="Open navigation menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 flex items-center justify-center">
                <img src="/assets/fleetguard-logo.png" alt="FleetGuard" className="w-full h-full object-contain" />
              </div>
              <span className="text-sm font-bold text-content">Fleet<span className="text-brand-500">Guard</span></span>
            </div>
            <div className="flex items-center gap-1">
              <NotificationBell />
            </div>
          </header>
        )}
        <main className="p-4 md:p-6 lg:p-8 lg:pt-24 flex-1 fg-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
