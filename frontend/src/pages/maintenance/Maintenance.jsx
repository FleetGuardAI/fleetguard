import React, { useState, useEffect } from 'react';
import { Wrench, Plus, Eye, CheckCircle, Calendar, Compass, FileText, Check, Settings, ShieldAlert, Package } from 'lucide-react';
import { getMaintenanceLogs, scheduleMaintenance } from '@/api/maintenanceApi';
import { getVehicles } from '@/api/vehicleApi';

import { getAssets } from '@/api/assetApi';
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
import { Input, Select } from '@/components/ui/Input';
import { cn } from '@/utils/cn';

export default function Maintenance() {
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState('logs'); // logs, inventory
  const [logs, setLogs] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [inventoryParts, setInventoryParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');

  // Modals
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // Form states
  const [vehicleId, setVehicleId] = useState('');
  const [serviceType, setServiceType] = useState('Scheduled Service');
  const [odometer, setOdometer] = useState('');
  const [cost, setCost] = useState('');
  const [workshop, setWorkshop] = useState('');
  const [description, setDescription] = useState('');
  const [scheduleDate, setScheduleDate] = useState('');
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const loadMaintenanceData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [lData, vData, aData] = await Promise.all([
        getMaintenanceLogs({ search }),
        getVehicles(),
        getAssets().catch(() => [])
      ]);
      setLogs(lData);
      setVehicles(vData);

      const parts = [
        ...aData.map(a => ({
          sku: a.business_id || `AST-${a.id}`,
          name: [a.manufacturer, a.model, a.asset_type?.replace(/_/g, ' ')].filter(Boolean).join(' '),
          stock: a.installation_status === 'uninstalled' ? 1 : 0,
          reorder: 1,
          unit: 'Units',
          price: a.purchase_information?.price || 0,
        }))
      ];
      setInventoryParts(parts);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve maintenance data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMaintenanceData();
  }, [search]);

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

  const validateForm = () => {
    const errs = {};
    if (!vehicleId) errs.vehicleId = 'Vehicle allocation is required';
    if (!workshop.trim()) errs.workshop = 'Workshop location details are required';
    if (!description.trim()) errs.description = 'Service description details are required';
    if (!scheduleDate) errs.scheduleDate = 'Scheduled date is required';

    if (!cost) {
      errs.cost = 'Est. cost amount is required';
    } else if (Number(cost) <= 0) {
      errs.cost = 'Cost must be positive';
    }

    if (!odometer) {
      errs.odometer = 'Current odometer logging is required';
    } else if (Number(odometer) <= 0) {
      errs.odometer = 'Odometer must be positive';
    }

    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleScheduleMaintenance = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSubmitting(true);
    const selectedTruck = vehicles.find(v => v.id === Number(vehicleId));
    const payload = {
      truck_id: Number(vehicleId),
      truck_plate: selectedTruck?.license_plate || '',
      type: serviceType,
      odometer: Number(odometer),
      cost: Number(cost),
      workshop: workshop.trim(),
      description: description.trim(),
      date: new Date(scheduleDate).toISOString()
    };

    try {
      const newRecord = await scheduleMaintenance(payload);
      setLogs(prev => [newRecord, ...prev]);
      success('Service Scheduled', `Successfully created ticket for truck ${payload.truck_plate}.`);
      setScheduleModalOpen(false);
      setVehicleId('');
      setOdometer('');
      setCost('');
      setWorkshop('');
      setDescription('');
      setScheduleDate('');
    } catch (e) {
      error('Action Failed', 'Failed to schedule service.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewRecord = (record) => {
    setSelectedRecord(record);
    setDetailsModalOpen(true);
  };

  const handleCompleteRecord = (id) => {
    setLogs(prev => prev.map(r => r.id === id ? { ...r, status: 'completed' } : r));
    success('Service Completed', 'Maintenance record updated to completed.');
    setDetailsModalOpen(false);
  };

  const getStatusVariant = (status) => {
    return status === 'completed' ? 'success' : 'warning';
  };

  const columns = [
    {
      key: 'truck_plate',
      label: 'Vehicle Plate',
      render: (item) => <span className="font-mono text-xs font-semibold">{item.truck_plate}</span>
    },
    {
      key: 'type',
      label: 'Service Category'
    },
    {
      key: 'workshop',
      label: 'Workshop'
    },
    {
      key: 'cost',
      label: 'Service Cost',
      render: (item) => <span className="font-bold">₹{item.cost.toLocaleString()}</span>
    },
    {
      key: 'date',
      label: 'Scheduled Date',
      render: (item) => <span>{new Date(item.date).toLocaleDateString()}</span>
    },
    {
      key: 'status',
      label: 'Status',
      render: (item) => (
        <Badge variant={getStatusVariant(item.status)} dot>
          {item.status.toUpperCase()}
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
            onClick={() => handleViewRecord(item)}
          />
        </div>
      )
    }
  ];

  const inventoryColumns = [
    { key: 'sku', label: 'SKU Part ID', render: (item) => <span className="font-mono text-xs">{item.sku}</span> },
    { key: 'name', label: 'Item Name', render: (item) => <span className="font-semibold">{item.name}</span> },
    { key: 'stock', label: 'In Stock', render: (item) => (
      <span className={item.stock <= item.reorder ? 'text-amber-600 font-bold' : ''}>
        {item.stock} {item.unit}
      </span>
    )},
    { key: 'price', label: 'Unit Cost', render: (item) => <span>₹{item.price.toLocaleString()}</span> },
    { key: 'status', label: 'Inventory Check', render: (item) => (
      <Badge variant={item.stock <= item.reorder ? 'warning' : 'success'}>
        {item.stock <= item.reorder ? 'LOW STOCK' : 'IN STOCK'}
      </Badge>
    )}
  ];

  const vehicleOptions = vehicles.map(v => ({ value: v.id, label: `${v.license_plate} - ${v.make} ${v.model}` }));

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Fleet Maintenance</h1>
          <p className="text-sm text-content-secondary mt-0.5">Track breakdown events, inspect parts safety, and schedule services.</p>
        </div>
        <Button
          variant="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => setScheduleModalOpen(true)}
        >
          Schedule Service
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab('logs')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'logs'
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Maintenance Service Logs
        </button>
        <button
          onClick={() => setActiveTab('inventory')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'inventory'
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Spare Parts Inventory
        </button>
      </div>

      {activeTab === 'logs' ? (
        <div className="space-y-6">
          <Card className="p-4 flex items-center justify-between">
            <SearchBox
              value={search}
              onChange={setSearch}
              placeholder="Search truck plate, service category..."
              className="w-full md:max-w-xs"
            />
          </Card>

          <Card padding="none" className="overflow-hidden">
            {loading ? (
              <div className="p-6">
                <SkeletonTable rows={5} cols={7} />
              </div>
            ) : err ? (
              <ErrorState
                title="Failed to Load Maintenance Logs"
                message={err.message || 'An error occurred.'}
                onRetry={loadMaintenanceData}
              />
            ) : logs.length === 0 ? (
              <EmptyState
                title="No Maintenance Logs recorded"
                description="Create a ticket or schedule service for fleet trucks."
                actionLabel="Schedule Service"
                onAction={() => setScheduleModalOpen(true)}
              />
            ) : (
              <>
                <Table
                  columns={columns}
                  data={paginatedLogs}
                  keyExtractor={(item) => item.id}
                  onRowClick={(item) => handleViewRecord(item)}
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
      ) : (
        <div className="space-y-6">
          {/* Inventory info */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4 flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-brand-50 text-brand-600">
                <Package className="h-5 w-5" />
              </div>
              <div>
                <span className="text-[10px] text-content-secondary uppercase block font-bold">Total Parts</span>
                <span className="text-xl font-bold text-content">{inventoryParts.length} SKUs</span>
              </div>
            </Card>
            <Card className="p-4 flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
                <ShieldAlert className="h-5 w-5 animate-pulse" />
              </div>
              <div>
                <span className="text-[10px] text-content-secondary uppercase block font-bold">Low Stock alerts</span>
                <span className="text-xl font-bold text-content">1 Alert</span>
              </div>
            </Card>
          </div>

          <Card padding="none" className="overflow-hidden">
            <Table
              columns={inventoryColumns}
              data={inventoryParts}
              keyExtractor={(item) => item.sku}
            />
          </Card>
        </div>
      )}

      {/* Schedule Service Modal */}
      <Modal
        open={scheduleModalOpen}
        onClose={() => setScheduleModalOpen(false)}
        title="Schedule Maintenance Service"
        description="Select vehicle and enter maintenance checklist details."
        closable={!submitting}
        footer={
          <>
            <Button variant="outline" onClick={() => setScheduleModalOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleScheduleMaintenance} loading={submitting}>
              Confirm Ticket
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleScheduleMaintenance}>
          <Select
            label="Allocate Vehicle"
            placeholder="-- Select Truck --"
            options={vehicleOptions}
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
            error={formErrors.vehicleId}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Service Type"
              options={[
                { value: 'Scheduled Service', label: 'Scheduled Maintenance' },
                { value: 'Breakdown Repair', label: 'Unscheduled Breakdown Repair' },
                { value: 'Inspection', label: 'Routine Safety Inspection' }
              ]}
              value={serviceType}
              onChange={(e) => setServiceType(e.target.value)}
              required
            />
            <Input
              label="Service Cost Est. (INR)"
              type="number"
              min="1"
              placeholder="e.g. 15000"
              value={cost}
              onChange={(e) => setCost(e.target.value)}
              error={formErrors.cost}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Odometer Logging value"
              type="number"
              placeholder="Odo reading (km)"
              value={odometer}
              onChange={(e) => setOdometer(e.target.value)}
              error={formErrors.odometer}
              required
            />
            <Input
              label="Scheduled Date"
              type="date"
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
              error={formErrors.scheduleDate}
              required
            />
          </div>

          <Input
            label="Authorized Workshop Details"
            placeholder="e.g. Tata Authorized Service, Jaipur"
            value={workshop}
            onChange={(e) => setWorkshop(e.target.value)}
            error={formErrors.workshop}
            required
          />

          <Input
            label="Checklist Description Notes"
            placeholder="e.g. Replenish engine lubricant, inspect wheel alignment"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            error={formErrors.description}
            required
          />
        </form>
      </Modal>

      {/* Details View Modal */}
      <Modal
        open={detailsModalOpen}
        onClose={() => setDetailsModalOpen(false)}
        title="Maintenance Ticket Details"
        closable
        footer={
          selectedRecord?.status === 'scheduled' && (
            <Button
              variant="success"
              icon={<CheckCircle className="h-4 w-4" />}
              onClick={() => handleCompleteRecord(selectedRecord.id)}
            >
              Mark Completed
            </Button>
          )
        }
      >
        {selectedRecord && (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="font-bold text-content text-lg">{selectedRecord.truck_plate}</h4>
                <p className="text-xs text-content-secondary">{selectedRecord.type}</p>
              </div>
              <Badge variant={selectedRecord.status === 'completed' ? 'success' : 'warning'}>
                {selectedRecord.status.toUpperCase()}
              </Badge>
            </div>
            <div className="space-y-2 text-sm">
              <p className="flex justify-between"><span className="text-content-secondary">Cost Logged:</span> <span className="font-bold text-brand-600">₹{selectedRecord.cost.toLocaleString()}</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Odometer Log:</span> <span className="font-medium">{selectedRecord.odometer} km</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Workshop:</span> <span className="font-medium">{selectedRecord.workshop}</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Execution Date:</span> <span className="font-medium">{new Date(selectedRecord.date).toLocaleDateString()}</span></p>
              <div className="pt-2 border-t border-border mt-2">
                <span className="text-xs text-content-secondary block uppercase font-semibold">Service Description Notes</span>
                <p className="text-xs text-content mt-1 italic">{selectedRecord.description}</p>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
