import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, Route, MapPin, Calendar, Clock, CheckCircle } from 'lucide-react';
import { getTrips } from '@/api/tripApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SearchBox } from '@/components/shared/SearchBox';
import { Pagination } from '@/components/ui/Pagination';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { usePagination } from '@/hooks/usePagination';
import { cn } from '@/utils/cn';

export default function TripList() {
  const navigate = useNavigate();
  const { error } = useToast();

  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState('all'); // all, on-trip, completed, scheduled

  const loadTrips = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getTrips({
        search,
        status: activeTab !== 'all' ? activeTab : undefined
      });
      setTrips(data);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve dispatch trips.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrips();
  }, [search, activeTab]);

  // Pagination hook
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: trips.length, initialPageSize: 10 });

  const paginatedTrips = trips.slice(startIndex, endIndex);

  const getStatusVariant = (status) => {
    if (status === 'on-trip') return 'brand';
    if (status === 'completed') return 'success';
    if (status === 'scheduled') return 'warning';
    return 'neutral';
  };

  const getStatusLabel = (status) => {
    if (status === 'on-trip') return 'ON TRIP';
    if (status === 'completed') return 'COMPLETED';
    if (status === 'scheduled') return 'SCHEDULED';
    return status.toUpperCase();
  };

  const columns = [
    {
      key: 'route_name',
      label: 'Route / Trip ID',
      render: (t) => (
        <div>
          <span className="font-semibold text-content block">{t.route_name}</span>
          <span className="text-xs text-content-secondary flex items-center gap-1 mt-0.5">
            <MapPin className="h-3 w-3 text-content-muted" />
            {t.start_point.split(',')[0]} → {t.end_point.split(',')[0]}
          </span>
        </div>
      )
    },
    {
      key: 'truck_plate',
      label: 'Vehicle',
      render: (t) => <span className="font-mono text-xs bg-surface-secondary px-2 py-1 rounded border border-border">{t.truck_plate}</span>
    },
    {
      key: 'driver_name',
      label: 'Driver'
    },
    {
      key: 'dates',
      label: 'Dispatch / Delivery',
      render: (t) => (
        <div className="text-xs text-content-secondary space-y-0.5">
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3 text-content-muted" />
            {new Date(t.start_date).toLocaleDateString()}
          </div>
          {t.end_date ? (
            <div className="flex items-center gap-1 text-green-600">
              <CheckCircle className="h-3 w-3" />
              {new Date(t.end_date).toLocaleDateString()}
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3 text-content-muted" />
              Est: {new Date(t.expected_delivery).toLocaleDateString()}
            </div>
          )}
        </div>
      )
    },
    {
      key: 'progress',
      label: 'Progress',
      render: (t) => (
        <div className="w-28 space-y-1">
          <div className="flex justify-between text-[10px] font-medium text-content-secondary">
            <span>{t.progress}%</span>
            <span>{t.distance_km} km</span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div className={cn(
              "h-full transition-all duration-300",
              t.status === 'completed' ? 'bg-green-600' : 'bg-brand-600'
            )} style={{ width: `${t.progress}%` }} />
          </div>
        </div>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (t) => (
        <Badge variant={getStatusVariant(t.status)}>
          {getStatusLabel(t.status)}
        </Badge>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (t) => (
        <div className="flex justify-end" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            icon={<Eye className="h-4 w-4" />}
            onClick={() => navigate(`/dashboard/trips/${t.id}`)}
          />
        </div>
      )
    }
  ];

  if (err) {
    return (
      <ErrorState
        title="Failed to Load Trips"
        message={err.message || 'An error occurred.'}
        onRetry={loadTrips}
      />
    );
  }

  const tabs = [
    { id: 'all', label: 'All Trips' },
    { id: 'on-trip', label: 'Active' },
    { id: 'scheduled', label: 'Scheduled' },
    { id: 'completed', label: 'Completed' }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Dispatch Trips</h1>
          <p className="text-sm text-content-secondary mt-0.5">Plan, dispatch, and track cargo routes across the country.</p>
        </div>
        <Button
          variant="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/trips/new')}
        >
          Dispatch Cargo
        </Button>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
              activeTab === tab.id
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-content-secondary hover:text-content"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters Toolbar */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search route name, truck plate, driver..."
          className="w-full md:max-w-xs"
        />
      </Card>

      {/* Main Table */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={6} />
          </div>
        ) : trips.length === 0 ? (
          <EmptyState
            title="No Trips Recorded"
            description="There are no dispatches matching the filter selections."
            actionLabel="Dispatch Cargo"
            onAction={() => navigate('/dashboard/trips/new')}
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedTrips}
              keyExtractor={(t) => t.id}
              onRowClick={(t) => navigate(`/dashboard/trips/${t.id}`)}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={trips.length}
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
