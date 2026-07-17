import { useState, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Sidebar } from '@/components/shared/Sidebar';
import { TopNavbar } from '@/components/shared/TopNavbar';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { cn } from '@/utils/cn';

export default function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isMobile = useIsMobile();
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('fleetguard_token');
    if (!token) {
      navigate('/login');
    }
  }, [navigate]);

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
