import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Check } from 'lucide-react';
import { Dropdown } from '@/components/ui/Dropdown';
import { getNotifications, markAllNotificationsRead } from '@/api/notificationApi';
import { formatRelativeTime } from '@/utils/formatters';
import { cn } from '@/utils/cn';

export function NotificationDropdown() {
  const [notifications, setNotifications] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    getNotifications()
      .then(data => setNotifications(data))
      .catch(() => setNotifications([]));
  }, []);

  const unreadCount = useMemo(() => notifications.filter(n => !n.read).length, [notifications]);

  const markAllRead = async () => {
    await markAllNotificationsRead();
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
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
            label: 'View Notifications',
            onClick: () => navigate('/dashboard/notifications'),
          },
        ]}
        align="right"
      />
    </div>
  );
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    getNotifications()
      .then(data => setNotifications(data))
      .catch(() => setNotifications([]));
  }, []);

  const unreadCount = useMemo(() => notifications.filter(n => !n.read).length, [notifications]);

  const markAllRead = async () => {
    await markAllNotificationsRead();
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
              {notifications.length === 0 ? (
                <div className="p-4 text-center text-xs text-content-muted">No unread notifications</div>
              ) : (
                notifications.slice(0, 6).map(n => (
                  <div
                    key={n.id}
                    className={cn(
                      'px-4 py-3 hover:bg-surface-secondary/50 transition-colors cursor-pointer',
                      !n.read && 'bg-brand-50/50'
                    )}
                  >
                    <div className="flex gap-3">
                      <span className="text-lg">{typeIcons[n.type] || 'ℹ️'}</span>
                      <div className="flex-1 min-w-0">
                        <p className={cn('text-sm', !n.read ? 'font-semibold text-content' : 'text-content-secondary')}>
                          {n.title}
                        </p>
                        <p className="text-xs text-content-muted mt-0.5 line-clamp-2">{n.message}</p>
                        <p className="text-xs text-content-muted mt-1">{formatRelativeTime(n.date || n.createdAt)}</p>
                      </div>
                      {!n.read && <span className="w-2 h-2 rounded-full bg-brand-500 mt-1.5 flex-shrink-0" />}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="border-t border-border p-2">
              <button
                onClick={() => { navigate('/dashboard/notifications'); setOpen(false); }}
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
