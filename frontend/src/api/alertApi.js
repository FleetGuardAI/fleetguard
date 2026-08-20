import api from './client';

/**
 * Fetch alerts from the backend APIs (Fuel and SOS).
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getAlerts(params = {}) {
  const queryParams = {};
  if (params.days) queryParams.days = params.days;
  if (params.truck_id) queryParams.truck_id = params.truck_id;

  // Fetch both fuel alerts and SOS alerts in parallel
  const [fuelData, sosData] = await Promise.all([
    api.fuel.getAlerts(queryParams).catch(() => []),
    api.sos.list(queryParams).catch(() => [])
  ]);

  let alerts = [];

  // Map Fuel Alerts
  if (fuelData && fuelData.length > 0) {
    alerts = alerts.concat(fuelData.map(a => ({
      id: `fuel_${a.id}`,
      original_id: a.id,
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
    })));
  }

  // Map SOS Alerts
  if (sosData && sosData.length > 0) {
    alerts = alerts.concat(sosData.map(s => ({
      id: `sos_${s.id}`,
      original_id: s.id,
      type: 'emergency',
      level: 'critical',
      severity: 'critical',
      message: s.message || 'Driver Emergency SOS Triggered',
      truck_id: s.vehicle_id,
      driver_id: s.driver_id,
      timestamp: s.created_at,
      latitude: s.latitude,
      longitude: s.longitude,
      resolved: s.status === 'RESOLVED',
    })));
  }

  // Sort by timestamp descending
  alerts.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

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
 *
 * @param {string|number} id
 * @param {string} comment
 * @returns {Promise<object>}
 */
export async function resolveAlert(id, comment) {
  const idStr = String(id);
  if (idStr.startsWith('sos_')) {
    const originalId = idStr.replace('sos_', '');
    const sos = await api.sos.resolve(originalId, comment);
    return {
      id,
      resolved: true,
      resolutionComment: comment,
      resolved_by: sos.resolved_by,
      resolved_at: sos.resolved_at,
    };
  } else {
    // Fuel alerts are read from fuel_log; resolving is a local/UI action for now.
    return {
      id,
      resolved: true,
      resolutionComment: comment,
      resolved_by: 'Current User',
      resolved_at: new Date().toISOString(),
    };
  }
}
