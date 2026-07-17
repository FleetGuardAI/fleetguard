import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Truck,
  Users,
  Receipt,
  Fuel,
  Bell,
  Settings,
  Shield,
  LogOut,
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Trucks', path: '/dashboard/trucks', icon: Truck },
  { label: 'Drivers', path: '/dashboard/drivers', icon: Users },
  { label: 'Expenses', path: '/dashboard/tickets', icon: Receipt, badge: 7 },
  { label: 'Fuel Monitor', path: '/dashboard/fuel', icon: Fuel },
  { label: 'Alerts', path: '/dashboard/alerts', icon: Bell, badge: 3 },
];

/**
 * Slim Sidebar component
 * Replicates the icon navigation panel on the left side of the monitor screen.
 */
export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-16 z-50 flex flex-col items-center py-4 bg-white border-r border-slate-200 shrink-0 shadow-sm">
      {/* Brand Logo */}
      <div className="w-9 h-9 flex items-center justify-center mb-8 shrink-0">
        <img src="/assets/fleetguard-logo.png" alt="FleetGuard Logo" className="w-full h-full object-contain" />
      </div>

      {/* Nav Actions */}
      <nav className="flex-1 w-full px-2 space-y-3 flex flex-col items-center">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path ||
            (item.path === '/dashboard' && location.pathname === '/dashboard');

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`group relative flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200
                ${isActive
                  ? 'bg-emerald-50 text-emerald-600 border border-emerald-100 shadow-sm'
                  : 'text-slate-400 hover:text-emerald-600 hover:bg-slate-50'
                }`}
              title={item.label}
            >
              <Icon className="w-5 h-5" />
              {item.badge && (
                <span className="absolute -top-1 -right-1 w-4.5 h-4.5 rounded-full bg-red-500 text-[9px] font-bold text-white flex items-center justify-center border-2 border-white">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Profile Settings */}
      <div className="mt-auto px-2 space-y-4 flex flex-col items-center w-full">
        <NavLink
          to="/dashboard/settings"
          className={({ isActive }) => `flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200
            ${isActive ? 'bg-emerald-50 text-emerald-600' : 'text-slate-400 hover:text-emerald-600 hover:bg-slate-50'}`}
          title="Settings"
        >
          <Settings className="w-5 h-5" />
        </NavLink>

        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-600 to-emerald-700 flex items-center justify-center text-white text-xs font-bold shrink-0 cursor-pointer shadow-lg">
          SC
        </div>
      </div>
    </aside>
  );
}
