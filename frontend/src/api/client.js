/**
 * FleetGuard API Client
 * Fetch wrapper for communicating with the FastAPI backend.
 * @module api/client
 */

const API_BASE = '/api';

/**
 * @param {string} endpoint - API path (e.g. '/dashboard/kpis')
 * @param {RequestInit} [options] - Fetch options
 * @returns {Promise<any>}
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const localToken = localStorage.getItem('fleetguard_token');
  const sessionToken = sessionStorage.getItem('fleetguard_token');
  const token = localToken || sessionToken;

  const tokenType = localToken
    ? localStorage.getItem('fleetguard_token_type') || 'bearer'
    : sessionStorage.getItem('fleetguard_token_type') || 'bearer';
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `${tokenType} ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    if (response.status === 401) {
      localStorage.removeItem('fleetguard_token');
      localStorage.removeItem('fleetguard_token_type');
      localStorage.removeItem('fleetguard_user');

      sessionStorage.removeItem('fleetguard_token');
      sessionStorage.removeItem('fleetguard_token_type');
      sessionStorage.removeItem('fleetguard_user');
      if (!window.location.pathname.startsWith('/login') && window.location.pathname !== '/') {
        window.location.href = '/login?expired=true';
      }
      throw new Error('Your session has expired. Please log in again.');
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    if (response.status === 204) return null;
    return await response.json();
  } catch (err) {
    console.warn(`[FleetGuard API] ${endpoint} failed:`, err.message);
    throw err;
  }
}

const api = {
  // ── Dashboard (existing) ───────────────────────────────────
  dashboard: {
    getKPIs: () => request('/dashboard/kpis'),
    getRecentActivity: (limit = 20) => request(`/dashboard/recent-activity?limit=${limit}`),
  },

  // ── Tickets (existing) ────────────────────────────────────
  tickets: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/tickets${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/tickets/${id}`),
    create: (data) => request('/tickets', { method: 'POST', body: JSON.stringify(data) }),
    action: (id, payload) =>
      request(`/tickets/${id}/action`, { method: 'POST', body: JSON.stringify(payload) }),
  },

  // ── Legacy Drivers (existing /api/drivers) ─────────────────
  drivers: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/drivers${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/drivers/${id}`),
    create: (data) => request('/drivers', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => request(`/drivers/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  },

  // ── Legacy Trucks (existing /api/trucks) ───────────────────
  trucks: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/trucks${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/trucks/${id}`),
    create: (data) => request('/trucks', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => request(`/trucks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  },

  // ── Fuel Monitoring (existing) ─────────────────────────────
  fuel: {
    getLogs: (truckId, hours = 24) => request(`/fuel/logs/${truckId}?hours=${hours}`),
    getChartData: (truckId, hours = 24) => request(`/fuel/chart/${truckId}?hours=${hours}`),
    getAlerts: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/fuel/alerts${query ? `?${query}` : ''}`);
    },
    ingest: (data) => request('/fuel/ingest', { method: 'POST', body: JSON.stringify(data) }),
  },

  // ── Trip Domain (NEW - /api/v1/trips) ──────────────────────
  trips: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/trips${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/trips/${id}`),
    search: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/trips/search${query ? `?${query}` : ''}`);
    },
    byVehicle: (vehicleId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/vehicles/${vehicleId}/trips${query ? `?${query}` : ''}`);
    },
    byDriver: (driverId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/drivers/${driverId}/trips${query ? `?${query}` : ''}`);
    },
  },

  // ── Maintenance Domain (NEW - /api/v1/maintenance) ─────────
  maintenance: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/maintenance${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/maintenance/${id}`),
    search: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/maintenance/search${query ? `?${query}` : ''}`);
    },
    byVehicle: (vehicleId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/vehicles/${vehicleId}/maintenance${query ? `?${query}` : ''}`);
    },
  },

  // ── Expense Domain (NEW - /api/v1/expenses) ────────────────
  expenses: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/expenses${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/expenses/${id}`),
    search: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/expenses/search${query ? `?${query}` : ''}`);
    },
    byVehicle: (vehicleId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/vehicles/${vehicleId}/expenses${query ? `?${query}` : ''}`);
    },
    byDriver: (driverId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/drivers/${driverId}/expenses${query ? `?${query}` : ''}`);
    },
    byTrip: (tripId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/trips/${tripId}/expenses${query ? `?${query}` : ''}`);
    },
  },

  // ── Vehicle Domain (NEW - /api/v1/vehicles) ────────────────
  vehicles: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/vehicles${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/vehicles/${id}`),
  },

  // ── Driver Domain (NEW - /api/v1/drivers) ──────────────────
  driversDomain: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/drivers${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/drivers/${id}`),
  },

  // ── Asset Domain (NEW - /api/v1/assets) ────────────────────
  assets: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/assets${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/assets/${id}`),
    byVehicle: (vehicleId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/vehicles/${vehicleId}/assets${query ? `?${query}` : ''}`);
    },
  },

  // ── Tyre Domain (NEW - /api/v1/tyres) ──────────────────────
  tyres: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/tyres${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/tyres/${id}`),
    byVehicle: (vehicleId, params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/vehicles/${vehicleId}/tyres${query ? `?${query}` : ''}`);
    },
  },

  // ── Documents (NEW - /api/v1/documents) ────────────────────
  documents: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/documents${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/documents/${id}`),
    upload: (formData) => {
      // Special case: don't set Content-Type, let browser set multipart boundary
      const localToken = localStorage.getItem('fleetguard_token');
      const sessionToken = sessionStorage.getItem('fleetguard_token');
      const token = localToken || sessionToken;
      const tokenType = localToken
        ? localStorage.getItem('fleetguard_token_type') || 'bearer'
        : sessionStorage.getItem('fleetguard_token_type') || 'bearer';
      
      const headers = {};
      if (token) {
        headers['Authorization'] = `${tokenType} ${token}`;
      }
      return fetch(`${API_BASE}/v1/documents`, {
        method: 'POST',
        headers,
        body: formData,
      }).then(r => r.json());
    },
  },

  // ── Operational Events (NEW - /api/v1/events) ──────────────
  events: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/v1/events${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/v1/events/${id}`),
    create: (data) => request('/v1/events', { method: 'POST', body: JSON.stringify(data) }),
  },
};

export default api;
