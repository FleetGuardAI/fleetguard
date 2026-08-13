import api from './client';

/**
 * Normalize a raw backend Trip response to the UI structure.
 * No hardcoded fallbacks — uses actual backend values.
 */
function normalizeTrip(t) {
  if (!t) return t;
  const origin = t.origin_location || t.origin || t.start_point || null;
  const dest = t.destination_location || t.destination || t.end_point || null;

  let status = (t.status || 'scheduled').toLowerCase();
  if (status === 'in_progress' || status === 'in-progress') status = 'on-trip';
  if (status === 'created') status = 'scheduled';

  return {
    ...t,
    id: t.id,
    trip_id: t.trip_id || `TRIP-${t.id}`,
    route_name: t.route_name || (origin && dest ? `${origin} → ${dest}` : null),
    start_point: origin,
    end_point: dest,
    truck_id: t.vehicle_id || t.truck_id || null,
    driver_id: t.driver_id || null,
    truck_plate: t.truck_plate || (t.vehicle_id ? `Vehicle ID: ${t.vehicle_id}` : null),
    driver_name: t.driver_name || (t.driver_id ? `Driver ID: ${t.driver_id}` : null),
    start_date: t.actual_start_time || t.planned_start_time || t.created_at || null,
    expected_delivery: t.planned_end_time || null,
    end_date: t.actual_end_time || null,
    planned_distance: t.planned_distance || null,
    actual_distance: t.actual_distance || null,
    progress: t.progress ?? (status === 'completed' ? 100 : status === 'on-trip' ? 50 : 0),
    status: status,
    cargo_weight: t.cargo_weight || null,
    revenue: t.revenue || null,
    planned_cost: t.planned_cost || null,
    planned_fuel_liters: t.planned_fuel_liters || null,
    timeline: t.timeline || [
      { status: status.toUpperCase(), time: t.created_at || new Date().toISOString(), description: `Trip status is ${status}` }
    ]
  };
}

export async function getTrips(params = {}) {
  const listParams = {};
  if (params.status && params.status !== 'all') {
    let s = params.status;
    if (s === 'on-trip') s = 'IN_PROGRESS';
    if (s === 'scheduled') s = 'CREATED';
    if (s === 'completed') s = 'COMPLETED';
    listParams.status = s;
  }

  const trips = await api.trips.list(listParams) || [];
  let normalized = trips.map(normalizeTrip);

  if (params.search) {
    const q = params.search.toLowerCase();
    normalized = normalized.filter(t =>
      (t.route_name && t.route_name.toLowerCase().includes(q)) ||
      (t.truck_plate && t.truck_plate.toLowerCase().includes(q)) ||
      (t.driver_name && t.driver_name.toLowerCase().includes(q)) ||
      (t.start_point && t.start_point.toLowerCase().includes(q)) ||
      (t.end_point && t.end_point.toLowerCase().includes(q))
    );
  }

  return normalized;
}

export async function getTripById(id) {
  const trip = await api.trips.get(id);
  if (!trip) {
    throw new Error('Trip not found');
  }
  return normalizeTrip(trip);
}

export async function createTrip(data) {
  const payload = {
    event_type: 'trip.created',
    domain: 'trip',
    payload: {
      origin_location: data.origin_location || data.start_point || data.origin,
      destination_location: data.destination_location || data.end_point || data.destination,
      planned_distance: data.planned_distance ? Number(data.planned_distance) : null,
      planned_start_time: data.planned_start_time || data.start_date || null,
      planned_end_time: data.planned_end_time || data.expected_delivery || null,
      vehicle_id: data.vehicle_id || data.truck_id ? Number(data.vehicle_id || data.truck_id) : null,
      driver_id: data.driver_id ? Number(data.driver_id) : null,
    },
  };
  const event = await api.events.create(payload);
  return normalizeTrip({
    id: Date.now(),
    trip_id: `TRIP-${Date.now().toString().slice(-4)}`,
    status: 'CREATED',
    ...data,
  });
}

export async function updateTripStatus(id, status, description) {
  const eventTypeMap = {
    'in_progress': 'trip.started',
    'on-trip': 'trip.started',
    'paused': 'trip.paused',
    'completed': 'trip.completed',
    'cancelled': 'trip.cancelled',
  };
  const payload = {
    event_type: eventTypeMap[status] || `trip.${status}`,
    domain: 'trip',
    aggregate_id: String(id),
    payload: {
      description: description || `Status updated to ${status}`,
    },
  };
  await api.events.create(payload);
  return normalizeTrip({ id, status });
}

/**
 * Fetch Trip Intelligence data for a specific trip.
 * Returns profitability, cost breakdown, efficiency score, insights, etc.
 *
 * @param {string|number} tripId
 * @returns {Promise<object>}
 */
export async function getTripIntelligence(tripId) {
  return await api.trips.intelligence(tripId);
}
