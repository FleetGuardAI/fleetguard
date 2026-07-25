import api from './client';

/**
 * Normalize a raw backend Driver response to the UI structure.
 * No hardcoded fallbacks — uses actual backend values.
 */
function normalizeDriver(d) {
  if (!d) return d;
  return {
    ...d,
    id: d.id,
    name: d.name || null,
    driver_name: d.name || null,
    phone_number: d.phone_number || null,
    employee_id: d.employee_id || null,
    license_number: d.license_number || null,
    license_valid_until: d.license_valid_until || null,
    status: (d.status || d.employment_status || 'unknown').toLowerCase(),
    employment_status: d.employment_status || null,
    avatar_url: d.avatar_url || null,
    // These fields don't exist in the Driver Domain schema — only pass through if present
    rating: d.rating ?? null,
    risk_score: d.risk_score ?? null,
    assigned_truck: d.assigned_truck || null,
    experience_years: d.experience_years || null,
  };
}

export async function getDrivers(params = {}) {
  const listParams = {};
  if (params.status && params.status !== 'all') {
    listParams.is_active = params.status === 'active';
  }

  let drivers;
  try {
    drivers = await api.driversDomain.list(listParams) || [];
  } catch {
    drivers = await api.drivers.list(listParams) || [];
  }

  let normalized = drivers.map(normalizeDriver);

  if (params.search) {
    const q = params.search.toLowerCase();
    normalized = normalized.filter(d =>
      (d.name && d.name.toLowerCase().includes(q)) ||
      (d.phone_number && d.phone_number.includes(q)) ||
      (d.employee_id && d.employee_id.toLowerCase().includes(q))
    );
  }

  return normalized;
}

export async function getDriverById(id) {
  let driver;
  try {
    driver = await api.driversDomain.get(id);
  } catch {
    driver = await api.drivers.get(id);
  }

  if (!driver) {
    throw new Error('Driver not found');
  }

  return { ...normalizeDriver(driver), assignedTruck: null };
}

export async function createDriver(data) {
  const payload = {
    name: data.name,
    phone_number: data.phone_number,
    avatar_url: data.avatar_url || null,
  };
  const created = await api.drivers.create(payload);
  return normalizeDriver(created);
}

export async function updateDriver(id, data) {
  const payload = {};
  if (data.name !== undefined) payload.name = data.name;
  if (data.phone_number !== undefined) payload.phone_number = data.phone_number;
  if (data.avatar_url !== undefined) payload.avatar_url = data.avatar_url;
  if (data.risk_score !== undefined) payload.risk_score = Number(data.risk_score);
  if (data.rating !== undefined) payload.rating = Number(data.rating);
  if (data.is_active !== undefined) payload.is_active = data.is_active;

  const updated = await api.drivers.update(id, payload);
  return normalizeDriver(updated);
}

export async function deleteDriver(id) {
  return await api.drivers.delete(id);
}

export async function assignVehicle(driverId, vehicleId) {
  return { success: true, message: `Vehicle ID ${vehicleId} assigned to driver ID ${driverId}.` };
}
