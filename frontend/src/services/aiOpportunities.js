/**
 * Fleet Intelligence API Service
 *
 * All AI opportunity endpoints. Each returns mock data for now.
 * Backend integration points are clearly marked with TODO.
 */

import { MOCK_AI_OPPORTUNITIES } from '@/data/aiOpportunityData';

/**
 * Fetch all AI-generated opportunities.
 *
 * TODO: GET /api/v1/opportunities
 * TODO: Query params — category, severity, status, page, limit
 *
 * @returns {Promise<{ data: Array, total: number }>}
 */
export async function fetchAiOpportunities() {
  // TODO: const response = await apiClient.get('/api/v1/opportunities');
  // TODO: return response.data;
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ data: [...MOCK_AI_OPPORTUNITIES], total: MOCK_AI_OPPORTUNITIES.length });
    }, 600);
  });
}

/**
 * Assign an opportunity to a team member or truck.
 *
 * TODO: POST /api/v1/opportunities/{id}/assign
 *
 * @param {string} id
 * @param {Object} assignData
 * @returns {Promise<{ success: boolean }>}
 */
export async function assignOpportunity(id, assignData = {}) {
  // TODO: const response = await apiClient.post(`/api/v1/opportunities/${id}/assign`, assignData);
  // TODO: return response.data;
  return new Promise((resolve) => {
    setTimeout(() => resolve({ success: true, message: `Opportunity ${id} assigned.` }), 400);
  });
}

/**
 * Dismiss an opportunity.
 *
 * TODO: POST /api/v1/opportunities/{id}/dismiss
 *
 * @param {string} id
 * @param {string} reason
 * @returns {Promise<{ success: boolean }>}
 */
export async function dismissOpportunity(id, reason = '') {
  // TODO: const response = await apiClient.post(`/api/v1/opportunities/${id}/dismiss`, { reason });
  // TODO: return response.data;
  return new Promise((resolve) => {
    setTimeout(() => resolve({ success: true, message: `Opportunity ${id} dismissed.` }), 400);
  });
}

/**
 * Schedule an opportunity for future action.
 *
 * TODO: POST /api/v1/opportunities/{id}/schedule
 *
 * @param {string} id
 * @param {Object} scheduleData
 * @returns {Promise<{ success: boolean }>}
 */
export async function scheduleOpportunity(id, scheduleData = {}) {
  // TODO: const response = await apiClient.post(`/api/v1/opportunities/${id}/schedule`, scheduleData);
  // TODO: return response.data;
  return new Promise((resolve) => {
    setTimeout(() => resolve({ success: true, message: `Opportunity ${id} scheduled.` }), 400);
  });
}
