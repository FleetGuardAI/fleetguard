import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle, Search, Clock, ShieldX, MapPin, Send, MessageSquare } from 'lucide-react';
import { getAlerts, resolveAlert } from '@/api/alertApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SearchBox } from '@/components/shared/SearchBox';
import { Pagination } from '@/components/ui/Pagination';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { usePagination } from '@/hooks/usePagination';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { cn } from '@/utils/cn';

export default function Alerts() {
  const { success, error, info } = useToast();

  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all'); // all, critical, medium, low
  const [resolvedFilter, setResolvedFilter] = useState('unresolved'); // all, unresolved, resolved

  // Resolution Modal State
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [alertToResolve, setAlertToResolve] = useState(null);
  const [resolutionComment, setResolutionComment] = useState('');
  const [resolving, setResolving] = useState(false);

  // Details Modal State
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);

  const loadAlerts = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getAlerts({
        search,
        severity: severityFilter !== 'all' ? severityFilter : undefined,
        resolved: resolvedFilter === 'all' ? undefined : (resolvedFilter === 'resolved')
      });
      setAlerts(data);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve alerts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [search, severityFilter, resolvedFilter]);

  // Pagination
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: alerts.length, initialPageSize: 10 });

  const paginatedAlerts = alerts.slice(startIndex, endIndex);

  const handleOpenResolve = (e, item) => {
    e.stopPropagation();
    setAlertToResolve(item);
    setResolveModalOpen(true);
  };

  const handleConfirmResolve = async () => {
    if (!alertToResolve) return;
    setResolving(true);
    try {
      const updated = await resolveAlert(alertToResolve.id, resolutionComment);
      setAlerts(prev => prev.map(a => a.id === alertToResolve.id ? updated : a));
      success('Alert Resolved', `Alert #${alertToResolve.id} has been marked resolved.`);
      setResolveModalOpen(false);
      setResolutionComment('');
      setAlertToResolve(null);
    } catch (e) {
      error('Action Failed', 'Failed to resolve alert.');
    } finally {
      setResolving(false);
    }
  };

  const handleQuickDismiss = (e, id) => {
    e.stopPropagation();
    setAlerts(prev => prev.filter(a => a.id !== id));
    info('Alert Snoozed', 'Alert dismissed from local session view.');
  };

  const getSeverityVariant = (severity) => {
    if (severity === 'critical') return 'danger';
    if (severity === 'medium') return 'warning';
    return 'neutral';
  };

  const getSeverityLabel = (severity) => {
    return severity.toUpperCase();
  };

  const columns = [
    {
      key: 'id',
      label: 'Alert ID',
      render: (item) => <span className="font-semibold text-content">#{item.id}</span>
    },
    {
      key: 'truck_plate',
      label: 'Vehicle Plate',
      render: (item) => <span className="font-mono text-xs font-semibold">{item.truck_plate}</span>
    },
    {
      key: 'type',
      label: 'Category',
      render: (item) => <span className="font-medium">{item.type}</span>
    },
    {
      key: 'message',
      label: 'Description Details',
      render: (item) => <span className="truncate max-w-[200px] block text-xs">{item.message}</span>
    },
    {
      key: 'severity',
      label: 'Severity',
      render: (item) => (
        <Badge variant={getSeverityVariant(item.severity)}>
          {getSeverityLabel(item.severity)}
        </Badge>
      )
    },
    {
      key: 'date',
      label: 'Timestamp',
      render: (item) => <span className="text-xs text-content-secondary">{new Date(item.date).toLocaleString()}</span>
    },
    {
      key: 'status',
      label: 'Status',
      render: (item) => (
        <Badge variant={item.resolved ? 'success' : 'danger'} dot>
          {item.resolved ? 'RESOLVED' : 'UNRESOLVED'}
        </Badge>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (item) => (
        <div className="flex justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            icon={<Eye className="h-4 w-4" />}
            onClick={() => { setSelectedAlert(item); detailsModalOpen ? null : setDetailsModalOpen(true); }}
            title="Inspect Coordinates"
          />
          {!item.resolved && (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="text-green-600 hover:bg-green-50"
                icon={<CheckCircle className="h-4 w-4" />}
                onClick={(e) => handleOpenResolve(e, item)}
                title="Resolve"
              />
              <Button
                variant="ghost"
                size="sm"
                className="text-content-secondary hover:bg-slate-50"
                icon={<Clock className="h-4 w-4" />}
                onClick={(e) => handleQuickDismiss(e, item.id)}
                title="Snooze"
              />
            </>
          )}
        </div>
      )
    }
  ];

  // Counters
  const criticalCount = alerts.filter(a => a.severity === 'critical' && !a.resolved).length;
  const mediumCount = alerts.filter(a => a.severity === 'medium' && !a.resolved).length;
  const resolvedCount = alerts.filter(a => a.resolved).length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Telematics Alerts</h1>
          <p className="text-sm text-content-secondary mt-0.5">Audit live speeding alarms, geofence breaches, and fuel drop triggers.</p>
        </div>
      </div>

      {/* Stats Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex items-center gap-3.5 p-4 border-l-4 border-l-red-500">
          <div className="p-2.5 rounded-lg bg-red-50 text-red-600">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] text-content-secondary uppercase block font-bold">Critical Anomalies</span>
            <span className="text-xl font-bold text-content">{criticalCount} Unresolved</span>
          </div>
        </Card>
        <Card className="flex items-center gap-3.5 p-4 border-l-4 border-l-amber-500">
          <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
            <Clock className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] text-content-secondary uppercase block font-bold">Medium Warnings</span>
            <span className="text-xl font-bold text-content">{mediumCount} Pending</span>
          </div>
        </Card>
        <Card className="flex items-center gap-3.5 p-4 border-l-4 border-l-green-500">
          <div className="p-2.5 rounded-lg bg-green-50 text-green-600">
            <CheckCircle className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] text-content-secondary uppercase block font-bold">Archived Audits</span>
            <span className="text-xl font-bold text-content">{resolvedCount} Completed</span>
          </div>
        </Card>
      </div>

      {/* Filter panel */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search truck plate, alarm type..."
          className="w-full md:max-w-xs"
        />

        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical Only</option>
            <option value="medium">Medium Warnings</option>
            <option value="low">Low Alarms</option>
          </select>
          <select
            value={resolvedFilter}
            onChange={(e) => setResolvedFilter(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="unresolved">Unresolved</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </Card>

      {/* Table grid */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={8} />
          </div>
        ) : err ? (
          <ErrorState
            title="Failed to Load Alerts"
            message={err.message || 'An error occurred.'}
            onRetry={loadAlerts}
          />
        ) : alerts.length === 0 ? (
          <EmptyState
            title="No Alarm Alerts Logged"
            description="Your fleet logs are clean. No warnings match current parameters."
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedAlerts}
              keyExtractor={(item) => item.id}
              onRowClick={(item) => { setSelectedAlert(item); setDetailsModalOpen(true); }}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={alerts.length}
                onPageChange={goToPage}
                onPageSizeChange={changePageSize}
              />
            </div>
          </>
        )}
      </Card>

      {/* Resolve Alert Modal */}
      <Modal
        open={resolveModalOpen}
        onClose={() => setResolveModalOpen(false)}
        title={`Resolve Alarm Ticket`}
        closable={!resolving}
        footer={
          <>
            <Button variant="outline" onClick={() => setResolveModalOpen(false)} disabled={resolving}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleConfirmResolve} loading={resolving}>
              Confirm Resolve
            </Button>
          </>
        }
      >
        {alertToResolve && (
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); handleConfirmResolve(); }}>
            <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl">
              <p className="text-xs text-content-secondary font-semibold">Alarm Trigger</p>
              <p className="text-sm font-semibold text-content mt-1">{alertToResolve.message}</p>
            </div>
            <Input
              label="Action Resolution Comments"
              placeholder="e.g. Spoke with driver; confirmed refueling receipt validation."
              value={resolutionComment}
              onChange={(e) => setResolutionComment(e.target.value)}
              required
            />
          </form>
        )}
      </Modal>

      {/* Details View Modal */}
      <Modal
        open={detailsModalOpen}
        onClose={() => setDetailsModalOpen(false)}
        title="Telematics Parameter Sheet"
        closable
        footer={
          selectedAlert && !selectedAlert.resolved && (
            <Button
              variant="primary"
              icon={<CheckCircle className="h-4 w-4" />}
              onClick={(e) => { setDetailsModalOpen(false); handleOpenResolve(e, selectedAlert); }}
            >
              Resolve Ticket
            </Button>
          )
        }
      >
        {selectedAlert && (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="font-bold text-content text-lg">{selectedAlert.truck_plate}</h4>
                <p className="text-xs text-content-secondary">{selectedAlert.type}</p>
              </div>
              <Badge variant={getSeverityVariant(selectedAlert.severity)}>
                {selectedAlert.severity.toUpperCase()}
              </Badge>
            </div>
            <div className="space-y-2.5 text-sm">
              <p className="flex justify-between"><span className="text-content-secondary">Alarm Details:</span> <span className="font-semibold text-content">{selectedAlert.message}</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Timestamp:</span> <span className="font-medium text-content">{new Date(selectedAlert.date).toLocaleString()}</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Audit Status:</span> <span className="font-bold">{selectedAlert.resolved ? 'RESOLVED' : 'ACTIVE TRIGGER'}</span></p>
              
              {selectedAlert.resolved && (
                <div className="p-3.5 bg-green-50/50 dark:bg-green-950/20 border border-green-100 dark:border-green-900/30 rounded-xl space-y-1 mt-2 text-green-950 dark:text-green-300">
                  <div className="flex items-center gap-1.5 font-semibold text-xs">
                    <MessageSquare className="h-4 w-4 text-green-600" />
                    Resolution Comments Note
                  </div>
                  <p className="text-xs italic opacity-95">{selectedAlert.resolutionComment || 'Logged as resolved.'}</p>
                </div>
              )}

              {/* Coordinates Map simulation */}
              <div className="pt-3 border-t border-border mt-3 flex items-center gap-2 text-content-secondary bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-xl">
                <MapPin className="h-5 w-5 text-rose-500 flex-shrink-0" />
                <span className="text-xs leading-relaxed">
                  GPS coordinate match: Latitude {selectedAlert.latitude || '24.985'}, Longitude {selectedAlert.longitude || '73.312'}. Velocity logging: {selectedAlert.speed || '0'} km/h.
                </span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
