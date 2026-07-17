import api from './client';
import { mockTrips } from '@/data/mockData';

/**
 * Fetch all vehicles from the backend.
 * Filters by status and search terms on the client/server.
 * 
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getVehicles(params = {}) {
  const listParams = {};
  if (params.status) {
    listParams.is_active = params.status === 'active';
  }
  
  const trucks = await api.trucks.list(listParams) || [];

  // Filter client-side by search query since backend list_trucks does not filter search queries
  if (params.search) {
    const q = params.search.toLowerCase();
    return trucks.filter(v =>
      (v.license_plate && v.license_plate.toLowerCase().includes(q)) ||
      (v.make && v.make.toLowerCase().includes(q)) ||
      (v.model && v.model.toLowerCase().includes(q))
    );
  }

  return trucks;
}

/**
 * Fetch details of a single vehicle by ID.
 * 
 * @param {string|number} id
 * @returns {Promise<object>}
 */
export async function getVehicleById(id) {
  const truck = await api.trucks.get(id);
  if (!truck) {
    throw new Error('Vehicle not found');
  }
  
  // Find associated active trip if any from mockData (since backend has no Trip model/endpoints)
  const activeTrip = mockTrips.find(tr => tr.truck_id === truck.id && tr.status === 'on-trip');
  return { ...truck, activeTrip };
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
 * Fetch vehicle location/telemetry history.
 * Placeholder mock as there is no backend equivalent.
 * 
 * @param {string|number} id
 * @returns {Promise<Array>}
 */
export async function getVehicleHistory(id) {
  return [
    { id: 1, date: new Date(Date.now() - 3600000).toISOString(), status: 'moving', speed: 65, location: 'Near Udaipur, NH-48', fuelLevel: 280 },
    { id: 2, date: new Date(Date.now() - 7200000).toISOString(), status: 'moving', speed: 70, location: 'Near Pali, NH-48', fuelLevel: 295 },
    { id: 3, date: new Date(Date.now() - 10800000).toISOString(), status: 'stopped', speed: 0, location: 'Dhaba Midway, Ajmer', fuelLevel: 300 }
  ];
}
