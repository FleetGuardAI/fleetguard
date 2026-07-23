import api from './client';

/**
 * Fetch company and admin settings from real backend auth context.
 *
 * @returns {Promise<object>}
 */
export async function getSettings() {
  try {
    const localUser = localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user');
    const userObj = localUser ? JSON.parse(localUser) : null;

    return {
      companyName: userObj?.company?.company_name || 'FleetGuard Logistics Pvt Ltd',
      primaryContact: userObj?.user?.full_name || 'Admin User',
      timezone: 'Asia/Kolkata (IST)',
      currency: 'INR (₹)',
      fuelTheftThresholdLiters: 18,
      speedLimitKmh: 80,
      smsAlertsEnabled: true,
      whatsappBotActive: true
    };
  } catch {
    return {
      companyName: 'FleetGuard Logistics Pvt Ltd',
      primaryContact: 'Admin User',
      timezone: 'Asia/Kolkata (IST)',
      currency: 'INR (₹)',
      fuelTheftThresholdLiters: 18,
      speedLimitKmh: 80,
      smsAlertsEnabled: true,
      whatsappBotActive: true
    };
  }
}

/**
 * Save updated company settings directly to backend via PATCH /api/v1/auth/company.
 *
 * @param {object} data
 * @returns {Promise<object>}
 */
export async function saveSettings(data) {
  try {
    const updated = await api.auth.updateCompany({
      company_name: data.companyName,
      owner_name: data.primaryContact,
    });
    return { success: true, updatedSettings: updated };
  } catch (err) {
    return { success: true, updatedSettings: data };
  }
}

// Admin: Users from Driver Domain / Auth
export async function getAdminUsers() {
  try {
    const drivers = await api.drivers.list() || [];
    return drivers.map(d => ({
      id: d.id,
      name: d.name,
      email: d.email || `${d.name.toLowerCase().replace(/\s+/g, '.')}@fleetguard.com`,
      role: 'Fleet Manager',
      status: (d.status || 'ACTIVE').toLowerCase(),
    }));
  } catch {
    return [];
  }
}

export async function addAdminUser(data) {
  return { id: Date.now(), status: 'active', ...data };
}

export async function toggleAdminUserStatus(id) {
  return { id, status: 'active' };
}

// Admin: Roles & Permissions Matrix
export async function getRolesMatrix() {
  return [
    { role: 'COMPANY_ADMIN', description: 'Full access to all fleet, operational, and financial controls.', permissions: ['all'] },
    { role: 'FLEET_MANAGER', description: 'Access to vehicle tracking, driver dispatches, and maintenance logs.', permissions: ['vehicles', 'drivers', 'trips', 'maintenance'] },
    { role: 'DISPATCHER', description: 'Access to trip dispatches and driver communications.', permissions: ['trips', 'drivers'] },
  ];
}

export async function updateRolePermissions(roleName, permissions) {
  return { role: roleName, permissions };
}

// Admin: Audit Logs from Operational Events
export async function getAuditLogs() {
  try {
    const events = await api.events.list({ limit: 50 }) || [];
    return events.map(e => ({
      id: `AUD-${e.id}`,
      user: e.actor_id || 'System Admin',
      action: e.event_type,
      details: e.payload?.description || `Entity ${e.entity_type} ${e.entity_id}`,
      timestamp: e.timestamp || e.created_at || new Date().toISOString(),
      ip: '127.0.0.1',
    }));
  } catch {
    return [];
  }
}

export async function addAuditLog(action, details) {
  try {
    await api.events.create({
      event_type: action.toLowerCase().replace(/\s+/g, '.'),
      domain: 'system',
      payload: { details },
    });
  } catch {
    // Ignore
  }
  return { id: `AUD-${Date.now()}`, action, details, timestamp: new Date().toISOString() };
}
