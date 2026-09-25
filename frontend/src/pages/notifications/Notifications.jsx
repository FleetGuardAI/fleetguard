import React, { useState, useEffect } from 'react';
import { Bell, Check, Trash2, Mail, MailOpen, ShieldAlert, FileText, IndianRupee, Settings, RefreshCw, Truck, MapPin } from 'lucide-react';
import { getNotifications, markNotificationRead, markAllNotificationsRead, deleteNotification } from '@/api/notificationApi';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { SearchBox } from '@/components/shared/SearchBox';
import { Pagination } from '@/components/ui/Pagination';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { usePagination } from '@/hooks/usePagination';
import { cn } from '@/utils/cn';

export default function Notifications() {
  const { success, error, info } = useToast();

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [readFilter, setReadFilter] = useState('all'); // all, unread, read
  const [typeFilter, setTypeFilter] = useState('all'); // all, ALERT, TRIP, VEHICLE, FINANCE, SYSTEM

  const loadNotifications = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getNotifications({
        search,
        type: typeFilter,
        read: readFilter === 'all' ? undefined : (readFilter === 'read')
      });
      setNotifications(data);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve notifications.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [search, readFilter, typeFilter]);

  // Pagination
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: notifications.length, initialPageSize: 10 });

  const paginatedNotifications = notifications.slice(startIndex, endIndex);

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      success('Read Status Updated', 'Notification marked as read.');
    } catch (e) {
      error('Action Failed', 'Failed to update notification.');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      success('Bulk Updated', 'All notifications marked as read.');
    } catch (e) {
      error('Action Failed', 'Failed to update notifications.');
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteNotification(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      info('Notification Deleted', 'Notification removed permanently.');
    } catch (e) {
      error('Delete Failed', 'Could not delete notification.');
    }
  };

  const handleViewDocument = async (docId) => {
    const popup = window.open('', '_blank');
    try {
      console.log(`[DocumentView] clicked`);
      console.log(`[DocumentView] document_id=${docId}`);
      console.log(`[DocumentView] request started`);
      
      const response = await getDocumentById(docId);
      
      console.log(`[DocumentView] response status=200`);
      console.log(`[DocumentView] response keys=${Object.keys(response).join(', ')}`);
      
      const url = response.signed_url || response.storage_path || response.url;
      console.log(`[DocumentView] signed URL available=${!!url}`);

      if (!url) {
        throw new Error("Document URL missing");
      }

      popup.location.href = url;
    } catch (e) {
      popup?.close();
      const status = e.response?.status;
      if (status === 404) {
        error("Document not found", "The requested document could not be found.");
      } else if (status === 403) {
        error("Access Denied", "You do not have permission to access this document.");
      } else if (status === 401) {
        error("Session Expired", "Your session has expired.");
      } else if (e.message === "Document URL missing") {
        error("Document Unavailable", "Document URL was not returned by the server.");
      } else {
        error("Error", "Unable to retrieve document.");
      }
    }
  };
  const getCategoryIcon = (type) => {
    const classes = "h-5 w-5";
    switch (type) {
      case 'ALERT':
        return <ShieldAlert className={cn(classes, "text-red-500")} />;
      case 'TRIP':
        return <MapPin className={cn(classes, "text-blue-500")} />;
      case 'VEHICLE':
        return <Truck className={cn(classes, "text-indigo-500")} />;
      case 'FINANCE':
        return <IndianRupee className={cn(classes, "text-green-600")} />;
      case 'SYSTEM':
        return <Settings className={cn(classes, "text-purple-500")} />;
      default:
        return <Bell className={cn(classes, "text-gray-500")} />;
    }
  };

  const getCategoryClass = (type) => {
    switch (type) {
      case 'ALERT':
        return 'bg-red-50 border-red-100';
      case 'TRIP':
        return 'bg-blue-50 border-blue-100';
      case 'VEHICLE':
        return 'bg-indigo-50 border-indigo-100';
      case 'FINANCE':
        return 'bg-green-50 border-green-100';
      case 'SYSTEM':
        return 'bg-purple-50 border-purple-100';
      default:
        return 'bg-gray-50 border-gray-100';
    }
  };

  const getCategoryLabel = (type) => {
    const map = {
      ALERT: 'ALERTS',
      TRIP: 'TRIP',
      VEHICLE: 'VEHICLE',
      FINANCE: 'FINANCE',
      SYSTEM: 'SYSTEM',
    };
    return map[type] || (type || 'SYSTEM').toUpperCase();
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content flex items-center gap-2">
            <Bell className="h-6 w-6" />
            Notifications Center
            {unreadCount > 0 && (
              <span className="text-xs bg-brand-600 text-white font-semibold px-2 py-0.5 rounded-full">
                {unreadCount} Unread
              </span>
            )}
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">Stay updated with driver advance tickets, fuel drop alarms, and safety alerts.</p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            icon={<Check className="h-4 w-4 text-brand-600" />}
            onClick={handleMarkAllRead}
          >
            Mark All as Read
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => setReadFilter('all')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            readFilter === 'all'
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          All Inbox
        </button>
        <button
          onClick={() => setReadFilter('unread')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            readFilter === 'unread'
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Unread Only
        </button>
      </div>

      {/* Filters Toolbar */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search notifications..."
          className="w-full md:max-w-xs"
        />

        <div className="w-full md:w-auto">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
          >
            <option value="all">All Categories</option>
            <option value="ALERT">Alerts</option>
            <option value="TRIP">Trip</option>
            <option value="VEHICLE">Vehicle</option>
            <option value="FINANCE">Finance</option>
            <option value="SYSTEM">System</option>
          </select>
        </div>
      </Card>

      {/* Notifications List */}
      <div className="space-y-4">
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-24 w-full rounded-xl" />
          </div>
        ) : err ? (
          <ErrorState
            title="Failed to Load Notifications"
            message={err.message || 'An error occurred.'}
            onRetry={loadNotifications}
          />
        ) : notifications.length === 0 ? (
          <EmptyState
            title="Notification Inbox is Clean"
            description="There are no system notifications matching the current criteria."
          />
        ) : (
          <>
            <div className="space-y-3">
              {paginatedNotifications.map((item) => (
                <div
                  key={item.id}
                  className={cn(
                    "flex items-start justify-between p-4 border rounded-xl hover:shadow-sm transition-all duration-200 gap-4",
                    item.read
                      ? "bg-surface border-border opacity-75"
                      : "bg-brand-50/10 border-brand-100"
                  )}
                >
                  <div className="flex items-start gap-3.5">
                    <div className={cn("p-2.5 rounded-lg border", getCategoryClass(item.type))}>
                      {getCategoryIcon(item.type)}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-content-secondary tracking-wider">
                          {getCategoryLabel(item.type)}
                        </span>
                        {!item.read && (
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-600" />
                        )}
                      </div>
                      <h4 className={cn("text-sm font-semibold", item.read ? "text-content-secondary" : "text-content")}>
                        {item.title}
                      </h4>
                      <p className="text-xs text-content-secondary leading-relaxed">
                        {item.message}
                      </p>
                      <span className="text-[10px] text-content-muted block pt-1">
                        {item.date ? new Date(item.date).toLocaleString() : "Date unavailable"}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-1.5">
                    {!item.read && (
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<MailOpen className="h-4 w-4 text-brand-600" />}
                        onClick={() => handleMarkRead(item.id)}
                        title="Mark as Read"
                      />
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:bg-red-50"
                      icon={<Trash2 className="h-4 w-4" />}
                      onClick={() => handleDelete(item.id)}
                      title="Delete"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-2">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={notifications.length}
                onPageChange={goToPage}
                onPageSizeChange={changePageSize}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
