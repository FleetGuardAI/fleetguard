import api from './client';

/**
 * Fetch fuel logs from the backend.
 * Normalizes entries into a standardized fuel log structure for UI display.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getFuelLogs(params = {}) {
  let records = [];

  if (params.truck_id) {
    const raw = await api.fuel.getLogs(params.truck_id, params.hours || 24) || [];
    records = raw.map(l => ({
      id: l.id,
      truck_id: l.vehicle_id,
      truck_plate: l.truck_plate || (l.vehicle_id ? `Vehicle ID: ${l.vehicle_id}` : 'Unassigned'),
      date: l.timestamp,
      quantity_liters: l.quantity_liters || l.volume_liters || 0,
      price_per_liter: l.price_per_liter || 0,
      total_amount: l.total_amount || l.amount || 0,
      station: l.station || l.vendor_name || 'Station',
      status: (l.status || 'COMPLETED').toUpperCase(),
      receipt_url: null,
    }));
  } else {
    // If no truck_id specified, return fuel alerts normalized as fuel directory entries
    const alerts = await api.fuel.getAlerts({ days: 30 }) || [];
    records = alerts.map(a => ({
      id: a.id,
      truck_id: a.truck_id,
      truck_plate: a.truck_plate || (a.truck_id ? `Vehicle ID: ${a.truck_id}` : 'Vehicle'),
      date: a.timestamp || a.created_at,
      quantity_liters: a.fuel_drop_liters ? Number(a.fuel_drop_liters.toFixed(1)) : 0,
      price_per_liter: 95.0,
      total_amount: Math.round((a.fuel_drop_liters || 0) * 95),
      station: a.latitude && a.longitude ? `GPS (${a.latitude.toFixed(2)}, ${a.longitude.toFixed(2)})` : 'Telematics Event',
      status: 'flagged',
      receipt_url: null,
    }));
  }

  if (params.search) {
    const q = params.search.toLowerCase();
    records = records.filter(r =>
      (r.truck_plate && r.truck_plate.toLowerCase().includes(q)) ||
      (r.station && r.station.toLowerCase().includes(q))
    );
  }

  return records;
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
