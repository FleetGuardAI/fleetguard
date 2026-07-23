import api from './client';

/**
 * Fetch all vehicles from the backend.
 * Uses the new Vehicle Domain API (/api/v1/vehicles) first, falls back to legacy /api/trucks.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getVehicles(params = {}) {
  const listParams = {};
  if (params.status) {
    listParams.is_active = params.status === 'active';
  }

  let vehicles;
  try {
    // Try the new Vehicle Domain API first
    vehicles = await api.vehicles.list(listParams) || [];
  } catch {
    // Fallback to legacy trucks API
    vehicles = await api.trucks.list(listParams) || [];
  }

  if (params.search) {
    const q = params.search.toLowerCase();
    return vehicles.filter(v =>
      (v.registration_number && v.registration_number.toLowerCase().includes(q)) ||
      (v.license_plate && v.license_plate.toLowerCase().includes(q)) ||
      (v.make && v.make.toLowerCase().includes(q)) ||
      (v.model && v.model.toLowerCase().includes(q))
    );
  }

  return vehicles;
}

/**
 * Fetch details of a single vehicle by ID.
 * Includes active trip from backend if available.
 *
 * @param {string|number} id
 * @returns {Promise<object>}
 */
export async function getVehicleById(id) {
  let vehicle;
  try {
    vehicle = await api.vehicles.get(id);
  } catch {
    vehicle = await api.trucks.get(id);
  }
  
  if (!vehicle) {
    throw new Error('Vehicle not found');
  }

  // Fetch active trip for this vehicle from the backend Trip Domain API
  let activeTrip = null;
  try {
    const trips = await api.trips.byVehicle(id, { status: 'IN_PROGRESS', limit: 1 });
    if (trips && trips.length > 0) {
      activeTrip = trips[0];
    }
  } catch {
    // Trip API may not have data yet, that's fine
  }

  return { ...vehicle, activeTrip };
}

/**
 * Create a new vehicle.
 *
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function createVehicle(data) {
  const payload = {
    license_plate: data.license_plate,
    make: data.make,
    model: data.model || null,
    year: data.year ? Number(data.year) : null,
    tank_capacity: data.tank_capacity ? Number(data.tank_capacity) : 400.0,
  };
  return await api.trucks.create(payload);
}

/**
 * Update a vehicle's details.
 *
 * @param {string|number} id
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function updateVehicle(id, data) {
  const payload = {};
  if (data.license_plate !== undefined) payload.license_plate = data.license_plate;
  if (data.make !== undefined) payload.make = data.make;
  if (data.model !== undefined) payload.model = data.model;
  if (data.year !== undefined) payload.year = data.year ? Number(data.year) : null;
  if (data.tank_capacity !== undefined) payload.tank_capacity = data.tank_capacity ? Number(data.tank_capacity) : null;
  if (data.is_active !== undefined) payload.is_active = data.is_active;

  return await api.trucks.update(id, payload);
}

/**
 * Fetch vehicle telemetry/fuel history from real fuel API.
 *
 * @param {string|number} id
 * @param {number} [hours=24]
 * @returns {Promise<Array>}
 */
export async function getVehicleHistory(id, hours = 24) {
  try {
    const fuelLogs = await api.fuel.getLogs(id, hours);
    return (fuelLogs || []).map((log, idx) => ({
      id: log.id || idx + 1,
      date: log.timestamp,
      status: log.speed > 0 ? 'moving' : 'stopped',
      speed: log.speed || 0,
      location: log.latitude && log.longitude
        ? `${log.latitude.toFixed(4)}, ${log.longitude.toFixed(4)}`
        : 'Unknown',
      fuelLevel: log.filtered_level || log.raw_level || 0,
    }));
  } catch {
    return [];
  }
}
