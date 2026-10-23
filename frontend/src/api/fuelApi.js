import api from './client';

/**
 * Fetch manual fuel transactions from the backend.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getFuelLogs(params = {}) {
  let records = [];

  try {
    let queryParams = {};
    if (params.truck_id) {
      queryParams.vehicle_id = params.truck_id;
    }
    
    // Hit the new manual transactions endpoint
    const transactions = await api.fuel.getTransactions(queryParams) || [];
    
    records = transactions.map(t => ({
      id: t.id,
      truck_id: t.vehicle_id,
      truck_plate: `Vehicle ID: ${t.vehicle_id}`, // Ideally joined with vehicle table in backend if needed
      date: t.timestamp,
      quantity_liters: t.amount_liters || 0,
      price_per_liter: t.price_per_liter || 0,
      total_amount: t.total_cost || 0,
      station: t.station || '-',
      odometer: t.odometer,
      status: 'COMPLETED',
      receipt_url: t.receipt_url,
    }));

    if (params.search) {
      const q = params.search.toLowerCase();
      records = records.filter(r =>
        (r.truck_plate && r.truck_plate.toLowerCase().includes(q)) ||
        (r.station && r.station.toLowerCase().includes(q))
      );
    }
  } catch (error) {
    console.error("Failed to fetch fuel transactions:", error);
  }

  return records;
}

/**
 * Create a manual fuel transaction entry.
 *
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function createFuelEntry(data) {
  return await api.fuel.createTransaction({
    vehicle_id: Number(data.truck_id),
    driver_id: data.driver_id ? Number(data.driver_id) : null,
    trip_id: data.trip_id ? Number(data.trip_id) : null,
    fuel_type: "DIESEL",
    quantity_liters: Number(data.quantity_liters || 0),
    price_per_liter: Number(data.price_per_liter || 0),
    odometer: data.odometer ? Number(data.odometer) : null,
    station: data.station || null,
    receipt_url: data.receipt_url || null,
    occurred_at: data.timestamp || new Date().toISOString(),
    description: data.description || null
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
