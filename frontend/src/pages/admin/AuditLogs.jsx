import React, { useState, useEffect } from 'react';
import { ShieldCheck, Search, Calendar, FileText, Filter, Laptop, User } from 'lucide-react';
import { getAuditLogs } from '@/api/settingsApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { SearchBox } from '@/components/shared/SearchBox';
import { Pagination } from '@/components/ui/Pagination';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { usePagination } from '@/hooks/usePagination';

export default function AuditLogs() {
  const { success, error } = useToast();

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const loadAuditLogs = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getAuditLogs();
      let filtered = [...data];

      if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter(l =>
          l.user.toLowerCase().includes(q) ||
          l.action.toLowerCase().includes(q) ||
          l.details.toLowerCase().includes(q)
        );
      }

      if (startDate) {
        const start = new Date(startDate);
        filtered = filtered.filter(l => new Date(l.timestamp) >= start);
      }

      if (endDate) {
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        filtered = filtered.filter(l => new Date(l.timestamp) <= end);
      }

      setLogs(filtered);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve audit trail.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [search, startDate, endDate]);

  // Pagination
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: logs.length, initialPageSize: 10 });

  const paginatedLogs = logs.slice(startIndex, endIndex);

  const handleExportCSV = () => {
    try {
      const headers = ['Log ID', 'User', 'Action', 'Details', 'Timestamp', 'IP Address'];
      const rows = logs.map(l => [
        l.id,
        l.user,
        l.action,
        l.details,
        new Date(l.timestamp).toLocaleString(),
        l.ip
      ]);
      const csvContent = [headers.join(','), ...rows.map(r => r.map(cell => `"${cell}"`).join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fleetguard_audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      success('Export Completed', 'Audit logs successfully saved as CSV.');
    } catch (e) {
      error('Export Failed', 'An error occurred during compilation.');
    }
  };

  const columns = [
    {
      key: 'id',
      label: 'Log ID',
      render: (item) => <span className="font-mono text-xs text-content-secondary">{item.id}</span>
    },
    {
      key: 'user',
      label: 'Operator / Administrator',
      render: (item) => (
        <span className="font-semibold text-content flex items-center gap-1.5">
          <User className="h-3.5 w-3.5 text-content-muted" />
          {item.user}
        </span>
      )
    },
    {
      key: 'action',
      label: 'System Action',
      render: (item) => <span className="font-semibold text-brand-600">{item.action}</span>
    },
    {
      key: 'details',
      label: 'Operation Details',
      className: 'w-[40%]',
      render: (item) => <span className="text-xs text-content-secondary leading-relaxed block">{item.details}</span>
    },
    {
      key: 'timestamp',
      label: 'Execution Time',
      render: (item) => <span className="text-xs text-content-secondary">{new Date(item.timestamp).toLocaleString()}</span>
    },
    {
      key: 'ip',
      label: 'IP Address',
      render: (item) => (
        <span className="text-xs text-content-secondary flex items-center gap-1">
          <Laptop className="h-3 w-3 text-content-muted" />
          {item.ip}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-brand-600" />
            Security Audit Trail
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">Audit system events, configuration changes, and settings history.</p>
        </div>
        <Button
          variant="outline"
          icon={<FileText className="h-4 w-4 text-emerald-600" />}
          onClick={handleExportCSV}
          disabled={logs.length === 0}
        >
          Export CSV
        </Button>
      </div>

      {/* Customizable Filters */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search user, action, detail logs..."
          className="w-full md:max-w-xs"
        />

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-content-secondary text-sm font-semibold">
            <Filter className="h-4 w-4 text-brand-600" />
            Time Bounds:
          </div>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
          />
          <span className="text-xs text-content-muted">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
          />
        </div>
      </Card>

      {/* Table grid */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={6} />
          </div>
        ) : err ? (
          <ErrorState
            title="Failed to Load Audit Logs"
            message={err.message || 'An error occurred.'}
            onRetry={loadAuditLogs}
          />
        ) : logs.length === 0 ? (
          <EmptyState
            title="Audit Trail is Empty"
            description="No system security logs match current filters."
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedLogs}
              keyExtractor={(item) => item.id}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={logs.length}
                onPageChange={goToPage}
                onPageSizeChange={changePageSize}
              />
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
