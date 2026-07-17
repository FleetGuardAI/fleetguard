import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit2, Eye, Trash2, ShieldAlert } from 'lucide-react';
import { getVehicles } from '@/api/vehicleApi';
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
import { Modal } from '@/components/ui/Modal';

export default function VehicleList() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filter states
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [vehicleToDelete, setVehicleToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadVehicles = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getVehicles({ search, status: statusFilter !== 'all' ? statusFilter : undefined });
      setVehicles(data);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve vehicles list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVehicles();
  }, [search, statusFilter]);

  // Pagination hook
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: vehicles.length, initialPageSize: 10 });

  // Paginated vehicles
  const paginatedVehicles = vehicles.slice(startIndex, endIndex);

  const handleDeleteClick = (e, vehicle) => {
    e.stopPropagation();
    setVehicleToDelete(vehicle);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!vehicleToDelete) return;
    setDeleting(true);
    try {
      // Mock deletion
      await new Promise(resolve => setTimeout(resolve, 500));
      setVehicles(prev => prev.filter(v => v.id !== vehicleToDelete.id));
      success('Vehicle Deleted', `Successfully removed vehicle ${vehicleToDelete.license_plate}.`);
      setDeleteModalOpen(false);
    } catch (e) {
      error('Delete Error', 'Failed to delete vehicle.');
    } finally {
      setDeleting(false);
      setVehicleToDelete(null);
    }
  };

  const columns = [
    {
      key: 'license_plate',
      label: 'License Plate',
      sortable: true,
      render: (v) => <span className="font-semibold font-mono text-content">{v.license_plate}</span>
    },
    {
      key: 'make_model',
      label: 'Make & Model',
      render: (v) => <span>{v.make} {v.model}</span>
    },
    {
      key: 'year',
      label: 'Year',
      sortable: true
    },
    {
      key: 'tank_capacity',
      label: 'Capacity (L)',
      render: (v) => <span>{v.tank_capacity} L</span>
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (v) => (
        <Badge variant={v.is_active ? 'success' : 'neutral'} dot>
          {v.is_active ? 'Active' : 'Inactive'}
        </Badge>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (v) => (
        <div className="flex justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            icon={<Eye className="h-4 w-4" />}
            onClick={() => navigate(`/dashboard/vehicles/${v.id}`)}
            title="View Details"
          />
          <Button
            variant="ghost"
            size="sm"
            icon={<Edit2 className="h-4 w-4" />}
            onClick={() => navigate(`/dashboard/vehicles/${v.id}/edit`)}
            title="Edit"
          />
          <Button
            variant="ghost"
            size="sm"
            className="text-red-500 hover:text-red-600 hover:bg-red-50"
            icon={<Trash2 className="h-4 w-4" />}
            onClick={(e) => handleDeleteClick(e, v)}
            title="Delete"
          />
        </div>
      )
    }
  ];

  if (err) {
    return (
      <ErrorState
        title="Failed to Load Vehicles"
        message={err.message || 'An error occurred.'}
        onRetry={loadVehicles}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Vehicles Management</h1>
          <p className="text-sm text-content-secondary mt-0.5">Maintain, monitor, and configure fleet trucks.</p>
        </div>
        <Button
          variant="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/vehicles/new')}
        >
          Add Vehicle
        </Button>
      </div>

      {/* Filters Toolbar */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search plate, manufacturer, model..."
          className="w-full md:max-w-xs"
        />

        <div className="flex gap-2 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
      </Card>

      {/* Main List Table */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={5} />
          </div>
        ) : vehicles.length === 0 ? (
          <EmptyState
            title="No Vehicles Found"
            description="Try modifying your search or add a new vehicle profile to get started."
            actionLabel="Add Vehicle"
            onAction={() => navigate('/dashboard/vehicles/new')}
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedVehicles}
              keyExtractor={(v) => v.id}
              onRowClick={(v) => navigate(`/dashboard/vehicles/${v.id}`)}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={vehicles.length}
                onPageChange={goToPage}
                onPageSizeChange={changePageSize}
              />
            </div>
          </>
        )}
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal
        open={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Vehicle Profile"
        description="Are you sure you want to remove this vehicle? This action cannot be undone."
        closable={!deleting}
        footer={
          <>
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleConfirmDelete} loading={deleting}>
              Delete
            </Button>
          </>
        }
      >
        {vehicleToDelete && (
          <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 rounded-xl">
            <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-950 dark:text-red-400">
                Removing {vehicleToDelete.license_plate}
              </p>
              <p className="text-xs text-red-700 dark:text-red-300">
                {vehicleToDelete.make} {vehicleToDelete.model} ({vehicleToDelete.year})
              </p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
