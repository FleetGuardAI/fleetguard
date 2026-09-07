import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, Brain, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { createTrip, evaluateTripIntelligence } from '@/api/tripApi';
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
  const [evaluating, setEvaluating] = useState(false);
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
  
  // Financial & Intelligence states
  const [revenue, setRevenue] = useState('');
  const [plannedCost, setPlannedCost] = useState('');
  const [plannedFuel, setPlannedFuel] = useState('');
  const [cargoWeight, setCargoWeight] = useState('');
  const [intelligenceResult, setIntelligenceResult] = useState(null);

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

  const getIntelligencePayload = () => {
    return {
      vehicle_id: Number(vehicleId),
      driver_id: Number(driverId),
      origin_location: startPoint.trim(),
      destination_location: endPoint.trim(),
      planned_distance: distanceKm ? Number(distanceKm) : null,
      planned_start_time: new Date().toISOString(),
      planned_end_time: expectedDelivery ? new Date(expectedDelivery).toISOString() : null,
      revenue: revenue ? Number(revenue) : null,
      planned_cost: plannedCost ? Number(plannedCost) : null,
      planned_fuel_liters: plannedFuel ? Number(plannedFuel) : null,
      cargo_weight: cargoWeight ? Number(cargoWeight) : null,
    };
  };

  const handleEvaluate = async () => {
    if (!validate()) return;
    setEvaluating(true);
    setIntelligenceResult(null);
    try {
      const result = await evaluateTripIntelligence(getIntelligencePayload());
      setIntelligenceResult(result);
    } catch (e) {
      error('Evaluation Failed', e.message || 'Could not evaluate trip intelligence.');
    } finally {
      setEvaluating(false);
    }
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
      expected_delivery: new Date(expectedDelivery).toISOString(),
      revenue: revenue ? Number(revenue) : null,
      planned_cost: plannedCost ? Number(plannedCost) : null,
      planned_fuel_liters: plannedFuel ? Number(plannedFuel) : null,
      cargo_weight: cargoWeight ? Number(cargoWeight) : null,
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
    <div className="space-y-6 max-w-4xl">
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-content border-b border-border pb-2">Logistics & Assignment</h3>
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
              </div>

              <div className="space-y-4 pt-4 border-t border-border">
                <h3 className="text-lg font-medium text-content border-b border-border pb-2">Economics (Optional)</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Freight Revenue (INR)"
                    type="number"
                    placeholder="e.g. 45000"
                    value={revenue}
                    onChange={(e) => setRevenue(e.target.value)}
                  />
                  <Input
                    label="Planned Cost (INR)"
                    type="number"
                    placeholder="e.g. 35000"
                    value={plannedCost}
                    onChange={(e) => setPlannedCost(e.target.value)}
                  />
                  <Input
                    label="Planned Fuel (Liters)"
                    type="number"
                    placeholder="e.g. 150"
                    value={plannedFuel}
                    onChange={(e) => setPlannedFuel(e.target.value)}
                  />
                  <Input
                    label="Cargo Weight (Tonnes)"
                    type="number"
                    placeholder="e.g. 20"
                    value={cargoWeight}
                    onChange={(e) => setCargoWeight(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex justify-between items-center pt-6 border-t border-border">
                <Button
                  type="button"
                  variant="secondary"
                  icon={<Brain className="h-4 w-4" />}
                  onClick={handleEvaluate}
                  loading={evaluating}
                >
                  Evaluate Economics
                </Button>
                <div className="flex gap-3">
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
              </div>
            </form>
          </Card>
        </div>

        {/* Intelligence Side Panel */}
        <div className="lg:col-span-1">
          <Card className="h-full sticky top-6">
            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-border">
              <Brain className="h-5 w-5 text-indigo-500" />
              <h2 className="text-lg font-semibold text-content">Trip Intelligence</h2>
            </div>
            
            {!intelligenceResult && !evaluating && (
              <div className="text-center py-12 text-content-secondary">
                <Brain className="h-12 w-12 mx-auto mb-3 opacity-20" />
                <p>Click "Evaluate Economics" to analyze this trip before dispatch.</p>
              </div>
            )}

            {evaluating && (
              <div className="flex flex-col items-center justify-center py-12 text-content-secondary">
                <Loader size="md" className="mb-4" />
                <p>Analyzing route, feasibility, and economics...</p>
              </div>
            )}

            {intelligenceResult && !evaluating && (
              <div className="space-y-5 animate-in fade-in">
                {/* Recommendation Banner */}
                <div className={`p-4 rounded-lg flex items-start gap-3 ${
                  intelligenceResult.recommendation === 'TAKE' ? 'bg-green-500/10 border border-green-500/20 text-green-700 dark:text-green-400' :
                  intelligenceResult.recommendation === 'REVIEW' ? 'bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400' :
                  'bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-400'
                }`}>
                  {intelligenceResult.recommendation === 'TAKE' && <CheckCircle className="h-5 w-5 shrink-0 mt-0.5" />}
                  {intelligenceResult.recommendation === 'REVIEW' && <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />}
                  {intelligenceResult.recommendation === 'AVOID' && <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />}
                  
                  <div>
                    <h3 className="font-bold text-lg mb-1">{intelligenceResult.recommendation}</h3>
                    <ul className="text-sm space-y-1">
                      {intelligenceResult.recommendation_reasons.map((r, i) => (
                        <li key={i} className="flex gap-1.5">
                          <span className={r.factor_type === 'positive' ? 'text-green-500' : 'text-red-500'}>•</span>
                          <span>{r.description}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Economics Summary */}
                <div className="bg-surface-elevated rounded-lg p-3 border border-border">
                  <h4 className="font-medium text-sm text-content-secondary mb-3 uppercase tracking-wider">Economics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-content-secondary">Expected Revenue</span>
                      <span className="font-medium">₹{intelligenceResult.expected_revenue?.toLocaleString() || '---'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-content-secondary">Expected Cost</span>
                      <span className="font-medium">₹{intelligenceResult.expected_total_cost?.toLocaleString() || '---'}</span>
                    </div>
                    <div className="pt-2 mt-2 border-t border-border flex justify-between">
                      <span className="font-medium text-content">Expected Profit</span>
                      <span className={`font-bold ${
                        (intelligenceResult.expected_profit || 0) > 0 ? 'text-green-500' : 
                        (intelligenceResult.expected_profit || 0) < 0 ? 'text-red-500' : 'text-content'
                      }`}>
                        ₹{intelligenceResult.expected_profit?.toLocaleString() || '---'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm mt-1">
                      <span className="text-content-secondary">Margin</span>
                      <span className="font-medium">{intelligenceResult.expected_margin_pct?.toFixed(1) || '---'}%</span>
                    </div>
                  </div>
                </div>

                {/* Risk & Confidence */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-surface-elevated rounded-lg p-3 border border-border">
                    <div className="text-xs text-content-secondary uppercase tracking-wider mb-1">Risk Level</div>
                    <div className={`font-semibold ${
                      intelligenceResult.risk_level === 'HIGH' ? 'text-red-500' :
                      intelligenceResult.risk_level === 'MEDIUM' ? 'text-amber-500' : 'text-green-500'
                    }`}>{intelligenceResult.risk_level}</div>
                  </div>
                  <div className="bg-surface-elevated rounded-lg p-3 border border-border">
                    <div className="text-xs text-content-secondary uppercase tracking-wider mb-1">Confidence</div>
                    <div className="font-semibold text-content">{intelligenceResult.confidence_level}</div>
                  </div>
                </div>

                {/* Assumptions warning */}
                {intelligenceResult.assumptions.length > 0 && (
                  <div className="text-xs text-content-tertiary flex gap-1.5 items-start mt-4">
                    <Info className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                    <p>Based on {intelligenceResult.assumptions.filter(a => a.source.includes('default')).length} system defaults and {intelligenceResult.assumptions.filter(a => !a.source.includes('default')).length} actual data points. Snapshot will be saved on dispatch.</p>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
