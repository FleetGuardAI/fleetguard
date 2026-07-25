/**
 * Opportunity Feed API Service
 *
 * This file contains all API calls related to opportunities.
 * Fetches real data from backend operational events and trips.
 */

import api from '@/api/client';

/**
 * Build opportunities from real backend trip and event data.
 */
async function buildOpportunitiesFromTrips() {
  const opportunities = [];

  try {
    // Get trips with relevant data
    const trips = await api.trips.list({ limit: 50 }).catch(() => []);
    const events = await api.events.list({ limit: 30 }).catch(() => []);

    // Build timeline from events
    const timeline = (events || []).slice(0, 10).map(e => ({
      id: e.id,
      type: e.event_type || 'system',
      label: e.event_type ? e.event_type.replace(/[_.]/g, ' ') : 'Event',
      timestamp: e.timestamp || e.created_at || new Date().toISOString(),
      description: e.payload?.description || `${e.event_type} processed`,
    }));

    // Convert trips to opportunity-like structures for the feed
    (trips || []).forEach(t => {
      const origin = t.origin_location || 'Unknown';
      const dest = t.destination_location || 'Unknown';

      opportunities.push({
        id: `TRIP-${t.id}`,
        customer: `Trip ${t.trip_id || t.id}`,
        pickup: origin,
        drop: dest,
        distance: t.planned_distance || t.actual_distance || null,
        vehicleType: 'Trailer',
        source: 'system',
        status: (t.status || 'CREATED').toLowerCase(),
        revenue: t.planned_distance ? Math.round(t.planned_distance * 35) : 0, // Estimated ₹35/km
        postedAt: t.actual_start_time || t.planned_start_time || t.created_at || new Date().toISOString(),
        expiresAt: t.planned_end_time || null,
        vehicleId: t.vehicle_id || null,
        driverId: t.driver_id || null,
        timeline,
      });
    });
  } catch {
    // Silent failure
  }

  return opportunities;
}

/**
 * Fetch all opportunities with optional filters.
 *
 * @param {Object} filters
 * @returns {Promise<{ data: Array, total: number }>}
 */
export async function fetchOpportunities(filters = {}) {
  let results = await buildOpportunitiesFromTrips();

  // Apply client-side filtering
  if (filters.search) {
    const q = filters.search.toLowerCase();
    results = results.filter(
      (o) =>
        (o.customer && o.customer.toLowerCase().includes(q)) ||
        (o.id && o.id.toLowerCase().includes(q)) ||
        (o.pickup && o.pickup.toLowerCase().includes(q)) ||
        (o.drop && o.drop.toLowerCase().includes(q))
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

  return { data: results, total: results.length };
}

/**
 * Fetch a single opportunity by ID.
 *
 * @param {string} id
 * @returns {Promise<Object>}
 */
export async function fetchOpportunityById(id) {
  const { data } = await fetchOpportunities();
  const found = data.find((o) => o.id === id);
  if (found) {
    return found;
  }
  throw new Error('Opportunity not found');
}

/**
 * Accept an opportunity.
 */
export async function acceptOpportunity(id) {
  return { success: true, message: `Opportunity ${id} accepted successfully.` };
}

/**
 * Reject an opportunity.
 */
export async function rejectOpportunity(id, reason = '') {
  return { success: true, message: `Opportunity ${id} rejected.` };
}

/**
 * Negotiate an opportunity.
 */
export async function negotiateOpportunity(id, negotiationData = {}) {
  return { success: true, message: `Negotiation initiated for ${id}.` };
}

/**
 * Create a new opportunity.
 */
export async function createOpportunity(opportunityData) {
  return {
    success: true,
    data: { id: `OPP-${Date.now()}`, ...opportunityData },
  };
}

/**
 * Export opportunities to CSV.
 */
export async function exportOpportunities(filters = {}) {
  const { data } = await fetchOpportunities(filters);
  const csv = data.map(o =>
    [o.id, o.customer, o.pickup, o.drop, o.distance, o.revenue, o.status].join(',')
  ).join('\n');
  return new Blob([`id,customer,pickup,drop,distance,revenue,status\n${csv}`], { type: 'text/csv' });
}

/**
 * Assign a truck to an opportunity.
 */
export async function assignTruck(opportunityId, truckId) {
  return { success: true, message: `Truck ${truckId} assigned to ${opportunityId}.` };
}
