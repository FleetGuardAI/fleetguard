import api from './client';

/**
 * Fetch live telematics locations for the fleet map.
 * 
 * @returns {Promise<Array>}
 */
export async function getLiveTracking() {
  try {
    const liveLocations = await api.telematics.getLiveFleet();
    return liveLocations.map(loc => ({
      id: loc.driver_id,
      driver_name: loc.driver_name,
      vehicle_id: loc.vehicle_id,
      vehicle_registration: loc.vehicle_registration,
      trip_id: loc.trip_id,
      lat: loc.latitude,
      lng: loc.longitude,
      speed: loc.speed || 0,
      heading: loc.heading || 0,
      battery: loc.battery_percent || 100,
      status: loc.duty_status === 'ON_DUTY' ? 'active' : 'idle',
      lastUpdate: loc.last_updated,
    }));
  } catch (err) {
    console.error("Failed to fetch live telematics data", err);
    return [];
  }
}

export async function getDriverHistory(driverId, startTime = null, endTime = null) {
  let url = `/tracking/driver/${driverId}/history`;
  const params = new URLSearchParams();
  if (startTime) params.append('start_time', startTime.toISOString());
  if (endTime) params.append('end_time', endTime.toISOString());
  
  if (params.toString()) {
    url += `?${params.toString()}`;
  }
  const { data } = await api.client.get(url);
  return data;
}

export async function getTripRoute(tripId) {
  const { data } = await api.client.get(`/tracking/trip/${tripId}/route`);
  return data;
}
