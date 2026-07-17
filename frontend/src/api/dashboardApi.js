import api from './client';
import { generateMockFuelData } from '@/data/mockData';

/**
 * Fetch and aggregate dashboard KPI blocks and feeds from the backend.
 * Fallback to mock fuel chart telematics data.
 * 
 * @returns {Promise<object>}
 */
export async function getDashboardData() {
  const [kpis, recentActivity, drivers] = await Promise.all([
    api.dashboard.getKPIs(),
    api.dashboard.getRecentActivity(5),
    api.drivers.list()
  ]);

  const defaultKPIs = {
    active_trucks: 0,
    pending_approvals: 0,
    theft_alerts: 0,
    flagged_drivers: 0,
    total_expenses_today: 0,
    total_expenses_month: 0,
  };

  const mappedKPIs = kpis ? {
    active_trucks: kpis.active_trucks,
    pending_approvals: kpis.pending_approvals,
    theft_alerts: kpis.theft_alerts,
    flagged_drivers: kpis.flagged_drivers,
    total_expenses_today: kpis.total_expenses_today,
    total_expenses_month: kpis.total_expenses_month,
  } : defaultKPIs;

  const mappedRecentActivity = (recentActivity || []).map(ticket => ({
    id: ticket.id,
    truck_id: ticket.truck_id,
    driver_id: ticket.driver_id,
    truck_plate: ticket.truck_plate || `Truck #${ticket.truck_id}`,
    driver_name: ticket.driver_name || `Driver #${ticket.driver_id}`,
    category: ticket.issue_type ? ticket.issue_type.toLowerCase() : 'other',
    title: ticket.description || ticket.issue_type || 'Expense Claim',
    amount: ticket.amount,
    date: ticket.created_at || new Date().toISOString(),
    status: ticket.status || 'pending',
    ai_risk: ticket.risk_level || 'Low',
  }));

  const flaggedDrivers = (drivers || []).filter(d => d.risk_score > 40);

  return {
    kpis: mappedKPIs,
    recentActivity: mappedRecentActivity,
    flaggedDrivers,
    fuelChart: generateMockFuelData(),
  };
}
