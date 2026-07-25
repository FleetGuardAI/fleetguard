/**
 * FleetGuard AI Opportunity Service
 * Derives AI opportunities from real backend data (fuel alerts, expenses, maintenance anomalies).
 * Falls back to curated intelligence data when no backend anomalies are detected.
 */

import api from '@/api/client';
import { CATEGORY_META, SEVERITY_CONFIG } from '@/data/aiOpportunityData';

// Re-export config constants used by UI components
export { CATEGORY_META, SEVERITY_CONFIG };

/**
 * Build AI opportunities from real backend anomaly data.
 */
async function buildOpportunitiesFromBackend() {
  const opportunities = [];
  let idCounter = 1;

  try {
    // 1. Fuel theft alerts → fuel_waste opportunities
    const fuelAlerts = await api.fuel.getAlerts({ days: 30 }).catch(() => []);
    (fuelAlerts || []).forEach(alert => {
      opportunities.push({
        id: `AI-F${String(idCounter++).padStart(3, '0')}`,
        title: `Fuel drop of ${alert.fuel_drop_liters?.toFixed(1)}L detected on ${alert.truck_plate || 'unknown vehicle'}`,
        category: 'fuel_waste',
        severity: alert.fuel_drop_liters > 30 ? 'critical' : alert.fuel_drop_liters > 15 ? 'high' : 'medium',
        confidence: 90,
        potentialSaving: Math.round(alert.fuel_drop_liters * 95), // ~₹95/L
        evidence: [
          `Fuel level dropped by ${alert.fuel_drop_liters?.toFixed(1)}L while vehicle was ${alert.speed > 0 ? 'moving' : 'stationary'}.`,
          alert.latitude && alert.longitude ? `Location: ${alert.latitude.toFixed(4)}, ${alert.longitude.toFixed(4)}` : null,
        ].filter(Boolean),
        rootCause: alert.speed === 0 ? 'Stationary fuel drop — possible theft or siphoning.' : 'Fuel drop during transit — possible leak or sensor malfunction.',
        recommendation: 'Investigate fuel level sensor readings. Check for theft evidence at location.',
        expectedRoi: '1x (prevented loss)',
        truck: { plate: alert.truck_plate, model: null },
        driver: null,
        status: 'new',
        eta: 'Immediate',
        createdAt: alert.timestamp || new Date().toISOString(),
      });
    });

    // 2. Pending maintenance → high_maintenance opportunities
    const maintenance = await api.maintenance.list({ limit: 20 }).catch(() => []);
    const overdueMaint = (maintenance || []).filter(m => {
      if ((m.status || '').toLowerCase() !== 'scheduled') return false;
      if (!m.scheduled_date) return false;
      return new Date(m.scheduled_date) < new Date();
    });
    overdueMaint.forEach(m => {
      opportunities.push({
        id: `AI-M${String(idCounter++).padStart(3, '0')}`,
        title: `Overdue maintenance: ${m.business_id || `Record #${m.id}`}`,
        category: 'high_maintenance',
        severity: 'high',
        confidence: 95,
        potentialSaving: m.cost || 5000,
        evidence: [
          `Maintenance ${m.business_id} was scheduled for ${new Date(m.scheduled_date).toLocaleDateString()} and is overdue.`,
          m.workshop ? `Workshop: ${m.workshop}` : null,
        ].filter(Boolean),
        rootCause: 'Scheduled maintenance not completed on time.',
        recommendation: 'Complete the overdue maintenance to prevent breakdowns.',
        expectedRoi: '3x (prevented breakdown costs)',
        truck: m.vehicle_id ? { plate: `Vehicle ID: ${m.vehicle_id}`, model: null } : null,
        driver: null,
        status: 'new',
        eta: 'Immediate',
        createdAt: m.scheduled_date || new Date().toISOString(),
      });
    });

    // 3. High-value pending tickets → unexpected_expense opportunities
    const tickets = await api.tickets.list({ status: 'PENDING' }).catch(() => []);
    const highValueTickets = (tickets || []).filter(t => t.amount > 5000 && (t.risk_level === 'High' || t.risk_level === 'Critical'));
    highValueTickets.forEach(t => {
      opportunities.push({
        id: `AI-E${String(idCounter++).padStart(3, '0')}`,
        title: `High-risk expense: ₹${t.amount?.toLocaleString('en-IN')} — ${t.issue_type || 'Unknown'}`,
        category: t.is_duplicate ? 'duplicate_fuel' : 'unexpected_expense',
        severity: t.risk_level === 'Critical' ? 'critical' : 'high',
        confidence: 85,
        potentialSaving: Math.round(t.amount * 0.5),
        evidence: [
          `${t.driver_name || 'Unknown driver'} submitted ₹${t.amount?.toLocaleString('en-IN')} expense.`,
          t.risk_reasons || 'Flagged by AI risk engine.',
          t.vendor_name ? `Vendor: ${t.vendor_name}` : null,
        ].filter(Boolean),
        rootCause: t.risk_reasons || 'Amount significantly exceeds benchmark.',
        recommendation: 'Review expense details and verify with receipt evidence.',
        expectedRoi: '1x (prevented overpayment)',
        truck: t.truck_plate ? { plate: t.truck_plate, model: null } : null,
        driver: t.driver_name ? { name: t.driver_name, id: t.driver_id } : null,
        status: 'new',
        eta: '1 day',
        createdAt: t.created_at || new Date().toISOString(),
      });
    });
  } catch {
    // Silent failure — return whatever opportunities we've built
  }

  return opportunities;
}

/**
 * Fetch AI opportunities.
 * Tries to build from real backend data first.
 * 
 * @param {object} filters
 * @returns {Promise<{data: Array, total: number}>}
 */
export async function fetchAiOpportunities(filters = {}) {
  const opportunities = await buildOpportunitiesFromBackend();
  return { data: opportunities, total: opportunities.length };
}

export async function assignOpportunity(id) {
  return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
}

export async function dismissOpportunity(id) {
  return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
}

export async function scheduleOpportunity(id) {
  return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
}
