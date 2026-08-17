import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Home, Truck, Navigation, User } from 'lucide-react';
import { cn } from '@/utils/cn';

export function BottomNav() {
  const location = useLocation();

  const navItems = [
    {
      id: 'home',
      label: 'Home',
      path: '/dashboard',
      exact: true,
      icon: Home,
    },
    {
      id: 'fleet',
      label: 'Truck & Driver',
      path: '/dashboard/fleet',
      icon: Truck,
    },
    {
      id: 'navigation',
      label: 'Navigation',
      path: '/dashboard/navigation',
      icon: Navigation,
    },
    {
      id: 'profile',
      label: 'Profile',
      path: '/dashboard/profile',
      icon: User,
    },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-t border-border shadow-2xl transition-all duration-300">
      <div className="max-w-md md:max-w-xl mx-auto flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.exact
            ? location.pathname === '/dashboard' || location.pathname === '/dashboard/'
            : location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.id}
              to={item.path}
              className={({ isActive: linkActive }) => {
                const active = item.exact
                  ? location.pathname === '/dashboard' || location.pathname === '/dashboard/'
                  : linkActive || isActive;
                return cn(
                  'flex flex-col items-center justify-center flex-1 h-full px-1 py-1 rounded-xl transition-all duration-200 group relative',
                  active
                    ? 'text-brand-600 dark:text-brand-400 font-bold'
                    : 'text-content-muted hover:text-content font-medium'
                );
              }}
            >
              {({ isActive: linkActive }) => {
                const active = item.exact
                  ? location.pathname === '/dashboard' || location.pathname === '/dashboard/'
                  : linkActive || isActive;
                return (
                  <>
                    <div
                      className={cn(
                        'p-1.5 rounded-xl transition-all duration-200 relative',
                        active
                          ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 scale-110 shadow-sm'
                          : 'group-hover:bg-surface-secondary'
                      )}
                    >
                      <Icon className="w-5 h-5 transition-transform duration-200" />
                      {active && (
                        <span className="absolute -top-1 right-1 w-1.5 h-1.5 bg-brand-500 rounded-full animate-ping" />
                      )}
                    </div>
                    <span className="text-[11px] leading-tight tracking-tight mt-0.5 whitespace-nowrap">
                      {item.label}
                    </span>
                  </>
                );
              }}
            </NavLink>
          );
        })}
      </div>
    </div>
  );
}
