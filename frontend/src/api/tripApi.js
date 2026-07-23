import api from './client';

/**
 * Fetch all trips from the backend Trip Domain API.
 * Supports status filter and search.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getTrips(params = {}) {
  const listParams = {};
  if (params.status) {
    listParams.status = params.status;
  }

  const trips = await api.trips.list(listParams) || [];

  if (params.search) {
    const q = params.search.toLowerCase();
    return trips.filter(t =>
      (t.origin_location && t.origin_location.toLowerCase().includes(q)) ||
      (t.destination_location && t.destination_location.toLowerCase().includes(q)) ||
      (t.trip_id && t.trip_id.toLowerCase().includes(q))
    );
  }

  return trips;
}

/**
 * Fetch details of a single trip by ID.
 *
 * @param {string|number} id
 * @returns {Promise<object>}
 */
export async function getTripById(id) {
  const trip = await api.trips.get(id);
  if (!trip) {
    throw new Error('Trip not found');
  }
  return trip;
}

/**
 * Create a new trip via Operational Events.
 * Trip creation goes through the event system; this posts an operational event.
 *
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function createTrip(data) {
  const payload = {
    event_type: 'trip.created',
    domain: 'trip',
    payload: {
      origin_location: data.origin_location || data.origin,
      destination_location: data.destination_location || data.destination,
      planned_distance: data.planned_distance ? Number(data.planned_distance) : null,
      planned_start_time: data.planned_start_time || data.start_time || null,
      planned_end_time: data.planned_end_time || data.end_time || null,
      vehicle_id: data.vehicle_id ? Number(data.vehicle_id) : null,
      driver_id: data.driver_id ? Number(data.driver_id) : null,
    },
  };
  return await api.events.create(payload);
}

/**
 * Update trip status via Operational Events.
 *
 * @param {string|number} id
 * @param {string} status
 * @param {string} [description]
 * @returns {Promise<object>}
 */
export async function updateTripStatus(id, status, description) {
  const eventTypeMap = {
    'in_progress': 'trip.started',
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
  return await api.events.create(payload);
}
