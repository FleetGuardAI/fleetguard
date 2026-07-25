import React, { useState, useEffect } from 'react';
import { Disc, Eye, Search, Filter, RefreshCw, PackageCheck } from 'lucide-react';
import { getTyres } from '@/api/tyreApi';
import { getVehicles } from '@/api/vehicleApi';
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

export default function TyreList() {
  const { error } = useToast();
  const [tyres, setTyres] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Modal
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedTyre, setSelectedTyre] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [tData, vData] = await Promise.all([
        getTyres({ search, status: statusFilter }),
        getVehicles()
      ]);
      setTyres(tData);
      setVehicles(vData);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve tyre records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [search, statusFilter]);

  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: tyres.length, initialPageSize: 10 });

  const paginatedTyres = tyres.slice(startIndex, endIndex);

  const vehicleMap = React.useMemo(() => {
    const map = {};
    vehicles.forEach(v => {
      map[v.id] = v.registration_number || v.license_plate;
    });
    return map;
  }, [vehicles]);

  const handleViewTyre = (tyre) => {
    setSelectedTyre(tyre);
    setDetailsModalOpen(true);
  };

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'installed':
      case 'in_use':
      case 'mounted':
        return <Badge variant="success" dot>MOUNTED</Badge>;
      case 'available':
      case 'in_stock':
      case 'storage':
        return <Badge variant="info" dot>IN STOCK</Badge>;
      case 'repaired':
      case 'retreaded':
        return <Badge variant="warning" dot>SERVICEABLE</Badge>;
      case 'retired':
      case 'scrapped':
        return <Badge variant="danger" dot>RETIRED</Badge>;
      default:
        return <Badge variant="neutral">{status?.toUpperCase() || 'UNKNOWN'}</Badge>;
    }
  };

  const columns = [
    {
      key: 'serial_number',
      label: 'Serial Number',
      render: (item) => <span className="font-mono text-xs font-bold text-content">{item.serial_number}</span>
    },
    {
      key: 'brand',
      label: 'Brand / Manufacturer',
      render: (item) => (
        <span className="font-medium text-content">
          {[item.manufacturer, item.brand].filter(Boolean).join(' ') || item.manufacturer || item.brand || 'N/A'}
        </span>
      )
    },
    {
      key: 'size',
      label: 'Size / Model',
      render: (item) => <span>{[item.size, item.model].filter(Boolean).join(' - ') || 'N/A'}</span>
    },
    {
      key: 'current_vehicle_id',
      label: 'Mounted Vehicle',
      render: (item) => (
        <span className="text-xs font-semibold">
          {item.current_vehicle_id ? (vehicleMap[item.current_vehicle_id] || `Vehicle ID: ${item.current_vehicle_id}`) : 'In Storage'}
        </span>
      )
    },
    {
      key: 'current_position',
      label: 'Position',
      render: (item) => <span className="text-xs text-content-secondary">{item.current_position || 'Unassigned'}</span>
    },
    {
      key: 'current_status',
      label: 'Status',
      render: (item) => getStatusBadge(item.current_status)
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
            onClick={() => handleViewTyre(item)}
          />
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Tyre Management</h1>
          <p className="text-sm text-content-secondary mt-0.5">Track fleet tyre inventory, vehicle mounting positions, and lifecycle records.</p>
        </div>
        <Button
          variant="outline"
          icon={<RefreshCw className="h-4 w-4" />}
          onClick={loadData}
        >
          Refresh
        </Button>
      </div>

      {/* Filter Bar */}
      <Card className="p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search serial number, brand, manufacturer..."
          className="w-full md:max-w-xs"
        />

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none w-full md:w-48"
          >
            <option value="all">All Statuses</option>
            <option value="installed">Mounted / Installed</option>
            <option value="available">In Stock / Available</option>
            <option value="retired">Retired / Scrapped</option>
          </select>
        </div>
      </Card>

      {/* Main Table */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={7} />
          </div>
        ) : err ? (
          <ErrorState
            title="Failed to Load Tyre Records"
            message={err.message || 'An error occurred while communicating with the backend.'}
            onRetry={loadData}
          />
        ) : tyres.length === 0 ? (
          <EmptyState
            title="No Tyre Records Found"
            description={search ? "No tyres matched your query criteria." : "No tyre assets recorded in the system."}
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedTyres}
              keyExtractor={(item) => item.id}
              onRowClick={(item) => handleViewTyre(item)}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={tyres.length}
                onPageChange={goToPage}
                onPageSizeChange={changePageSize}
              />
            </div>
          </>
        )}
      </Card>

      {/* Details View Modal */}
      <Modal
        open={detailsModalOpen}
        onClose={() => setDetailsModalOpen(false)}
        title="Tyre Asset Specification & History"
        closable
      >
        {selectedTyre && (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="font-bold text-content text-lg font-mono">{selectedTyre.serial_number}</h4>
                <p className="text-xs text-content-secondary">
                  {[selectedTyre.manufacturer, selectedTyre.brand, selectedTyre.size].filter(Boolean).join(' | ') || 'Tyre Asset'}
                </p>
              </div>
              {getStatusBadge(selectedTyre.current_status)}
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-xs text-content-secondary block">Mounted Vehicle</span>
                <span className="font-semibold text-content">
                  {selectedTyre.current_vehicle_id ? (vehicleMap[selectedTyre.current_vehicle_id] || `Vehicle ID: ${selectedTyre.current_vehicle_id}`) : 'Unmounted (Storage)'}
                </span>
              </div>
              <div>
                <span className="text-xs text-content-secondary block">Mount Position</span>
                <span className="font-semibold text-content">{selectedTyre.current_position || 'N/A'}</span>
              </div>
              <div>
                <span className="text-xs text-content-secondary block">Model</span>
                <span className="font-semibold text-content">{selectedTyre.model || 'N/A'}</span>
              </div>
              <div>
                <span className="text-xs text-content-secondary block">Size / Spec</span>
                <span className="font-semibold text-content">{selectedTyre.size || 'N/A'}</span>
              </div>
            </div>

            {/* Lifecycle Timeline */}
            <div className="pt-3 border-t border-border">
              <h5 className="text-xs font-bold text-content uppercase tracking-wider mb-3">Lifecycle Event Log</h5>
              {selectedTyre.lifecycle_records && selectedTyre.lifecycle_records.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {selectedTyre.lifecycle_records.map((rec) => (
                    <div key={rec.id} className="p-2.5 rounded-lg bg-surface-secondary text-xs flex justify-between items-center">
                      <div>
                        <span className="font-semibold text-content block">{rec.event_category}</span>
                        <span className="text-content-muted">{new Date(rec.performed_at).toLocaleString()}</span>
                      </div>
                      <Badge variant="neutral">{rec.origin_type || 'SYSTEM'}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-content-muted italic">No lifecycle events recorded for this tyre.</p>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
