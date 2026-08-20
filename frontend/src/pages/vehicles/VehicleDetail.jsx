import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, Edit2, Trash2, Calendar, Fuel, Info, Route, ShieldAlert, Zap } from 'lucide-react';
import { getVehicleById, getVehicleHistory } from '@/api/vehicleApi';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Table } from '@/components/ui/Table';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { TruckFinancialIntelligence } from '@/components/vehicles/TruckFinancialIntelligence';

export default function VehicleDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [vehicle, setVehicle] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [vData, hData] = await Promise.all([
        getVehicleById(id),
        getVehicleHistory(id)
      ]);
      setVehicle(vData);
      setHistory(hData);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve vehicle details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleConfirmDelete = async () => {
    setDeleting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      success('Vehicle Deleted', `Successfully removed vehicle ${vehicle.license_plate}.`);
      setDeleteModalOpen(false);
      navigate('/dashboard/vehicles');
    } catch (e) {
      error('Delete Error', 'Failed to delete vehicle.');
    } finally {
      setDeleting(false);
    }
  };

  const historyColumns = [
    {
      key: 'date',
      label: 'Timestamp',
      render: (item) => <span className="text-xs text-content-secondary">{new Date(item.date).toLocaleString()}</span>
    },
    {
      key: 'status',
      label: 'Telemetry Status',
      render: (item) => (
        <Badge variant={item.status === 'moving' ? 'success' : 'neutral'} size="sm">
          {item.status.toUpperCase()}
        </Badge>
      )
    },
    {
      key: 'speed',
      label: 'Speed',
      render: (item) => <span>{item.speed} km/h</span>
    },
    {
      key: 'location',
      label: 'GPS Location'
    },
    {
      key: 'fuelLevel',
      label: 'Fuel Sensor (L)',
      render: (item) => <span>{item.fuelLevel} L</span>
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (err || !vehicle) {
    return (
      <ErrorState
        title="Vehicle Profile Not Found"
        message={err?.message || 'The requested vehicle could not be loaded.'}
        onRetry={loadData}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate('/dashboard/vehicles')}
          />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold font-mono text-content">{vehicle.license_plate}</h1>
              <Badge variant={vehicle.is_active ? 'success' : 'neutral'} dot>
                {vehicle.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <p className="text-sm text-content-secondary mt-0.5">
              {vehicle.make} {vehicle.model} • Year {vehicle.year}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            icon={<Edit2 className="h-4 w-4" />}
            onClick={() => navigate(`/dashboard/vehicles/${vehicle.id}/edit`)}
          >
            Edit Profile
          </Button>
          <Button
            variant="danger"
            icon={<Trash2 className="h-4 w-4" />}
            onClick={() => setDeleteModalOpen(true)}
          >
            Delete
          </Button>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Specifications Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Info className="h-4 w-4 text-brand-600" />
              Specifications
            </CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-sm text-content-secondary">Brand</span>
              <span className="text-sm font-medium text-content">{vehicle.make}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-sm text-content-secondary">Model Series</span>
              <span className="text-sm font-medium text-content">{vehicle.model}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-sm text-content-secondary">Model Year</span>
              <span className="text-sm font-medium text-content flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-content-muted" />
                {vehicle.year}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-sm text-content-secondary">Fuel Tank Capacity</span>
              <span className="text-sm font-medium text-content flex items-center gap-1.5">
                <Fuel className="h-3.5 w-3.5 text-content-muted" />
                {vehicle.tank_capacity} L
              </span>
            </div>
          </div>
        </Card>

        {/* Active Trip Details */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Route className="h-4 w-4 text-brand-600" />
              Active Operations
            </CardTitle>
          </CardHeader>
          {vehicle.activeTrip ? (
            <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-xl space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <Badge variant="brand">ON TRIP</Badge>
                  <h4 className="text-base font-semibold text-content mt-1.5">{vehicle.activeTrip.route_name}</h4>
                  <p className="text-xs text-content-secondary mt-0.5">Assigned to: {vehicle.activeTrip.driver_name}</p>
                </div>
                <Link to={`/dashboard/trips/${vehicle.activeTrip.id}`}>
                  <Button variant="outline" size="sm" icon={<Zap className="h-3.5 w-3.5 text-brand-600" />}>
                    Track Trip
                  </Button>
                </Link>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm pt-2">
                <div>
                  <span className="text-xs text-content-secondary block">Start Date</span>
                  <span className="font-medium text-content">{new Date(vehicle.activeTrip.start_date).toLocaleDateString()}</span>
                </div>
                <div>
                  <span className="text-xs text-content-secondary block">Estimated Delivery</span>
                  <span className="font-medium text-content">{new Date(vehicle.activeTrip.expected_delivery).toLocaleDateString()}</span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-medium text-content-secondary">
                  <span>Trip Progress</span>
                  <span>{vehicle.activeTrip.progress}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-brand-600 h-full transition-all duration-300" style={{ width: `${vehicle.activeTrip.progress}%` }} />
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 border border-dashed border-border rounded-xl text-center">
              <Route className="h-8 w-8 text-content-muted mb-2" />
              <p className="text-sm font-semibold text-content">Idle Status</p>
              <p className="text-xs text-content-secondary mt-0.5 max-w-xs">This vehicle is not currently allocated to any dispatch trip route.</p>
            </div>
          )}
        </Card>
      </div>

      {/* Financial Intelligence Section */}
      <div className="pt-2">
        <h2 className="text-lg font-semibold text-content mb-4 flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-brand-600" />
          Financial Intelligence Profile
        </h2>
        <TruckFinancialIntelligence truckId={vehicle.license_plate} />
      </div>

      {/* Telemetry Log */}
      <Card padding="none" className="overflow-hidden">
        <CardHeader className="p-6 pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Zap className="h-4 w-4 text-brand-600 animate-pulse" />
            Live Telematics History Log
          </CardTitle>
        </CardHeader>
        <Table
          columns={historyColumns}
          data={history}
          keyExtractor={(item) => item.id}
          emptyMessage="No telemetry logged for this vehicle yet."
        />
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
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-xl">
          <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-950">
              Removing {vehicle.license_plate}
            </p>
            <p className="text-xs text-red-700">
              This will permanently archive the specifications and associated history details.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
