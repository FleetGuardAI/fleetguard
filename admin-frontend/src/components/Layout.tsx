import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { 
  LayoutDashboard, 
  Ticket, 
  KeyRound, 
  FileCheck, 
  Activity,
  LogOut
} from 'lucide-react';

export default function Layout() {
  const { logout } = useAuth();
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Support Tickets', path: '/tickets', icon: Ticket },
    { name: 'Password Resets', path: '/password-resets', icon: KeyRound },
    { name: 'Document Verification', path: '/documents', icon: FileCheck },
    { name: 'Audit Logs', path: '/audit-logs', icon: Activity },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col border-r border-slate-800 shadow-xl">
        <div className="h-16 flex items-center px-6 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center gap-2">
            <img src="/assets/the_vahan_logo.png" alt="Vahan Logo" className="h-6 w-auto object-contain brightness-0 invert" />
            <span className="text-lg font-bold tracking-wide">Vahan</span>
          </div>
        </div>
        
        <div className="px-6 py-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Operations Portal</p>
        </div>
        
        <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                  isActive 
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm' 
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-emerald-400' : 'text-slate-500'} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800 mt-auto">
          <button 
            onClick={logout}
            className="flex items-center space-x-3 text-slate-400 hover:text-red-400 hover:bg-red-500/10 w-full px-3 py-2.5 rounded-lg transition-colors text-sm font-medium"
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-50">
        <div className="p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
