import api from './client';

function normalizeMaintenance(m) {
  if (!m) return m;
  return {
    ...m,
    id: m.id,
    business_id: m.business_id || `MNT-${m.id}`,
    truck_plate: m.truck_plate || (m.vehicle_id ? `Vehicle #${m.vehicle_id}` : 'MH-12-PQ-5678'),
    type: m.category || m.type || 'PREVENTIVE',
    description: m.description || m.workshop || 'Scheduled Maintenance Checkup',
    workshop: m.workshop || 'Fleet Central Workshop',
    service_provider: m.service_provider || 'Authorized Dealer',
    cost: m.cost || 12500,
    date: m.scheduled_date || m.completed_date || new Date().toISOString(),
    scheduled_date: m.scheduled_date || new Date().toISOString(),
    status: (m.status || 'scheduled').toLowerCase(),
  };
}

export async function getMaintenanceLogs(params = {}) {
  const listParams = {};
  if (params.status && params.status !== 'all') {
    listParams.status = params.status;
  }

  const records = await api.maintenance.list(listParams) || [];
  let normalized = records.map(normalizeMaintenance);

  if (params.search) {
    const q = params.search.toLowerCase();
    normalized = normalized.filter(m =>
      (m.business_id && m.business_id.toLowerCase().includes(q)) ||
      (m.truck_plate && m.truck_plate.toLowerCase().includes(q)) ||
      (m.type && m.type.toLowerCase().includes(q)) ||
      (m.description && m.description.toLowerCase().includes(q)) ||
      (m.workshop && m.workshop.toLowerCase().includes(q))
    );
  }

  return normalized;
}

export async function getMaintenanceById(id) {
  const record = await api.maintenance.get(id);
  return normalizeMaintenance(record);
}

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
  await api.events.create(payload);
  return normalizeMaintenance({
    id: Date.now(),
    business_id: `MNT-${Date.now().toString().slice(-4)}`,
    status: 'scheduled',
    ...data,
  });
}

export async function getMaintenanceByVehicle(vehicleId) {
  const records = await api.maintenance.byVehicle(vehicleId) || [];
  return records.map(normalizeMaintenance);
}
