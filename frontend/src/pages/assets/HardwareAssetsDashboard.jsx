import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu,
  Eye,
  RefreshCw,
  Plus,
  Radio,
  Server,
  Truck,
  Edit,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  MoreVertical,
  ExternalLink,
  MapPin,
  Clock,
  Wifi,
  WifiOff,
  Filter,
  SlidersHorizontal,
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Table } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { SearchBox } from '@/components/shared/SearchBox';
import { useToast } from '@/components/ui/Toast';
import { getVehicles } from '@/api/vehicleApi';
import {
  getHardwareSummaryStats,
  getHardwareDevices,
  testHardwareConnection,
  disconnectHardwareDevice,
  removeHardwareDevice,
} from '@/api/assetApi';

import HardwareSummaryCards from './HardwareSummaryCards';
import AddDeviceWizardModal from './AddDeviceWizardModal';
import ReassignVehicleModal from './ReassignVehicleModal';
import EditDeviceModal from './EditDeviceModal';
import ProviderManagementModal from './ProviderManagementModal';

export default function HardwareAssetsDashboard() {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();

  // Summary Metrics State
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);

  // Table Data State
  const [devices, setDevices] = useState([]);
  const [totalDevices, setTotalDevices] = useState(0);
  const [tableLoading, setTableLoading] = useState(true);
  const [tableError, setTableError] = useState(null);

  // Vehicles for assignment lookup
  const [vehicles, setVehicles] = useState([]);

  // Search & Filters
  const [search, setSearch] = useState('');
  const [manufacturerFilter, setManufacturerFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [assignmentFilter, setAssignmentFilter] = useState('all');

  // Sorting & Pagination
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDesc, setSortDesc] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Modals
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [providersModalOpen, setProvidersModalOpen] = useState(false);
  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);

  // Action status tracker (for row-level spinning)
  const [testingId, setTestingId] = useState(null);

  // Load summary statistics
  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const data = await getHardwareSummaryStats();
      setSummary(data);
    } catch (err) {
      console.warn('Failed to load summary stats:', err);
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  // Load devices table
  const loadDevices = useCallback(async () => {
    setTableLoading(true);
    setTableError(null);
    try {
      const params = {
        search: search.trim() || undefined,
        manufacturer: manufacturerFilter || undefined,
        connection_status: statusFilter || undefined,
        gps_provider: providerFilter || undefined,
        vehicle_assignment: assignmentFilter,
        sort_by: sortBy,
        sort_desc: sortDesc,
        page: page,
        page_size: pageSize,
      };
      const res = await getHardwareDevices(params);
      setDevices(res.items || []);
      setTotalDevices(res.total || 0);
    } catch (err) {
      console.error(err);
      setTableError(err);
      toastError('Load Error', 'Unable to retrieve hardware telematics devices.');
    } finally {
      setTableLoading(false);
    }
  }, [search, manufacturerFilter, statusFilter, providerFilter, assignmentFilter, sortBy, sortDesc, page, pageSize]);

  // Initial load
  useEffect(() => {
    loadSummary();
    getVehicles().then(v => setVehicles(v || [])).catch(() => {});
  }, [loadSummary]);

  useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  // Refresh all
  const handleRefreshAll = () => {
    loadSummary();
    loadDevices();
  };

  // Test Connection
  const handleTestConnection = async (e, dev) => {
    e.stopPropagation();
    setTestingId(dev.id);
    try {
      const res = await testHardwareConnection(dev.id);
      if (res.connected) {
        success('Device Online', `${dev.device_name} responded. Latency: ${res.latency_ms}ms.`);
      } else {
        toastError('Device Offline', res.message || 'No response received from device.');
      }
      handleRefreshAll();
    } catch (err) {
      toastError('Test Failed', err.message);
    } finally {
      setTestingId(null);
    }
  };

  // Disconnect Device to Storage
  const handleDisconnect = async (e, dev) => {
    e.stopPropagation();
    if (!window.confirm(`Unassign ${dev.device_name} from vehicle and move to storage inventory?`)) return;
    try {
      await disconnectHardwareDevice(dev.id);
      success('Device Disconnected', `${dev.device_name} unassigned and moved to storage.`);
      handleRefreshAll();
    } catch (err) {
      toastError('Disconnect Failed', err.message);
    }
  };

  // Remove Device Permanently
  const handleRemove = async (e, dev) => {
    e.stopPropagation();
    if (!window.confirm(`Retire ${dev.device_name} permanently?`)) return;
    try {
      await removeHardwareDevice(dev.id);
      success('Device Retired', `${dev.device_name} has been removed from active telematics service.`);
      handleRefreshAll();
    } catch (err) {
      toastError('Removal Failed', err.message);
    }
  };

  // Status Badge Component
  const renderStatusBadge = (dev) => {
    const isConn = dev.connection_status === 'CONNECTED';
    const isDisc = dev.connection_status === 'DISCONNECTED';
    const isPend = dev.connection_status === 'PENDING';

    return (
      <div className="flex flex-col gap-1">
        <Badge
          variant={isConn ? 'success' : isDisc ? 'warning' : isPend ? 'info' : 'neutral'}
          size="sm"
          dot
        >
          {dev.connection_status}
        </Badge>
        {dev.is_stale && (
          <span className="text-[10px] text-amber-600 font-medium">Stale data</span>
        )}
      </div>
    );
  };

  const totalPages = Math.ceil(totalDevices / pageSize) || 1;

  // Table Columns Definition
  const columns = [
    {
      key: 'device_name',
      label: 'Device Details',
      render: (item) => (
        <div>
          <span className="font-semibold text-content block text-xs md:text-sm hover:text-brand-600 cursor-pointer">
            {item.device_name}
          </span>
          <span className="font-mono text-[11px] text-content-muted">
            {item.business_id}
          </span>
        </div>
      ),
    },
    {
      key: 'imei',
      label: 'IMEI / Identifier',
      render: (item) => (
        <span className="font-mono text-xs text-content font-medium select-all">
          {item.imei || item.serial_number || 'N/A'}
        </span>
      ),
    },
    {
      key: 'manufacturer',
      label: 'Hardware Specs',
      render: (item) => (
        <div className="text-xs">
          <span className="font-medium text-content block">
            {[item.manufacturer, item.model].filter(Boolean).join(' ') || 'Generic Tracker'}
          </span>
          <span className="text-[10px] font-mono text-brand-700 bg-brand-50 px-1 py-0.5 rounded">
            {item.protocol || 'DEFAULT'}
          </span>
        </div>
      ),
    },
    {
      key: 'vehicle_registration',
      label: 'Assigned Vehicle',
      render: (item) => (
        item.vehicle_registration ? (
          <div className="flex items-center gap-1.5">
            <Truck className="w-3.5 h-3.5 text-brand-600 shrink-0" />
            <span className="font-mono text-xs font-bold text-content">
              {item.vehicle_registration}
            </span>
          </div>
        ) : (
          <Badge variant="neutral" size="sm">UNASSIGNED</Badge>
        )
      ),
    },
    {
      key: 'gps_provider',
      label: 'GPS Provider',
      render: (item) => (
        <span className="text-xs text-content-secondary">
          {item.gps_provider || 'Direct TCP'}
        </span>
      ),
    },
    {
      key: 'connection_status',
      label: 'Status',
      render: (item) => renderStatusBadge(item),
    },
    {
      key: 'last_communication_at',
      label: 'Last Communication',
      render: (item) => (
        <div className="text-xs text-content-secondary">
          {item.last_communication_at ? (
            <div>
              <span className="block font-medium">
                {new Date(item.last_communication_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <span className="text-[10px] text-content-muted">
                {new Date(item.last_communication_at).toLocaleDateString()}
              </span>
            </div>
          ) : (
            <span className="text-content-muted italic">Never</span>
          )}
        </div>
      ),
    },
    {
      key: 'last_known_location',
      label: 'Last Location',
      render: (item) => (
        <div className="text-xs max-w-[180px]">
          {item.last_known_lat !== null && item.last_known_lng !== null ? (
            <div>
              <span className="text-content-secondary line-clamp-1 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-brand-600 shrink-0" />
                {item.last_known_address || `${item.last_known_lat.toFixed(4)}, ${item.last_known_lng.toFixed(4)}`}
              </span>
              <span className="text-[10px] text-content-muted font-medium">
                {Math.round(item.last_known_speed || 0)} km/h • {item.last_known_ignition ? 'Ignition ON' : 'Ignition OFF'}
              </span>
            </div>
          ) : (
            <span className="text-content-muted italic">No fix yet</span>
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (item) => (
        <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
          {/* Test Ping Button */}
          <button
            title="Test Connection"
            onClick={(e) => handleTestConnection(e, item)}
            disabled={testingId === item.id}
            className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-muted hover:text-green-600 transition-colors"
          >
            <Radio className={`w-4 h-4 ${testingId === item.id ? 'animate-pulse text-green-600' : ''}`} />
          </button>

          {/* View Details */}
          <button
            title="View Live Details & Playback"
            onClick={() => navigate(`/dashboard/assets/${item.id}`)}
            className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-muted hover:text-brand-600 transition-colors"
          >
            <Eye className="w-4 h-4" />
          </button>

          {/* Reassign Vehicle */}
          <button
            title="Reassign Vehicle"
            onClick={() => {
              setSelectedDevice(item);
              setReassignModalOpen(true);
            }}
            className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-muted hover:text-blue-600 transition-colors"
          >
            <Truck className="w-4 h-4" />
          </button>

          {/* Edit Device */}
          <button
            title="Edit Parameters"
            onClick={() => {
              setSelectedDevice(item);
              setEditModalOpen(true);
            }}
            className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-muted hover:text-content transition-colors"
          >
            <Edit className="w-4 h-4" />
          </button>

          {/* Unassign / Disconnect */}
          {item.current_vehicle_id && (
            <button
              title="Disconnect to Storage"
              onClick={(e) => handleDisconnect(e, item)}
              className="p-1.5 rounded-lg hover:bg-amber-50 text-content-muted hover:text-amber-600 transition-colors"
            >
              <WifiOff className="w-4 h-4" />
            </button>
          )}

          {/* Remove / Retire */}
          <button
            title="Retire Device"
            onClick={(e) => handleRemove(e, item)}
            className="p-1.5 rounded-lg hover:bg-red-50 text-content-muted hover:text-red-500 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content tracking-tight">Hardware Assets & Telematics</h1>
          <p className="text-xs sm:text-sm text-content-secondary mt-0.5">
            Universal GPS gateway management, multi-vendor protocols, live tracking, and device diagnostics.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setProvidersModalOpen(true)}
            icon={<Server className="w-4 h-4" />}
          >
            Manage Providers
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshAll}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setAddModalOpen(true)}
            icon={<Plus className="w-4 h-4" />}
          >
            Add Device
          </Button>
        </div>
      </div>

      {/* Summary KPI Cards from real backend data */}
      <HardwareSummaryCards summary={summary} loading={summaryLoading} />

      {/* Filter and Search Bar */}
      <Card className="p-4 border border-border shadow-card bg-surface flex flex-col lg:flex-row items-center justify-between gap-3">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search by device name, IMEI, or vehicle registration..."
          className="w-full lg:max-w-sm"
        />

        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="h-9 px-3 border border-border bg-surface text-content text-xs rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="">All Statuses</option>
            <option value="CONNECTED">Connected</option>
            <option value="DISCONNECTED">Disconnected</option>
            <option value="PENDING">Pending Configuration</option>
            <option value="MAINTENANCE">Maintenance</option>
          </select>

          {/* Vehicle Assignment Filter */}
          <select
            value={assignmentFilter}
            onChange={(e) => {
              setAssignmentFilter(e.target.value);
              setPage(1);
            }}
            className="h-9 px-3 border border-border bg-surface text-content text-xs rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="all">All Assignments</option>
            <option value="assigned">Assigned to Vehicle</option>
            <option value="unassigned">In Storage / Unassigned</option>
          </select>

          {/* Manufacturer Filter */}
          <select
            value={manufacturerFilter}
            onChange={(e) => {
              setManufacturerFilter(e.target.value);
              setPage(1);
            }}
            className="h-9 px-3 border border-border bg-surface text-content text-xs rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="">All Manufacturers</option>
            <option value="Teltonika">Teltonika</option>
            <option value="Concox">Concox / Jimi</option>
            <option value="Coban">Coban</option>
            <option value="Queclink">Queclink</option>
            <option value="AIS-140">AIS-140</option>
            <option value="Sinotrack">Sinotrack</option>
          </select>
        </div>
      </Card>

      {/* Main Table Card */}
      <Card padding="none" className="overflow-hidden border border-border shadow-card rounded-2xl bg-surface">
        {tableLoading ? (
          <div className="p-6">
            <SkeletonTable rows={6} cols={9} />
          </div>
        ) : tableError ? (
          <ErrorState
            title="Failed to Load Telematics Devices"
            message={tableError.message || 'Error communicating with backend service.'}
            onRetry={loadDevices}
          />
        ) : devices.length === 0 ? (
          <EmptyState
            title="No Telematics Hardware Found"
            description={
              search || statusFilter || manufacturerFilter
                ? 'No devices matched the selected filter criteria.'
                : 'No GPS or IoT telematics devices are currently registered in your company fleet.'
            }
            action={
              <Button
                variant="primary"
                size="sm"
                onClick={() => setAddModalOpen(true)}
                icon={<Plus className="w-4 h-4" />}
              >
                Register First Device
              </Button>
            }
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={devices}
              keyExtractor={(item) => item.id}
              onRowClick={(item) => navigate(`/dashboard/assets/${item.id}`)}
            />

            <div className="border-t border-border px-6 py-3">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={totalDevices}
                onPageChange={setPage}
                onPageSizeChange={(newSize) => {
                  setPageSize(newSize);
                  setPage(1);
                }}
              />
            </div>
          </>
        )}
      </Card>

      {/* Modals */}
      <AddDeviceWizardModal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        vehicles={vehicles}
        onSuccess={handleRefreshAll}
      />

      <ReassignVehicleModal
        open={reassignModalOpen}
        onClose={() => setReassignModalOpen(false)}
        device={selectedDevice}
        vehicles={vehicles}
        onSuccess={handleRefreshAll}
      />

      <EditDeviceModal
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        device={selectedDevice}
        onSuccess={handleRefreshAll}
      />

      <ProviderManagementModal
        open={providersModalOpen}
        onClose={() => {
          setProvidersModalOpen(false);
          loadSummary();
        }}
      />
    </div>
  );
}
