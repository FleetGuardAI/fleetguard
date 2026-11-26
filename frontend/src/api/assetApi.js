import api from './client';

/**
 * Normalizes backend AssetResponse object for UI display.
 */
function normalizeAsset(a) {
  if (!a) return a;
  return {
    ...a,
    id: a.id,
    business_id: a.business_id || `AST-${a.id}`,
    asset_type: a.asset_type || 'GPS_TRACKER',
    manufacturer: a.manufacturer || null,
    model: a.model || null,
    serial_number: a.serial_number || null,
    firmware_version: a.firmware_version || null,
    current_vehicle_id: a.current_vehicle_id || null,
    installation_status: (a.installation_status || 'uninstalled').toLowerCase(),
    operational_status: (a.operational_status || 'active').toLowerCase(),
    purchase_information: a.purchase_information || {},
    warranty_information: a.warranty_information || {},
    history_records: a.history_records || [],
  };
}

export async function getAssets(params = {}) {
  const listParams = {};
  if (params.installation_status && params.installation_status !== 'all') {
    listParams.installation_status = params.installation_status.toUpperCase();
  }
  if (params.operational_status && params.operational_status !== 'all') {
    listParams.operational_status = params.operational_status.toUpperCase();
  }

  const records = await api.assets.list(listParams) || [];
  let normalized = records.map(normalizeAsset);

  if (params.search) {
    const q = params.search.toLowerCase();
    normalized = normalized.filter(a =>
      (a.business_id && a.business_id.toLowerCase().includes(q)) ||
      (a.serial_number && a.serial_number.toLowerCase().includes(q)) ||
      (a.asset_type && a.asset_type.toLowerCase().includes(q)) ||
      (a.manufacturer && a.manufacturer.toLowerCase().includes(q)) ||
      (a.model && a.model.toLowerCase().includes(q))
    );
  }

  return normalized;
}

export async function getAssetById(id) {
  const record = await api.assets.get(id);
  return normalizeAsset(record);
}

export async function getAssetsByVehicle(vehicleId) {
  const records = await api.assets.byVehicle(vehicleId) || [];
  return records.map(normalizeAsset);
}

export async function createHardwareAsset(data) {
  const record = await api.assets.createHardware(data);
  return normalizeAsset(record);
}

// ── Universal Hardware & Telematics Endpoints ─────────────────────────

export async function getHardwareSummaryStats() {
  return await api.hardware.getStats();
}

export async function getHardwareProtocols() {
  return await api.hardware.getProtocols();
}

export async function getHardwareDevices(params = {}) {
  return await api.hardware.getDevices(params);
}

export async function getHardwareDeviceById(id) {
  return await api.hardware.getDevice(id);
}

export async function registerHardwareDevice(data) {
  return await api.hardware.registerDevice(data);
}

export async function updateHardwareDevice(id, data) {
  return await api.hardware.updateDevice(id, data);
}

export async function reassignDeviceVehicle(id, data) {
  return await api.hardware.reassignVehicle(id, data);
}

export async function disconnectHardwareDevice(id) {
  return await api.hardware.disconnectDevice(id);
}

export async function removeHardwareDevice(id) {
  return await api.hardware.removeDevice(id);
}

export async function testHardwareConnection(id) {
  return await api.hardware.testConnection(id);
}

export async function getDeviceLocationHistory(id, params = {}) {
  return await api.hardware.getLocations(id, params);
}

export async function getGPSProviders() {
  return await api.hardware.getProviders();
}

export async function createGPSProvider(data) {
  return await api.hardware.createProvider(data);
}

export async function testGPSProvider(id) {
  return await api.hardware.testProvider(id);
}

export async function syncGPSProvider(id) {
  return await api.hardware.syncProvider(id);
}

export async function deleteGPSProvider(id) {
  return await api.hardware.deleteProvider(id);
}
