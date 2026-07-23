import api from './client';

/**
 * Fetch fuel logs from the backend.
 * Uses the fuel chart endpoint with the first available vehicle, or all alerts.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getFuelLogs(params = {}) {
  if (params.truck_id) {
    const logs = await api.fuel.getLogs(params.truck_id, params.hours || 24) || [];
    if (params.search) {
      const q = params.search.toLowerCase();
      return logs.filter(l =>
        (l.vehicle_id && String(l.vehicle_id).includes(q))
      );
    }
    return logs;
  }

  // If no truck_id specified, return fuel alerts as a log-like list
  const alerts = await api.fuel.getAlerts({ days: 30 }) || [];
  if (params.search) {
    const q = params.search.toLowerCase();
    return alerts.filter(a =>
      (a.truck_plate && a.truck_plate.toLowerCase().includes(q))
    );
  }
  return alerts;
}

/**
 * Create a fuel log entry via the ingest endpoint.
 *
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function createFuelEntry(data) {
  return await api.fuel.ingest({
    truck_id: Number(data.truck_id),
    timestamp: data.timestamp || new Date().toISOString(),
    raw_level: Number(data.raw_level || data.liters || 0),
    expected_level: Number(data.expected_level || 0),
    speed: Number(data.speed || 0),
    latitude: data.latitude || null,
    longitude: data.longitude || null,
  });
}

/**
 * Fetch fuel telemetry chart data for a specific vehicle.
 *
 * @param {string|number} truckId
 * @param {number} [hours=24]
 * @returns {Promise<Array>}
 */
export async function getFuelTelemetry(truckId, hours = 24) {
  return await api.fuel.getChartData(truckId, hours) || [];
}

/**
 * Fetch fuel theft alerts from the backend.
 *
 * @param {object} [params]
 * @returns {Promise<Array>}
 */
export async function getFuelAlerts(params = {}) {
  return await api.fuel.getAlerts(params) || [];
}
