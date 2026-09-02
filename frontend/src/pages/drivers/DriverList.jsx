import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit2, Eye, Trash2, Star, ShieldAlert, QrCode, UserPlus, Smartphone } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import api from '@/api/client';
import { getDrivers, deleteDriver } from '@/api/driverApi';
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
import { Dropdown } from '@/components/ui/Dropdown';
import { QRCodeSVG } from 'qrcode.react';
import api from '@/api/client';

export default function DriverList() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [driverToDelete, setDriverToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // QR Modal state
  const [qrModalOpen, setQrModalOpen] = useState(false);
  const [qrScanning, setQrScanning] = useState(false);
  const [qrInvite, setQrInvite] = useState(null);
  const [qrLoading, setQrLoading] = useState(false);

  const loadDrivers = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getDrivers({ search, status: statusFilter !== 'all' ? statusFilter : undefined });
      setDrivers(data || []);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve drivers directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDrivers();
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
  } = usePagination({ totalItems: drivers.length, initialPageSize: 10 });

  const paginatedDrivers = drivers.slice(startIndex, endIndex);

  const handleDeleteClick = (e, driver) => {
    e.stopPropagation();
    setDriverToDelete(driver);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!driverToDelete) return;
    setDeleting(true);
    try {
      await deleteDriver(driverToDelete.id);
      setDrivers(prev => prev.filter(d => d.id !== driverToDelete.id));
      success('Driver Removed', `Successfully archived profile for ${driverToDelete.name || 'Driver'}.`);
      setDeleteModalOpen(false);
    } catch (e) {
      error('Delete Error', e.message || 'Failed to remove driver.');
    } finally {
      setDeleting(false);
      setDriverToDelete(null);
    }
  };

  const handleSimulateQrScan = () => {
    // We are keeping this for testing the UI updates, but the real onboarding is done by the driver app.
    loadDrivers();
    success('Drivers Refreshed', 'Checking if any new drivers have joined...');
  };

  const handleOpenQrModal = async () => {
    setQrModalOpen(true);
    setQrLoading(true);
    try {
      const invite = await api.fleet.createInvite({ label: 'Dashboard Invite', max_uses: 1 });
      setQrInvite(invite);
    } catch (e) {
      error('Invite Error', 'Failed to generate QR code invite.');
      setQrModalOpen(false);
    } finally {
      setQrLoading(false);
    }
  };

  const getVerificationVariant = (status) => {
    switch (status) {
      case 'APPROVED': return 'success';
      case 'PENDING_APPROVAL': return 'warning';
      case 'PENDING_DOCUMENTS': return 'info';
      case 'REJECTED': return 'danger';
      default: return 'neutral';
    }
  };

  const getVerificationLabel = (status) => {
    switch (status) {
      case 'APPROVED': return 'Approved';
      case 'PENDING_APPROVAL': return 'Pending Approval';
      case 'PENDING_DOCUMENTS': return 'Pending Docs';
      case 'REJECTED': return 'Rejected';
      default: return 'Not Started';
    }
  };

  const columns = [
    {
      key: 'name',
      label: 'Driver Name',
      sortable: true,
      render: (d) => <span className="font-semibold text-content">{d.name || `Driver ID: ${d.id}`}</span>
    },
    {
      key: 'phone_number',
      label: 'Phone Number',
      render: (d) => <span>{d.phone_number || 'N/A'}</span>
    },
    {
      key: 'age',
      label: 'Age',
      sortable: true,
      render: (d) => <span>{d.age ?? 'N/A'}</span>
    },
    {
      key: 'verification_status',
      label: 'Verification',
      sortable: true,
      render: (d) => (
        <Badge variant={getVerificationVariant(d.verification_status)}>
          {getVerificationLabel(d.verification_status)}
        </Badge>
      )
    },
    {
      key: 'assigned_truck',
      label: 'Assigned Truck',
      render: (d) => (
        <span className={`text-sm font-mono ${d.assigned_truck ? 'text-content font-semibold' : 'text-content-muted'}`}>
          {d.assigned_truck || 'Unassigned'}
        </span>
      )
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (d) => {
        const isActive = d.status === 'active' || d.is_active === true;
        return (
          <Badge variant={isActive ? 'success' : 'neutral'} dot>
            {isActive ? 'Active' : 'Inactive'}
          </Badge>
        );
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (d) => (
        <div className="flex justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            icon={<Eye className="h-4 w-4" />}
            onClick={() => navigate(`/dashboard/drivers/${d.id}`)}
            title="View Profile"
          />
          <Button
            variant="ghost"
            size="sm"
            icon={<Edit2 className="h-4 w-4" />}
            onClick={() => navigate(`/dashboard/drivers/${d.id}/edit`)}
            title="Edit"
          />
          <Button
            variant="ghost"
            size="sm"
            className="text-red-500 hover:text-red-600 hover:bg-red-50"
            icon={<Trash2 className="h-4 w-4" />}
            onClick={(e) => handleDeleteClick(e, d)}
            title="Delete"
          />
        </div>
      )
    }
  ];

  if (err) {
    return (
      <ErrorState
        title="Failed to Load Drivers"
        message={err.message || 'An error occurred.'}
        onRetry={loadDrivers}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Drivers Directory</h1>
          <p className="text-sm text-content-secondary mt-0.5">Manage operator credentials, safety ratings, and advanced advances.</p>
        </div>
        <Dropdown
          align="right"
          trigger={
            <Button variant="primary" icon={<Plus className="h-4 w-4" />}>
              Add Driver
            </Button>
          }
          items={[
            {
              label: 'Scan QR Code',
              icon: <QrCode className="h-4 w-4" />,
              onClick: handleOpenQrModal
            },
            {
              label: 'Add Driver Manually',
              icon: <UserPlus className="h-4 w-4" />,
              onClick: () => navigate('/dashboard/drivers/new')
            }
          ]}
        />
      </div>

      {/* Filters Card */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search driver name, phone number..."
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

      {/* Main Drivers Table */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={6} />
          </div>
        ) : drivers.length === 0 ? (
          <EmptyState
            title="No Drivers Found"
            description="Try modifying your search or add a new driver profile to get started."
            actionLabel="Add Driver"
            onAction={() => navigate('/dashboard/drivers/new')}
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedDrivers}
              keyExtractor={(d) => d.id}
              onRowClick={(d) => navigate(`/dashboard/drivers/${d.id}`)}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={drivers.length}
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
        title="Delete Driver Profile"
        description="Are you sure you want to remove this driver profile? This action will archive safety ratings."
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
        {driverToDelete && (
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-xl">
            <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-950">
                Removing {driverToDelete.name || 'Driver'}
              </p>
              <p className="text-xs text-red-700">
                Phone: {driverToDelete.phone_number || 'N/A'} • Safety Score: {driverToDelete.risk_score != null ? `${driverToDelete.risk_score}/100` : 'N/A'}
              </p>
            </div>
          </div>
        )}
      </Modal>

      {/* QR Code Invitation Modal */}
      <Modal
        open={qrModalOpen}
        onClose={() => setQrModalOpen(false)}
        title="Fleet Invite QR Code"
        description="Ask the driver to scan this unique QR code with their mobile device to instantly join your fleet."
        footer={
          <div className="w-full flex justify-end items-center">
            <Button variant="outline" onClick={() => setQrModalOpen(false)} disabled={qrScanning}>
              Close
            </Button>
            <Button variant="primary" icon={<Smartphone className="w-4 h-4" />} onClick={handleSimulateQrScan} loading={qrScanning}>
              Refresh Driver List
            </Button>
          </div>
        }
      >
        <div className="flex flex-col items-center justify-center py-6 space-y-6">
          <div className="p-4 bg-white rounded-2xl shadow-sm border border-border">
            {/* Real QR Code */}
            <div className="w-48 h-48 bg-white flex items-center justify-center rounded-xl border-2 border-brand-200 border-dashed relative">
              {qrLoading ? (
                 <div className="animate-pulse w-full h-full bg-slate-100 rounded-xl"></div>
              ) : qrInvite ? (
                 <QRCodeSVG 
                    value={qrInvite.qr_data} 
                    size={160}
                    level="H"
                    includeMargin={false}
                    fgColor="#0f172a" 
                 />
              ) : (
                 <QrCode className="w-24 h-24 text-brand-600 opacity-60" />
              )}
            </div>
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-content">
              {qrLoading ? 'Generating Invite...' : qrInvite ? `Fleet ID: FG-CORP-${qrInvite.company_id}` : 'Error'}
            </p>
            <p className="text-xs text-content-muted max-w-[250px] mx-auto">
              Scanning this code binds the driver to your fleet and syncs their telematics data.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
