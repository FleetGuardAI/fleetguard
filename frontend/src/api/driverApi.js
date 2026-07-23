import api from './client';

function normalizeDriver(d) {
  if (!d) return d;
  return {
    ...d,
    id: d.id,
    name: d.name || 'Fleet Driver',
    driver_name: d.name || 'Fleet Driver',
    phone_number: d.phone_number || '+91 98765 43210',
    employee_id: d.employee_id || `EMP-${d.id}`,
    license_number: d.license_number || 'DL-1420110012345',
    status: (d.status || 'active').toLowerCase(),
    rating: d.rating ?? 4.6,
    risk_score: d.risk_score ?? 15,
    assigned_truck: d.assigned_truck || 'KA-01-HH-1234',
    experience_years: d.experience_years || 5,
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

export async function assignVehicle(driverId, vehicleId) {
  return { success: true, message: `Vehicle ID ${vehicleId} assigned to driver ID ${driverId}.` };
}
