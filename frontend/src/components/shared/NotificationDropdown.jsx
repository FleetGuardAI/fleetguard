import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Check } from 'lucide-react';
import { Dropdown } from '@/components/ui/Dropdown';
import { formatRelativeTime } from '@/utils/formatters';
import { cn } from '@/utils/cn';

// Embedded mock notifications generator to avoid external service dependencies
function generateNotifications(count = 8) {
  const types = ['alert', 'success', 'warning', 'info'];
  const titles = {
    alert: 'Fraud Alert',
    success: 'Trip Completed',
    warning: 'Document Expiring',
    info: 'New Expense'
  };
  const messages = {
    alert: 'Suspicious expense claim detected for vehicle RJ14 XX 1234',
    success: 'Trip from Jaipur to Delhi completed successfully',
    warning: 'Driver license for Ramesh Kumar expires in 30 days',
    info: 'New expense claim of ₹450 submitted'
  };
  return Array.from({ length: count }, (_, i) => {
    const type = types[i % types.length];
    return {
      id: `n${i + 1}`,
      type,
      title: titles[type],
      message: messages[type],
      read: i > 2,
      createdAt: new Date(Date.now() - i * 3600000).toISOString()
    };
  });
}

export function NotificationDropdown() {
  const [notifications, setNotifications] = useState(() => generateNotifications(8));
  const navigate = useNavigate();

  const unreadCount = useMemo(() => notifications.filter(n => !n.read).length, [notifications]);

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const typeColors = {
    alert: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
    warning: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
    success: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
    info: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  };

  return (
    <div className="relative">
      <Dropdown
        trigger={
          <div className="relative p-2 rounded-lg hover:bg-surface-secondary transition-colors text-content-secondary">
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </div>
        }
        items={[
          {
            label: '',
            onClick: () => {},
          },
        ]}
        align="right"
      />
      <NotificationPanel
        notifications={notifications}
        onMarkAllRead={markAllRead}
        onViewAll={() => navigate('/notifications')}
        typeColors={typeColors}
      />
    </div>
  );
}

function NotificationPanel({ notifications, onMarkAllRead, onViewAll, typeColors }) {
  return null;
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState(() => generateNotifications(8));
  const navigate = useNavigate();

  const unreadCount = useMemo(() => notifications.filter(n => !n.read).length, [notifications]);

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const typeIcons = {
    alert: '🚨', warning: '⚠️', success: '✅', info: 'ℹ️',
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-lg hover:bg-surface-secondary transition-colors text-content-secondary"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-80 bg-surface border border-border rounded-xl shadow-elevated z-50 animate-fade-in overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <h3 className="text-sm font-semibold text-content">Notifications</h3>
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
                  <Check className="h-3 w-3" /> Mark all read
                </button>
              )}
            </div>

            <div className="max-h-80 overflow-y-auto divide-y divide-border">
              {notifications.slice(0, 6).map(n => (
                <div
                  key={n.id}
                  className={cn(
                    'px-4 py-3 hover:bg-surface-secondary/50 transition-colors cursor-pointer',
                    !n.read && 'bg-brand-50/50 dark:bg-brand-900/10'
                  )}
                >
                  <div className="flex gap-3">
                    <span className="text-lg">{typeIcons[n.type] || 'ℹ️'}</span>
                    <div className="flex-1 min-w-0">
                      <p className={cn('text-sm', !n.read ? 'font-semibold text-content' : 'text-content-secondary')}>
                        {n.title}
                      </p>
                      <p className="text-xs text-content-muted mt-0.5 line-clamp-2">{n.message}</p>
                      <p className="text-xs text-content-muted mt-1">{formatRelativeTime(n.createdAt)}</p>
                    </div>
                    {!n.read && <span className="w-2 h-2 rounded-full bg-brand-500 mt-1.5 flex-shrink-0" />}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-border p-2">
              <button
                onClick={() => { navigate('/notifications'); setOpen(false); }}
                className="w-full py-2 text-sm font-medium text-brand-600 hover:bg-surface-secondary rounded-lg transition-colors"
              >
                View All Notifications
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
