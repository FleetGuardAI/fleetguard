import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Truck, User, Calendar, MapPin, DollarSign, Activity, AlertCircle, Loader2 } from 'lucide-react';
import { getVehicles } from '@/api/vehicleApi';
import { getDrivers } from '@/api/driverApi';
import { createTrip, evaluateTripIntelligence } from '@/api/tripApi';
import { locationApi } from '@/api/locationApi';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

import { useToast } from '@/components/ui/Toast';
import { LocationAutocomplete } from '@/components/trip/LocationAutocomplete';
import { RouteMap } from '@/components/trip/RouteMap';
import { IntelligencePanel } from '@/components/trip/IntelligencePanel';
import { motion } from 'framer-motion';
import { cn } from '@/utils/cn';

export default function TripForm() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [loading, setLoading] = useState(false);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  
  // Trip Data
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [routeData, setRouteData] = useState(null);
  
  const [formData, setFormData] = useState({
    vehicle_id: '',
    driver_id: '',
    planned_start_time: '',
    planned_end_time: '',
    revenue: '',
    cargo_weight: ''
  });

  // Intelligence State
  const [intelligence, setIntelligence] = useState(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState(null);

  useEffect(() => {
    Promise.all([getVehicles(), getDrivers()])
      .then(([v, d]) => {
        setVehicles(v);
        setDrivers(d);
      })
      .catch(err => error('Load Error', 'Failed to load master data.'));
  }, []);

  // Effect: Auto-calculate route when origin and destination change
  useEffect(() => {
    if (origin?.lat && destination?.lat) {
      const fetchRoute = async () => {
        try {
          const res = await locationApi.calculateRoute({
            origin_lat: origin.lat,
            origin_lng: origin.lng,
            destination_lat: destination.lat,
            destination_lng: destination.lng
          });
          // Decode polyline for map
          // res.polyline = encoded polyline string from RouteCalculationResponse
          const encodedPoly = res.polyline;
          console.log("[TripForm] Route result:", {
            distance_km: res.distance_km,
            duration_hours: res.duration_hours,
            source: res.source,
            encoded_polyline_exists: !!encodedPoly,
            encoded_polyline_length: encodedPoly?.length ?? 0
          });
          const polylinePoints = locationApi.decodePolyline(encodedPoly);
          console.log("[TripForm] Decoded polyline points:", polylinePoints.length, "first:", polylinePoints[0], "last:", polylinePoints[polylinePoints.length - 1]);
          setRouteData({ ...res, polylineArray: polylinePoints });
        } catch (e) {
          console.error("Routing error:", e);
        }
      };
      fetchRoute();
    } else {
      setRouteData(null);
    }
  }, [origin, destination]);

  // Effect: Debounced Progressive Intelligence Evaluation
  useEffect(() => {
    const timer = setTimeout(async () => {
      // Don't evaluate if we have absolutely nothing
      if (!origin && !destination && !formData.vehicle_id && !formData.revenue) {
        setIntelligence(null);
        return;
      }

      setEvaluating(true);
      setEvalError(null);
      try {
        const payload = {
          origin_location: origin?.address || origin?.description || origin?.main_text || null,
          origin_lat: origin?.lat,
          origin_lng: origin?.lng,
          origin_place_id: origin?.place_id,
          destination_location: destination?.address || destination?.description || destination?.main_text || null,
          destination_lat: destination?.lat,
          destination_lng: destination?.lng,
          destination_place_id: destination?.place_id,
          route_distance_km: routeData?.distance_km,
          route_duration_hours: routeData?.duration_hours,
          vehicle_id: formData.vehicle_id ? Number(formData.vehicle_id) : null,
          driver_id: formData.driver_id ? Number(formData.driver_id) : null,
          revenue: formData.revenue ? Number(formData.revenue) : null,
          planned_start_time: formData.planned_start_time || null,
          planned_end_time: formData.planned_end_time || null
        };
        
        console.log("[TripForm] Sending Intelligence Payload:", payload);
        const intel = await evaluateTripIntelligence(payload);
        console.log("[TripForm] Intelligence Response:", intel);
        setIntelligence(intel);
      } catch (e) {
        console.error("[TripForm] Intelligence Eval Error:", e);
        setEvalError(e.message || "Failed to evaluate trip economics.");
        // Explicitly clear intelligence if it fails so it doesn't get stuck in a weird state
        // But we handle UI loading state explicitly below
      } finally {
        setEvaluating(false);
      }
    }, 800); // 800ms debounce

    return () => clearTimeout(timer);
  }, [origin, destination, routeData, formData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!origin || !destination) {
      error('Validation Error', 'Please select pickup and dropoff locations.');
      return;
    }
    if (!formData.vehicle_id || !formData.driver_id) {
      error('Validation Error', 'Please assign a vehicle and driver.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...formData,
        origin_location: origin.address || origin.description,
        origin_lat: origin.lat,
        origin_lng: origin.lng,
        origin_place_id: origin.place_id,
        origin_address: origin.address,
        destination_location: destination.address || destination.description,
        destination_lat: destination.lat,
        destination_lng: destination.lng,
        destination_place_id: destination.place_id,
        destination_address: destination.address,
        route_distance_km: routeData?.distance_km,
        route_duration_hours: routeData?.duration_hours,
        route_toll_estimate: routeData?.toll_estimate,
        route_provider: routeData?.source,
        route_polyline: routeData?.polyline,
        revenue: formData.revenue ? Number(formData.revenue) : null,
        cargo_weight: formData.cargo_weight ? Number(formData.cargo_weight) : null,
      };
      
      const trip = await createTrip(payload);
      success('Dispatch Successful', `Trip ${trip.trip_id} created.`);
      navigate(`/trips/${trip.id}`);
    } catch (e) {
      error('Dispatch Error', e.message || 'Failed to dispatch trip.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full mb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content flex items-center gap-2">
            Intelligent Dispatch
            <Badge variant="brand" className="ml-2">Trip Intel 2.0</Badge>
          </h1>
          <p className="text-content-muted">Progressive evaluation powered by the vahan AI</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN: Inputs */}
        <div className="lg:col-span-5 space-y-6">
          <form id="trip-form" onSubmit={handleSubmit} className="space-y-6">
            
            {/* 1. Route Section */}
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-content mb-4 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-brand-500" />
                1. Route Selection
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-content mb-1">Pickup Location</label>
                  <LocationAutocomplete 
                    value={origin} 
                    onChange={setOrigin} 
                    placeholder="Search origin..." 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-content mb-1">Dropoff Location</label>
                  <LocationAutocomplete 
                    value={destination} 
                    onChange={setDestination} 
                    placeholder="Search destination..." 
                  />
                </div>

                {origin?.lat && destination?.lat && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                    <RouteMap 
                      origin={origin} 
                      destination={destination} 
                      routePolyline={routeData?.polylineArray} 
                    />
                    {routeData && (
                      <div className="flex justify-between items-center mt-3 text-sm text-content-muted px-2">
                        <span>Distance: <strong>{routeData.distance_km?.toFixed(0)} km</strong></span>
                        <span>Time: <strong>{routeData.duration_hours?.toFixed(1)} hrs</strong></span>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </Card>

            {/* 2. Assignment Section */}
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-content mb-4 flex items-center gap-2">
                <Truck className="w-5 h-5 text-brand-500" />
                2. Assignment
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-content mb-1">Assign Truck</label>
                  <Select
                    value={formData.vehicle_id}
                    onChange={(e) => setFormData({...formData, vehicle_id: e.target.value})}
                  >
                    <option value="">Select Truck</option>
                    {vehicles.map(v => (
                      <option key={v.id} value={v.id}>{v.registration_number}</option>
                    ))}
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-content mb-1">Assign Driver</label>
                  <Select
                    value={formData.driver_id}
                    onChange={(e) => setFormData({...formData, driver_id: e.target.value})}
                  >
                    <option value="">Select Driver</option>
                    {drivers.length === 0 ? (
                      <option disabled value="">No eligible drivers available</option>
                    ) : (
                      drivers.map(d => (
                        <option key={d.id} value={d.id}>{d.name || d.driver_name || d.id}</option>
                      ))
                    )}
                  </Select>
                </div>
              </div>
            </Card>

            {/* 3. Freight & Timings */}
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-content mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-brand-500" />
                3. Freight & Schedule
              </h2>
              <div className="space-y-4">
                <Input
                  label="Expected Freight Revenue (₹)"
                  type="number"
                  placeholder="e.g., 45000"
                  icon={<DollarSign className="w-4 h-4" />}
                  value={formData.revenue}
                  onChange={(e) => setFormData({...formData, revenue: e.target.value})}
                />
                
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Start Date/Time"
                    type="datetime-local"
                    icon={<Calendar className="w-4 h-4" />}
                    value={formData.planned_start_time}
                    onChange={(e) => setFormData({...formData, planned_start_time: e.target.value})}
                  />
                  <Input
                    label="Expected Delivery"
                    type="datetime-local"
                    icon={<Calendar className="w-4 h-4" />}
                    value={formData.planned_end_time}
                    onChange={(e) => setFormData({...formData, planned_end_time: e.target.value})}
                  />
                </div>
                
                <Input
                  label="Cargo Weight (Tons) - Optional"
                  type="number"
                  placeholder="e.g., 18"
                  value={formData.cargo_weight}
                  onChange={(e) => setFormData({...formData, cargo_weight: e.target.value})}
                />
              </div>
            </Card>

          </form>
        </div>

        {/* RIGHT COLUMN: Intelligence */}
        <div className="lg:col-span-7">
          <div className="sticky top-6">
            <IntelligencePanel 
              intelligence={intelligence} 
              isLoading={evaluating} 
              error={evalError}
            />
            
            <div className="mt-6 flex justify-end gap-4">
              <Button variant="outline" onClick={() => navigate('/trips')}>Cancel</Button>
              <Button 
                type="submit" 
                form="trip-form"
                loading={loading}
                disabled={!origin || !destination || !formData.vehicle_id || !formData.driver_id}
                variant={intelligence?.recommendation === 'AVOID' ? 'destructive' : 'brand'}
              >
                Dispatch Trip
              </Button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// Simple Badge fallback if missing
function Badge({ children, variant, className }) {
  return (
    <span className={cn(
      "px-2 py-0.5 text-xs font-semibold rounded-full",
      variant === 'brand' ? "bg-brand-100 text-brand-800" : "bg-gray-100 text-gray-800",
      className
    )}>
      {children}
    </span>
  );
}
