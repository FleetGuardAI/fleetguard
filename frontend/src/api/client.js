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
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    if (response.status === 204) return null;
    return await response.json();
  } catch (err) {
    console.warn(`[FleetGuard API] ${endpoint} failed:`, err.message);
    return null;
  }
}

/** @type {{ dashboard: object, tickets: object, drivers: object, trucks: object, fuel: object }} */
const api = {
  dashboard: {
    /** @returns {Promise<import('../data/mockData').DashboardKPIs | null>} */
    getKPIs: () => request('/dashboard/kpis'),
    getRecentActivity: (limit = 20) => request(`/dashboard/recent-activity?limit=${limit}`),
  },

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

  drivers: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/drivers${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/drivers/${id}`),
    create: (data) => request('/drivers', { method: 'POST', body: JSON.stringify(data) }),
  },

  trucks: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/trucks${query ? `?${query}` : ''}`);
    },
    get: (id) => request(`/trucks/${id}`),
    create: (data) => request('/trucks', { method: 'POST', body: JSON.stringify(data) }),
  },

  fuel: {
    getLogs: (truckId, hours = 24) => request(`/fuel/logs/${truckId}?hours=${hours}`),
    getChartData: (truckId, hours = 24) => request(`/fuel/chart/${truckId}?hours=${hours}`),
    getAlerts: (params = {}) => {
      const query = new URLSearchParams(params).toString();
      return request(`/fuel/alerts${query ? `?${query}` : ''}`);
    },
  },
};

export default api;
