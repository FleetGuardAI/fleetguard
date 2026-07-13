import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Send } from 'lucide-react';
import { createTrip } from '@/api/tripApi';
import { getVehicles } from '@/api/vehicleApi';
import { getDrivers } from '@/api/driverApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';

export default function TripForm() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  // Form states
  const [vehicleId, setVehicleId] = useState('');
  const [driverId, setDriverId] = useState('');
  const [routeName, setRouteName] = useState('');
  const [startPoint, setStartPoint] = useState('');
  const [endPoint, setEndPoint] = useState('');
  const [distanceKm, setDistanceKm] = useState('');
  const [expectedDelivery, setExpectedDelivery] = useState('');

  const [errors, setErrors] = useState({});

  const loadResources = async () => {
    setFetching(true);
    setFetchError(null);
    try {
      const [vData, dData] = await Promise.all([
        getVehicles({ status: 'active' }),
        getDrivers({ status: 'active' })
      ]);
      setVehicles(vData);
      setDrivers(dData);
    } catch (e) {
      setFetchError(e);
      error('Load Error', 'Failed to retrieve active resources.');
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    loadResources();
  }, []);

  const validate = () => {
    const errs = {};
    if (!vehicleId) errs.vehicleId = 'Vehicle allocation is required';
    if (!driverId) errs.driverId = 'Driver allocation is required';
    if (!routeName.trim()) errs.routeName = 'Route name is required';
    if (!startPoint.trim()) errs.startPoint = 'Dispatch start point is required';
    if (!endPoint.trim()) errs.endPoint = 'Delivery destination is required';

    if (!distanceKm) {
      errs.distanceKm = 'Trip distance is required';
    } else if (Number(distanceKm) <= 0) {
      errs.distanceKm = 'Distance must be greater than 0';
    }

    if (!expectedDelivery) {
      errs.expectedDelivery = 'Expected delivery date is required';
    } else {
      const selectedDate = new Date(expectedDelivery);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (selectedDate < today) {
        errs.expectedDelivery = 'Delivery date cannot be in the past';
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);

    const selectedTruck = vehicles.find(v => v.id === Number(vehicleId));
    const selectedDriver = drivers.find(d => d.id === Number(driverId));

    const payload = {
      truck_id: Number(vehicleId),
      truck_plate: selectedTruck?.license_plate || '',
      driver_id: Number(driverId),
      driver_name: selectedDriver?.name || '',
      route_name: routeName.trim(),
      start_point: startPoint.trim(),
      end_point: endPoint.trim(),
      distance_km: Number(distanceKm),
      start_date: new Date().toISOString(),
      expected_delivery: new Date(expectedDelivery).toISOString()
    };

    try {
      await createTrip(payload);
      success('Trip Dispatched', `Cargo trip successfully planned for vehicle ${payload.truck_plate}.`);
      navigate('/dashboard/trips');
    } catch (e) {
      error('Dispatch Error', e.message || 'Failed to dispatch trip.');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (fetchError) {
    return (
      <ErrorState
        title="Resources Error"
        message="Could not load active trucks or drivers to plan dispatch."
        onRetry={loadResources}
      />
    );
  }

  const vehicleOptions = vehicles.map(v => ({ value: v.id, label: `${v.license_plate} - ${v.make} ${v.model}` }));
  const driverOptions = drivers.map(d => ({ value: d.id, label: d.name }));

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Title */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/trips')}
        />
        <div>
          <h1 className="text-2xl font-bold text-content">Dispatch Cargo Trip</h1>
          <p className="text-sm text-content-secondary mt-0.5">Plan and assign operational routes to active drivers.</p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Allocate Vehicle"
              placeholder="-- Select Truck --"
              options={vehicleOptions}
              value={vehicleId}
              onChange={(e) => setVehicleId(e.target.value)}
              error={errors.vehicleId}
              required
            />
            <Select
              label="Allocate Driver"
              placeholder="-- Select Operator --"
              options={driverOptions}
              value={driverId}
              onChange={(e) => setDriverId(e.target.value)}
              error={errors.driverId}
              required
            />
          </div>

          <Input
            label="Route / Trip Identifier"
            placeholder="e.g. Pune - Hyderabad Express Load"
            value={routeName}
            onChange={(e) => setRouteName(e.target.value)}
            error={errors.routeName}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Start Location (Origin)"
              placeholder="e.g. Pune Yard, Maharashtra"
              value={startPoint}
              onChange={(e) => setStartPoint(e.target.value)}
              error={errors.startPoint}
              required
            />
            <Input
              label="End Location (Destination)"
              placeholder="e.g. Hyderabad Depot, Telangana"
              value={endPoint}
              onChange={(e) => setEndPoint(e.target.value)}
              error={errors.endPoint}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Est. Distance (km)"
              type="number"
              min="1"
              placeholder="e.g. 560"
              value={distanceKm}
              onChange={(e) => setDistanceKm(e.target.value)}
              error={errors.distanceKm}
              required
            />
            <Input
              label="Expected Delivery Date"
              type="date"
              value={expectedDelivery}
              onChange={(e) => setExpectedDelivery(e.target.value)}
              error={errors.expectedDelivery}
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/dashboard/trips')}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              icon={<Send className="h-4 w-4" />}
              loading={loading}
            >
              Confirm Dispatch
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
