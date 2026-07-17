import api from './client';

/**
 * Fetch all drivers from the backend.
 * Filters by status and search terms.
 * 
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getDrivers(params = {}) {
  const listParams = {};
  if (params.status) {
    listParams.is_active = params.status === 'active';
  }
  
  const drivers = await api.drivers.list(listParams) || [];

  if (params.search) {
    const q = params.search.toLowerCase();
    return drivers.filter(d =>
      (d.name && d.name.toLowerCase().includes(q)) ||
      (d.phone_number && d.phone_number.includes(q))
    );
  }

  return drivers;
}

/**
 * Fetch details of a single driver by ID.
 * 
 * @param {string|number} id
 * @returns {Promise<object>}
 */
export async function getDriverById(id) {
  const driver = await api.drivers.get(id);
  if (!driver) {
    throw new Error('Driver not found');
  }
  
  // Return driver; assignTruck is null for backend compatibility
  return { ...driver, assignedTruck: null };
}

/**
 * Register a new driver in the fleet.
 * 
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function createDriver(data) {
  const payload = {
    name: data.name,
    phone_number: data.phone_number,
    avatar_url: data.avatar_url || null,
  };
  return await api.drivers.create(payload);
}

/**
 * Update driver profile details.
 * 
 * @param {string|number} id
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function updateDriver(id, data) {
  const payload = {};
  if (data.name !== undefined) payload.name = data.name;
  if (data.phone_number !== undefined) payload.phone_number = data.phone_number;
  if (data.avatar_url !== undefined) payload.avatar_url = data.avatar_url;
  if (data.risk_score !== undefined) payload.risk_score = Number(data.risk_score);
  if (data.rating !== undefined) payload.rating = Number(data.rating);
  if (data.is_active !== undefined) payload.is_active = data.is_active;

  return await api.drivers.update(id, payload);
}

/**
 * Assign a vehicle to a driver.
 * Placeholder mock for frontend compatibility.
 * 
 * @param {string|number} driverId
 * @param {string|number} vehicleId
 * @returns {Promise<object>}
 */
export async function assignVehicle(driverId, vehicleId) {
  return { success: true, message: `Vehicle ID ${vehicleId} assigned to driver ID ${driverId}.` };
}
