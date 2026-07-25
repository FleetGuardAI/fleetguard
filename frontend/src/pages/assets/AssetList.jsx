import React, { useState, useEffect } from 'react';
import { Cpu, Eye, RefreshCw, Layers } from 'lucide-react';
import { getAssets } from '@/api/assetApi';
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

export default function AssetList() {
  const { error } = useToast();
  const [assets, setAssets] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [installFilter, setInstallFilter] = useState('all');
  const [opsFilter, setOpsFilter] = useState('all');

  // Modal
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [aData, vData] = await Promise.all([
        getAssets({ search, installation_status: installFilter, operational_status: opsFilter }),
        getVehicles()
      ]);
      setAssets(aData);
      setVehicles(vData);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve asset records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [search, installFilter, opsFilter]);

  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: assets.length, initialPageSize: 10 });

  const paginatedAssets = assets.slice(startIndex, endIndex);

  const vehicleMap = React.useMemo(() => {
    const map = {};
    vehicles.forEach(v => {
      map[v.id] = v.registration_number || v.license_plate;
    });
    return map;
  }, [vehicles]);

  const handleViewAsset = (asset) => {
    setSelectedAsset(asset);
    setDetailsModalOpen(true);
  };

  const getInstallBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'installed':
      case 'mounted':
        return <Badge variant="success" dot>INSTALLED</Badge>;
      case 'uninstalled':
      case 'storage':
        return <Badge variant="neutral" dot>UNINSTALLED</Badge>;
      default:
        return <Badge variant="neutral">{status?.toUpperCase() || 'UNKNOWN'}</Badge>;
    }
  };

  const getOpsBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'operational':
      case 'online':
        return <Badge variant="success">ACTIVE</Badge>;
      case 'maintenance':
      case 'degraded':
        return <Badge variant="warning">DEGRADED</Badge>;
      case 'faulty':
      case 'failed':
      case 'offline':
        return <Badge variant="danger">FAULTY</Badge>;
      default:
        return <Badge variant="neutral">{status?.toUpperCase() || 'UNKNOWN'}</Badge>;
    }
  };

  const columns = [
    {
      key: 'business_id',
      label: 'Asset ID',
      render: (item) => <span className="font-mono text-xs font-bold text-content">{item.business_id}</span>
    },
    {
      key: 'asset_type',
      label: 'Hardware Type',
      render: (item) => <span className="font-medium text-content">{item.asset_type?.replace(/_/g, ' ') || 'Hardware'}</span>
    },
    {
      key: 'model',
      label: 'Make / Model',
      render: (item) => (
        <span>{[item.manufacturer, item.model].filter(Boolean).join(' ') || 'N/A'}</span>
      )
    },
    {
      key: 'serial_number',
      label: 'Serial Number',
      render: (item) => <span className="font-mono text-xs text-content-secondary">{item.serial_number || 'N/A'}</span>
    },
    {
      key: 'current_vehicle_id',
      label: 'Assigned Truck',
      render: (item) => (
        <span className="text-xs font-semibold">
          {item.current_vehicle_id ? (vehicleMap[item.current_vehicle_id] || `Vehicle ID: ${item.current_vehicle_id}`) : 'Unassigned'}
        </span>
      )
    },
    {
      key: 'installation_status',
      label: 'Mounting Status',
      render: (item) => getInstallBadge(item.installation_status)
    },
    {
      key: 'operational_status',
      label: 'Health',
      render: (item) => getOpsBadge(item.operational_status)
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
            onClick={() => handleViewAsset(item)}
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
          <h1 className="text-2xl font-bold text-content">Hardware Assets</h1>
          <p className="text-sm text-content-secondary mt-0.5">Manage IoT telematics gateways, fuel sensors, dashcams, and fleet hardware assets.</p>
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
          placeholder="Search asset ID, serial number, model..."
          className="w-full md:max-w-xs"
        />

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={installFilter}
            onChange={(e) => setInstallFilter(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none w-full md:w-44"
          >
            <option value="all">All Mountings</option>
            <option value="installed">Installed</option>
            <option value="uninstalled">Uninstalled</option>
          </select>

          <select
            value={opsFilter}
            onChange={(e) => setOpsFilter(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none w-full md:w-44"
          >
            <option value="all">All Operational Health</option>
            <option value="active">Active / Healthy</option>
            <option value="faulty">Faulty / Degraded</option>
          </select>
        </div>
      </Card>

      {/* Main Table */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={8} />
          </div>
        ) : err ? (
          <ErrorState
            title="Failed to Load Hardware Assets"
            message={err.message || 'An error occurred while communicating with the backend.'}
            onRetry={loadData}
          />
        ) : assets.length === 0 ? (
          <EmptyState
            title="No Hardware Assets Found"
            description={search ? "No assets matched your filter criteria." : "No telematics assets recorded in the system."}
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedAssets}
              keyExtractor={(item) => item.id}
              onRowClick={(item) => handleViewAsset(item)}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={assets.length}
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
        title="Hardware Asset Details & Telematics Audit"
        closable
      >
        {selectedAsset && (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="font-bold text-content text-lg font-mono">{selectedAsset.business_id}</h4>
                <p className="text-xs text-content-secondary">
                  {selectedAsset.asset_type?.replace(/_/g, ' ')} | {[selectedAsset.manufacturer, selectedAsset.model].filter(Boolean).join(' ')}
                </p>
              </div>
              <div className="flex gap-1.5">
                {getInstallBadge(selectedAsset.installation_status)}
                {getOpsBadge(selectedAsset.operational_status)}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-xs text-content-secondary block">Assigned Truck</span>
                <span className="font-semibold text-content">
                  {selectedAsset.current_vehicle_id ? (vehicleMap[selectedAsset.current_vehicle_id] || `Vehicle ID: ${selectedAsset.current_vehicle_id}`) : 'Unassigned'}
                </span>
              </div>
              <div>
                <span className="text-xs text-content-secondary block">Serial Number</span>
                <span className="font-mono text-xs text-content font-semibold">{selectedAsset.serial_number || 'N/A'}</span>
              </div>
              <div>
                <span className="text-xs text-content-secondary block">Firmware Version</span>
                <span className="font-semibold text-content">{selectedAsset.firmware_version || 'v1.0.0'}</span>
              </div>
              <div>
                <span className="text-xs text-content-secondary block">Manufacturer</span>
                <span className="font-semibold text-content">{selectedAsset.manufacturer || 'N/A'}</span>
              </div>
            </div>

            {/* Event History */}
            <div className="pt-3 border-t border-border">
              <h5 className="text-xs font-bold text-content uppercase tracking-wider mb-3">Asset Operational Log</h5>
              {selectedAsset.history_records && selectedAsset.history_records.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {selectedAsset.history_records.map((rec) => (
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
                <p className="text-xs text-content-muted italic">No history records logged for this hardware asset.</p>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
