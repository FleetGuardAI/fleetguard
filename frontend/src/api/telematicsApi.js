import api from './client';

/**
 * Fetch live telematics locations for all fleet trucks.
 * 
 * @returns {Promise<Array>}
 */
export async function getLiveTracking() {
  try {
    const liveLocations = await api.telematics.getLiveFleet();
    return (liveLocations || []).map(loc => ({
      id: loc.driver_id,
      driver_name: loc.driver_name,
      vehicle_id: loc.vehicle_id,
      vehicle_registration: loc.vehicle_registration,
      trip_id: loc.trip_id,
      lat: loc.latitude,
      lng: loc.longitude,
      speed: loc.speed || 0,
      speed_kmh: loc.speed_kmh || (loc.speed ? Math.round(loc.speed * 3.6 * 10) / 10 : 0),
      heading: loc.heading || 0,
      battery: loc.battery_percent || 100,
      status: loc.duty_status === 'ON_DUTY' ? 'active' : 'idle',
      duty_status: loc.duty_status,
      lastUpdate: loc.last_updated,
    }));
  } catch (err) {
    console.error("Failed to fetch live telematics data", err);
    return [];
  }
}

/**
 * Fetch drivers list enriched with assigned vehicle, trip counts, and GPS status.
 * Company-scoped.
 */
export async function getTrackingDrivers(params = {}, signal = null) {
  const query = new URLSearchParams();
  if (params.search) query.append('search', params.search);
  if (params.duty_status) query.append('duty_status', params.duty_status);
  if (params.has_trips !== undefined && params.has_trips !== null) query.append('has_trips', params.has_trips);
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.limit) query.append('limit', params.limit);
  if (params.offset) query.append('offset', params.offset);

  const qs = query.toString();
  const url = `/v1/tracking/drivers${qs ? `?${qs}` : ''}`;
  return await api.get(url, { signal });
}

/**
 * Fetch trips for a specific driver with GPS point counts.
 */
export async function getDriverTrips(driverId, params = {}, signal = null) {
  const query = new URLSearchParams();
  if (params.start_time) {
    const st = params.start_time instanceof Date ? params.start_time.toISOString() : params.start_time;
    query.append('start_time', st);
  }
  if (params.end_time) {
    const et = params.end_time instanceof Date ? params.end_time.toISOString() : params.end_time;
    query.append('end_time', et);
  }
  if (params.status && params.status !== 'all') query.append('status', params.status);
  if (params.limit) query.append('limit', params.limit);
  if (params.offset) query.append('offset', params.offset);

  const qs = query.toString();
  const url = `/v1/tracking/driver/${driverId}/trips${qs ? `?${qs}` : ''}`;
  return await api.get(url, { signal });
}

/**
 * Fetch paginated, chronological GPS points with gaps, stops, and bounding box.
 */
export async function getDriverLocations(driverId, params = {}, signal = null) {
  const query = new URLSearchParams();
  if (params.start_time) {
    const st = params.start_time instanceof Date ? params.start_time.toISOString() : params.start_time;
    query.append('start_time', st);
  }
  if (params.end_time) {
    const et = params.end_time instanceof Date ? params.end_time.toISOString() : params.end_time;
    query.append('end_time', et);
  }
  if (params.trip_id) query.append('trip_id', params.trip_id);
  if (params.page) query.append('page', params.page);
  if (params.page_size) query.append('page_size', params.page_size);
  if (params.downsample_max) query.append('downsample_max', params.downsample_max);

  const qs = query.toString();
  const url = `/v1/tracking/driver/${driverId}/locations${qs ? `?${qs}` : ''}`;
  return await api.get(url, { signal });
}

/**
 * Fetch deterministic operational analytics for a driver's GPS track.
 */
export async function getDriverAnalytics(driverId, params = {}, signal = null) {
  const query = new URLSearchParams();
  if (params.start_time) {
    const st = params.start_time instanceof Date ? params.start_time.toISOString() : params.start_time;
    query.append('start_time', st);
  }
  if (params.end_time) {
    const et = params.end_time instanceof Date ? params.end_time.toISOString() : params.end_time;
    query.append('end_time', et);
  }
  if (params.trip_id) query.append('trip_id', params.trip_id);

  const qs = query.toString();
  const url = `/v1/tracking/driver/${driverId}/analytics${qs ? `?${qs}` : ''}`;
  return await api.get(url, { signal });
}

/**
 * Fetch a driver's latest live known location.
 */
export async function getDriverLiveLocation(driverId, signal = null) {
  return await api.get(`/v1/tracking/driver/${driverId}/live`, { signal });
}

/**
 * Fetch route history for a specific trip by ID or business identifier.
 */
export async function getTripRoute(tripId, signal = null) {
  return await api.get(`/v1/tracking/trip/${tripId}/route`, { signal });
}

/**
 * Legacy driver history helper.
 */
export async function getDriverHistory(driverId, startTime = null, endTime = null, signal = null) {
  let url = `/v1/tracking/driver/${driverId}/history`;
  const params = new URLSearchParams();
  if (startTime) {
    const st = startTime instanceof Date ? startTime.toISOString() : startTime;
    params.append('start_time', st);
  }
  if (endTime) {
    const et = endTime instanceof Date ? endTime.toISOString() : endTime;
    params.append('end_time', et);
  }
  
  if (params.toString()) {
    url += `?${params.toString()}`;
  }
  return await api.get(url, { signal });
}
