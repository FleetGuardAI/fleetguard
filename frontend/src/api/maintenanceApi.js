import api from './client';

/**
 * Fetch maintenance records from the backend.
 * Supports status filter and search.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getMaintenanceLogs(params = {}) {
  const listParams = {};
  if (params.status) {
    listParams.status = params.status;
  }

  const records = await api.maintenance.list(listParams) || [];

  if (params.search) {
    const q = params.search.toLowerCase();
    return records.filter(m =>
      (m.business_id && m.business_id.toLowerCase().includes(q)) ||
      (m.category && m.category.toLowerCase().includes(q)) ||
      (m.workshop && m.workshop.toLowerCase().includes(q)) ||
      (m.service_provider && m.service_provider.toLowerCase().includes(q))
    );
  }

  return records;
}

/**
 * Get a single maintenance record by ID.
 *
 * @param {string|number} id
 * @returns {Promise<object>}
 */
export async function getMaintenanceById(id) {
  return await api.maintenance.get(id);
}

/**
 * Schedule maintenance via Operational Events.
 * Write operations go through the event system.
 *
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function scheduleMaintenance(data) {
  const payload = {
    event_type: 'maintenance.created',
    domain: 'maintenance',
    payload: {
      category: data.category || data.type || 'PREVENTIVE',
      vehicle_id: data.vehicle_id ? Number(data.vehicle_id) : null,
      workshop: data.workshop || null,
      service_provider: data.service_provider || null,
      scheduled_date: data.scheduled_date || data.date || null,
    },
  };
  return await api.events.create(payload);
}

/**
 * Get maintenance records for a specific vehicle.
 *
 * @param {string|number} vehicleId
 * @returns {Promise<Array>}
 */
export async function getMaintenanceByVehicle(vehicleId) {
  return await api.maintenance.byVehicle(vehicleId) || [];
}
