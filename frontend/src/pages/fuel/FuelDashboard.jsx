import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Fuel, AlertTriangle, Eye, TrendingUp, Compass, FileText } from 'lucide-react';
import { getFuelLogs, getFuelTelemetry, getFuelAlerts } from '@/api/fuelApi';
import { getVehicles } from '@/api/vehicleApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SearchBox } from '@/components/shared/SearchBox';
import { Pagination } from '@/components/ui/Pagination';
import { SkeletonTable, Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { usePagination } from '@/hooks/usePagination';
import FuelChart from '@/components/dashboard/FuelChart';
import { cn } from '@/utils/cn';

export default function FuelDashboard() {
  const navigate = useNavigate();
  const { error } = useToast();

  const [activeTab, setActiveTab] = useState('logs'); // logs, analytics
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [logsError, setLogsError] = useState(null);

  // Search filter for logs
  const [search, setSearch] = useState('');

  // Analytics states
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [telemetry, setTelemetry] = useState([]);
  const [loadingTelemetry, setLoadingTelemetry] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(true);

  // Fetch Logs
  const loadLogs = async () => {
    setLoadingLogs(true);
    setLogsError(null);
    try {
      const data = await getFuelLogs({ search });
      setLogs(data);
    } catch (e) {
      setLogsError(e);
      error('Load Error', 'Failed to retrieve fuel entries.');
    } finally {
      setLoadingLogs(false);
    }
  };

  // Fetch vehicles & alerts on load
  const loadAnalyticsMetadata = async () => {
    setLoadingAlerts(true);
    try {
      const [vData, aData] = await Promise.all([
        getVehicles(),
        getFuelAlerts()
      ]);
      setVehicles(vData);
      setAlerts(aData);
      if (vData.length > 0) {
        setSelectedVehicleId(String(vData[0].id));
      }
    } catch (e) {
      error('Load Error', 'Failed to fetch analytics metadata.');
    } finally {
      setLoadingAlerts(false);
    }
  };

  // Load telemetry for selected vehicle
  const loadTelemetry = async () => {
    if (!selectedVehicleId) return;
    setLoadingTelemetry(true);
    try {
      const tData = await getFuelTelemetry(selectedVehicleId);
      setTelemetry(tData);
    } catch (e) {
      error('Telemetry Error', 'Failed to retrieve telemetry points.');
    } finally {
      setLoadingTelemetry(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [search]);

  useEffect(() => {
    loadAnalyticsMetadata();
  }, []);

  useEffect(() => {
    if (selectedVehicleId && activeTab === 'analytics') {
      loadTelemetry();
    }
  }, [selectedVehicleId, activeTab]);

  // Logs pagination
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

  const columns = [
    {
      key: 'truck_plate',
      label: 'Vehicle',
      render: (item) => <span className="font-mono text-xs font-semibold">{item.truck_plate || `Vehicle ID: ${item.truck_id}`}</span>
    },
    {
      key: 'date',
      label: 'Timestamp',
      sortable: true,
      render: (item) => (
        <span className="text-xs text-content-secondary">
          {item.date ? new Date(item.date).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : 'N/A'}
        </span>
      )
    },
    {
      key: 'station',
      label: 'Fuel Station / Location',
      render: (item) => <span className="text-xs font-medium text-content">{item.station || 'Depot'}</span>
    },
    {
      key: 'quantity_liters',
      label: 'Volume (L)',
      sortable: true,
      render: (item) => <span className="font-mono text-xs text-content">{item.quantity_liters != null ? `${item.quantity_liters} L` : 'N/A'}</span>
    },
    {
      key: 'total_amount',
      label: 'Total Amount',
      sortable: true,
      render: (item) => (
        <span className="font-mono text-xs font-semibold text-content">
          {item.total_amount != null ? `₹${item.total_amount.toLocaleString('en-IN')}` : 'N/A'}
        </span>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (item) => (
        <Badge variant={(item.status || 'LOGGED').toUpperCase() === 'APPROVED' || (item.status || 'LOGGED').toUpperCase() === 'COMPLETED' ? 'success' : 'warning'}>
          {(item.status || 'LOGGED').toUpperCase()}
        </Badge>
      )
    }
  ];

  const alertColumns = [
    {
      key: 'truck_plate',
      label: 'Vehicle Plate',
      render: (item) => <span className="font-mono text-xs font-semibold text-rose-600">{item.truck_plate || (item.truck_id ? `Vehicle ID: ${item.truck_id}` : 'Vehicle')}</span>
    },
    {
      key: 'timestamp',
      label: 'Alert Time',
      render: (item) => <span>{item.timestamp ? new Date(item.timestamp).toLocaleString() : 'N/A'}</span>
    },
    {
      key: 'fuel_drop_liters',
      label: 'Theft Volume',
      render: (item) => <span className="font-bold text-rose-600">-{item.fuel_drop_liters != null ? `${item.fuel_drop_liters} Liters` : 'N/A'}</span>
    },
    {
      key: 'telemetry',
      label: 'Sensor Bounds',
      render: (item) => <span className="text-xs text-content-secondary">{item.filtered_level_before ?? 'N/A'}L → {item.filtered_level_after ?? 'N/A'}L</span>
    },
    {
      key: 'gps',
      label: 'Coordinates Location',
      render: (item) => (
        <span className="text-xs text-content-secondary flex items-center gap-1">
          <Compass className="h-3 w-3" /> Lat {item.latitude ?? '0'}, Lng {item.longitude ?? '0'}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Fuel Management</h1>
          <p className="text-sm text-content-secondary mt-0.5">Log filling transactions and monitor stationary siphon theft telemetry.</p>
        </div>
        <Button
          variant="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/fuel/new')}
        >
          Add Fuel Log
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
          Fuel Logs Directory
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'analytics'
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Fuel Analytics & Theft Telematics
        </button>
      </div>

      {/* Tab contents */}
      {activeTab === 'logs' ? (
        <div className="space-y-6">
          <Card className="p-4 flex items-center justify-between">
            <SearchBox
              value={search}
              onChange={setSearch}
              placeholder="Search station location, vehicle plate..."
              className="w-full md:max-w-xs"
            />
          </Card>

          <Card padding="none" className="overflow-hidden">
            {loadingLogs ? (
              <div className="p-6">
                <SkeletonTable rows={5} cols={7} />
              </div>
            ) : logsError ? (
              <ErrorState
                title="Failed to Load Logs"
                message={logsError.message || 'An error occurred.'}
                onRetry={loadLogs}
              />
            ) : logs.length === 0 ? (
              <EmptyState
                title="No Refuel Transactions logged"
                description="Record the first diesel purchase log for your fleet."
                actionLabel="Add Fuel Entry"
                onAction={() => navigate('/dashboard/fuel/new')}
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
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chart Area */}
            <Card className="lg:col-span-2 space-y-4">
              <CardHeader className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-0 gap-4">
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-brand-600" />
                  Fuel Sensor level Curves (Liters)
                </CardTitle>
                <div className="w-full sm:max-w-xs">
                  <select
                    value={selectedVehicleId}
                    onChange={(e) => setSelectedVehicleId(e.target.value)}
                    className="w-full h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  >
                    {vehicles.map(v => (
                      <option key={v.id} value={v.id}>
                        {v.license_plate} - {v.make}
                      </option>
                    ))}
                  </select>
                </div>
              </CardHeader>
              {loadingTelemetry ? (
                <div className="h-72 bg-surface-secondary rounded-xl flex items-center justify-center">
                  <Loader size="md" />
                </div>
              ) : telemetry.length === 0 ? (
                <div className="h-72 border border-dashed rounded-xl flex items-center justify-center text-content-secondary">
                  Select a truck to display live sensor telemetry.
                </div>
              ) : (
                <div className="h-72">
                  <FuelChart data={telemetry} />
                </div>
              )}
            </Card>

            {/* Suspected Siphon drops */}
            <Card className="lg:col-span-1 space-y-4">
              <CardHeader className="p-0">
                <CardTitle className="text-base flex items-center gap-2 text-rose-600">
                  <AlertTriangle className="h-4 w-4 animate-bounce" />
                  Theft Detection Analytics
                </CardTitle>
              </CardHeader>
              <div className="p-4 bg-rose-50/50 border border-rose-100 rounded-xl">
                <p className="text-xs text-rose-900 font-medium">
                  EMA Siphon Telemetry Check:
                </p>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                  Sudden drops exceeding 15 Liters while truck velocity matches 0 km/h trigger instant owner alerts.
                </p>
              </div>
              <div className="space-y-3">
                {alerts.slice(0, 3).map((item) => (
                  <div key={item.id} className="p-3 bg-surface border border-border rounded-xl flex flex-col gap-1 hover:border-rose-300 transition-colors">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-content">{item.truck_plate}</span>
                      <span className="font-bold text-rose-600">-{item.fuel_drop_liters} L</span>
                    </div>
                    <p className="text-[10px] text-content-secondary">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                    <p className="text-[10px] text-rose-700 bg-rose-50 px-2 py-1 rounded mt-1">
                      {item.fuel_drop_liters > 25 ? 'Suspected Siphon Siphonage' : 'Anomalous Drop'}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Alarm Log table */}
          <Card padding="none" className="overflow-hidden">
            <CardHeader className="p-6 pb-2">
              <CardTitle className="text-base">Historical Theft Alarms Log</CardTitle>
            </CardHeader>
            {loadingAlerts ? (
              <div className="p-6">
                <SkeletonTable rows={3} cols={5} />
              </div>
            ) : (
              <Table
                columns={alertColumns}
                data={alerts}
                keyExtractor={(item) => item.id}
                emptyMessage="No fuel theft alarms registered."
              />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
