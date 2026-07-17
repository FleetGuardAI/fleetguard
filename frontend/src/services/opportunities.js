/**
 * Opportunity Feed API Service
 *
 * This file contains all API calls related to opportunities.
 * Each function currently returns mock data — replace with real API calls
 * when the backend is ready.
 */

import {
  MOCK_OPPORTUNITIES,
  MOCK_TIMELINE_EVENTS,
} from '@/data/opportunityMockData';

/**
 * Fetch all opportunities with optional filters.
 *
 * TODO: GET /api/opportunities
 * TODO: Query params — search, vehicleType, source, status, dateFrom, dateTo,
 *       priceMin, priceMax, distanceMin, distanceMax, page, limit
 *
 * @param {Object} filters
 * @returns {Promise<{ data: Array, total: number }>}
 */
export async function fetchOpportunities(filters = {}) {
  // TODO: Replace with actual API call
  // const response = await apiClient.get('/api/opportunities', { params: filters });
  // return response.data;

  return new Promise((resolve) => {
    setTimeout(() => {
      let results = [...MOCK_OPPORTUNITIES];

      // Apply client-side filtering for mock
      if (filters.search) {
        const q = filters.search.toLowerCase();
        results = results.filter(
          (o) =>
            o.customer.toLowerCase().includes(q) ||
            o.id.toLowerCase().includes(q) ||
            o.pickup.toLowerCase().includes(q) ||
            o.drop.toLowerCase().includes(q)
        );
      }

      if (filters.vehicleType) {
        results = results.filter((o) => o.vehicleType === filters.vehicleType);
      }

      if (filters.source) {
        results = results.filter((o) => o.source === filters.source);
      }

      if (filters.status) {
        results = results.filter((o) => o.status === filters.status);
      }

      if (filters.priceMin) {
        results = results.filter((o) => o.revenue >= Number(filters.priceMin));
      }

      if (filters.priceMax) {
        results = results.filter((o) => o.revenue <= Number(filters.priceMax));
      }

      resolve({ data: results, total: results.length });
    }, 800); // Simulate network delay
  });
}

/**
 * Fetch a single opportunity by ID.
 *
 * TODO: GET /api/opportunities/:id
 *
 * @param {string} id
 * @returns {Promise<Object>}
 */
export async function fetchOpportunityById(id) {
  // TODO: Replace with actual API call
  // const response = await apiClient.get(`/api/opportunities/${id}`);
  // return response.data;

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const found = MOCK_OPPORTUNITIES.find((o) => o.id === id);
      if (found) {
        resolve({ ...found, timeline: MOCK_TIMELINE_EVENTS });
      } else {
        reject(new Error('Opportunity not found'));
      }
    }, 400);
  });
}

/**
 * Accept an opportunity.
 *
 * TODO: POST /api/opportunities/accept
 *
 * @param {string} id
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export async function acceptOpportunity(id) {
  // TODO: Replace with actual API call
  // const response = await apiClient.post('/api/opportunities/accept', { id });
  // return response.data;

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, message: `Opportunity ${id} accepted successfully.` });
    }, 500);
  });
}

/**
 * Reject an opportunity.
 *
 * TODO: POST /api/opportunities/reject
 *
 * @param {string} id
 * @param {string} reason
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export async function rejectOpportunity(id, reason = '') {
  // TODO: Replace with actual API call
  // const response = await apiClient.post('/api/opportunities/reject', { id, reason });
  // return response.data;

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, message: `Opportunity ${id} rejected.` });
    }, 500);
  });
}

/**
 * Negotiate an opportunity.
 *
 * TODO: POST /api/opportunities/negotiate
 *
 * @param {string} id
 * @param {Object} negotiationData
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export async function negotiateOpportunity(id, negotiationData = {}) {
  // TODO: Replace with actual API call
  // const response = await apiClient.post('/api/opportunities/negotiate', { id, ...negotiationData });
  // return response.data;

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, message: `Negotiation initiated for ${id}.` });
    }, 500);
  });
}

/**
 * Create a new opportunity.
 *
 * TODO: POST /api/opportunities/create
 *
 * @param {Object} opportunityData
 * @returns {Promise<{ success: boolean, data: Object }>}
 */
export async function createOpportunity(opportunityData) {
  // TODO: Replace with actual API call
  // const response = await apiClient.post('/api/opportunities/create', opportunityData);
  // return response.data;

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        data: { id: `OPP-${Date.now()}`, ...opportunityData },
      });
    }, 600);
  });
}

/**
 * Export opportunities to CSV/Excel.
 *
 * TODO: GET /api/opportunities/export
 *
 * @param {Object} filters
 * @returns {Promise<Blob>}
 */
export async function exportOpportunities(filters = {}) {
  // TODO: Replace with actual API call
  // const response = await apiClient.get('/api/opportunities/export', { params: filters, responseType: 'blob' });
  // return response.data;

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(new Blob(['mock csv data'], { type: 'text/csv' }));
    }, 500);
  });
}

/**
 * Assign a truck to an opportunity.
 *
 * TODO: POST /api/opportunities/:id/assign-truck
 *
 * @param {string} opportunityId
 * @param {string} truckId
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export async function assignTruck(opportunityId, truckId) {
  // TODO: Replace with actual API call
  // const response = await apiClient.post(`/api/opportunities/${opportunityId}/assign-truck`, { truckId });
  // return response.data;

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, message: `Truck ${truckId} assigned to ${opportunityId}.` });
    }, 500);
  });
}
