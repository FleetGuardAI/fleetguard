import api from './client';

/**
 * Normalizes backend TyreResponse object for UI display.
 */
function normalizeTyre(t) {
  if (!t) return t;
  return {
    ...t,
    id: t.id,
    serial_number: t.serial_number || `TYRE-${t.id}`,
    manufacturer: t.manufacturer || null,
    brand: t.brand || null,
    model: t.model || null,
    size: t.size || null,
    current_status: (t.current_status || 'available').toLowerCase(),
    current_vehicle_id: t.current_vehicle_id || null,
    current_position: t.current_position || null,
    purchase_information: t.purchase_information || {},
    lifecycle_records: t.lifecycle_records || [],
  };
}

export async function getTyres(params = {}) {
  const listParams = {};
  if (params.status && params.status !== 'all') {
    listParams.status = params.status.toUpperCase();
  }

  const records = await api.tyres.list(listParams) || [];
  let normalized = records.map(normalizeTyre);

  if (params.search) {
    const q = params.search.toLowerCase();
    normalized = normalized.filter(t =>
      (t.serial_number && t.serial_number.toLowerCase().includes(q)) ||
      (t.brand && t.brand.toLowerCase().includes(q)) ||
      (t.manufacturer && t.manufacturer.toLowerCase().includes(q)) ||
      (t.size && t.size.toLowerCase().includes(q))
    );
  }

  return normalized;
}

export async function getTyreById(id) {
  const record = await api.tyres.get(id);
  return normalizeTyre(record);
}

export async function getTyresByVehicle(vehicleId) {
  const records = await api.tyres.byVehicle(vehicleId) || [];
  return records.map(normalizeTyre);
}
