import { useState, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { getCurrentUser } from '@/api/authApi';
import { Sidebar } from '@/components/shared/Sidebar';
import { TopNavbar } from '@/components/shared/TopNavbar';
import { Loader } from '@/components/ui/Loader';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';

export default function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);
  const isMobile = useIsMobile();
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;

    async function checkSession() {
      try {
        const user = await getCurrentUser();
        if (!user && active) {
          navigate('/login', { replace: true });
        }
      } catch {
        if (active) {
          navigate('/login', { replace: true });
        }
      } finally {
        if (active) {
          setAuthChecking(false);
        }
      }
    }

    checkSession();

    return () => {
      active = false;
    };
  }, [navigate]);

  if (authChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-secondary">
        <Loader size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-secondary">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      <div className={cn(
        'transition-all duration-300 min-h-screen flex flex-col',
        isMobile ? 'ml-0' : (sidebarCollapsed ? 'ml-[72px]' : 'ml-[260px]')
      )}>
        <TopNavbar
          sidebarCollapsed={sidebarCollapsed}
          isMobile={isMobile}
          onMenuClick={() => isMobile ? setMobileMenuOpen(true) : setSidebarCollapsed(!sidebarCollapsed)}
        />
        <main className="p-4 md:p-6 lg:p-8 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
