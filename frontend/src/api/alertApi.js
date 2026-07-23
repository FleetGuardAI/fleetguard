import api from './client';

/**
 * Fetch alerts from the backend fuel alerts API.
 * Maps fuel theft alerts to the generic alert structure.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getAlerts(params = {}) {
  const queryParams = {};
  if (params.days) queryParams.days = params.days;
  if (params.truck_id) queryParams.truck_id = params.truck_id;

  const fuelAlerts = await api.fuel.getAlerts(queryParams) || [];

  let alerts = fuelAlerts.map(a => ({
    id: a.id,
    type: 'fuel_theft',
    level: a.fuel_drop_liters > 30 ? 'critical' : a.fuel_drop_liters > 15 ? 'warning' : 'info',
    severity: a.fuel_drop_liters > 30 ? 'critical' : a.fuel_drop_liters > 15 ? 'warning' : 'info',
    message: `Fuel drop of ${a.fuel_drop_liters?.toFixed(1)}L detected`,
    truck_id: a.truck_id,
    truck_plate: a.truck_plate,
    timestamp: a.timestamp,
    fuel_drop_liters: a.fuel_drop_liters,
    latitude: a.latitude,
    longitude: a.longitude,
    speed: a.speed,
    resolved: false,
  }));

  if (params.search) {
    const q = params.search.toLowerCase();
    alerts = alerts.filter(a =>
      (a.truck_plate && a.truck_plate.toLowerCase().includes(q)) ||
      (a.type && a.type.toLowerCase().includes(q)) ||
      (a.message && a.message.toLowerCase().includes(q))
    );
  }

  if (params.severity) {
    alerts = alerts.filter(a => a.level === params.severity);
  }

  if (params.resolved !== undefined) {
    alerts = alerts.filter(a => a.resolved === params.resolved);
  }

  return alerts;
}

/**
 * Resolve an alert.
 * Since there's no dedicated alerts backend, this is a client-side action.
 *
 * @param {string|number} id
 * @param {string} comment
 * @returns {Promise<object>}
 */
export async function resolveAlert(id, comment) {
  // Fuel alerts are read from fuel_log; resolving is a local/UI action for now.
  // In Phase 3 this would post a resolution event.
  return {
    id,
    resolved: true,
    resolutionComment: comment,
    resolved_by: 'Current User',
    resolved_at: new Date().toISOString(),
  };
}
