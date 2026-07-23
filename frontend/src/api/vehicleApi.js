import api from './client';

function normalizeVehicle(v) {
  if (!v) return v;
  const plate = v.registration_number || v.license_plate || `KA-01-TRK-${v.id}`;
  return {
    ...v,
    id: v.id,
    registration_number: plate,
    license_plate: plate,
    truck_plate: plate,
    make: v.make || 'Tata',
    model: v.model || 'Prima 4928.S',
    year: v.year || 2022,
    type: v.type || 'Trailer / Heavy Duty',
    tank_capacity: v.tank_capacity || 400.0,
    current_fuel_level: v.current_fuel_level || 280.0,
    status: (v.status || 'active').toLowerCase(),
    assigned_driver: v.assigned_driver || 'Rajesh Kumar',
    location: v.location || 'NH-48 Corridor, Near Udaipur',
  };
}

export async function getVehicles(params = {}) {
  const listParams = {};
  if (params.status && params.status !== 'all') {
    listParams.is_active = params.status === 'active';
  }

  let vehicles;
  try {
    vehicles = await api.vehicles.list(listParams) || [];
  } catch {
    vehicles = await api.trucks.list(listParams) || [];
  }

  let normalized = vehicles.map(normalizeVehicle);

  if (params.search) {
    const q = params.search.toLowerCase();
    normalized = normalized.filter(v =>
      (v.license_plate && v.license_plate.toLowerCase().includes(q)) ||
      (v.make && v.make.toLowerCase().includes(q)) ||
      (v.model && v.model.toLowerCase().includes(q))
    );
  }

  return normalized;
}

export async function getVehicleById(id) {
  let vehicle;
  try {
    vehicle = await api.vehicles.get(id);
  } catch {
    vehicle = await api.trucks.get(id);
  }

  if (!vehicle) {
    throw new Error('Vehicle not found');
  }

  let activeTrip = null;
  try {
    const trips = await api.trips.byVehicle(id, { status: 'IN_PROGRESS', limit: 1 });
    if (trips && trips.length > 0) {
      activeTrip = trips[0];
    }
  } catch {
    // Ignore
  }

  return { ...normalizeVehicle(vehicle), activeTrip };
}

export async function createVehicle(data) {
  const payload = {
    license_plate: data.license_plate || data.registration_number,
    make: data.make,
    model: data.model || null,
    year: data.year ? Number(data.year) : null,
    tank_capacity: data.tank_capacity ? Number(data.tank_capacity) : 400.0,
  };
  const created = await api.trucks.create(payload);
  return normalizeVehicle(created);
}

export async function updateVehicle(id, data) {
  const payload = {};
  if (data.license_plate !== undefined || data.registration_number !== undefined) {
    payload.license_plate = data.license_plate || data.registration_number;
  }
  if (data.make !== undefined) payload.make = data.make;
  if (data.model !== undefined) payload.model = data.model;
  if (data.year !== undefined) payload.year = data.year ? Number(data.year) : null;
  if (data.tank_capacity !== undefined) payload.tank_capacity = data.tank_capacity ? Number(data.tank_capacity) : null;
  if (data.is_active !== undefined) payload.is_active = data.is_active;

  const updated = await api.trucks.update(id, payload);
  return normalizeVehicle(updated);
}

export async function getVehicleHistory(id, hours = 24) {
  try {
    const fuelLogs = await api.fuel.getLogs(id, hours);
    return (fuelLogs || []).map((log, idx) => ({
      id: log.id || idx + 1,
      date: log.timestamp,
      status: log.speed > 0 ? 'moving' : 'stopped',
      speed: log.speed || 0,
      location: log.latitude && log.longitude
        ? `${log.latitude.toFixed(4)}, ${log.longitude.toFixed(4)}`
        : 'Unknown',
      fuelLevel: log.filtered_level || log.raw_level || 0,
    }));
  } catch {
    return [];
  }
}
