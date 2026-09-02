import api from './client';

/**
 * Fetch and aggregate dashboard KPI blocks and feeds from the backend.
 * 
 * @returns {Promise<object>}
 */
export async function getDashboardData() {
  // Do NOT catch errors here. Let them propagate to the UI.
  const [vehicles, events, expenses, recentActivity] = await Promise.all([
    api.vehicles.list(),
    api.events.list(),
    api.expenses.list(),
    api.expenses.list({ limit: 5 }), // Using expenses as recent activity for now
  ]);

  const activeTrucks = (vehicles || []).filter(v => v.status === 'ACTIVE').length;
  const pendingApprovals = (events || []).filter(e => e.status === 'PENDING').length;
  const theftAlerts = (events || []).filter(e => e.type === 'THEFT').length;
  const totalExpensesMonth = (expenses || []).reduce((sum, exp) => sum + (exp.amount || 0), 0);

  const mappedKPIs = {
    active_trucks: activeTrucks,
    pending_approvals: pendingApprovals,
    theft_alerts: theftAlerts,
    flagged_drivers: 0, // Requires driver intelligence API
    total_expenses_today: 0,
    total_expenses_month: totalExpensesMonth,
  };

  const mappedRecentActivity = (recentActivity || []).map(expense => ({
    id: expense.id,
    truck_id: expense.vehicle_id,
    driver_id: expense.driver_id,
    truck_plate: null, // would need to be enriched
    driver_name: null, // would need to be enriched
    category: expense.category ? expense.category.toLowerCase() : 'other',
    title: expense.description || expense.category || 'Expense Claim',
    amount: expense.amount,
    date: expense.created_at || null,
    status: expense.status || 'pending',
    ai_risk: null,
  }));

  // Fetch real fuel chart data from backend
  let fuelChart = [];
  try {
    if (vehicles && vehicles.length > 0) {
      const activeVehicle = vehicles.find(v => v.status === 'ACTIVE') || vehicles[0];
      const chartData = await api.fuel.getChartData(activeVehicle.id, 24);
      fuelChart = (chartData || []).map(point => ({
        time: point.timestamp,
        expected: point.expected_level,
        actual: point.actual_filtered_level,
        raw: point.raw_level,
      }));
    }
  } catch {
    // Graceful fallback for fuel chart since it's an optional visual layer
  }

  return {
    kpis: mappedKPIs,
    recentActivity: mappedRecentActivity,
    fuelChart,
  };
}

/**
 * Compute fleet health metrics from real backend data.
 * Replaces MOCK_FLEET_HEALTH.
 * 
 * @returns {Promise<object>}
 */
export async function getFleetHealth() {
  const [kpis, vehicles, maintenance] = await Promise.all([
    api.ownerDashboard.getKPIs().catch(() => null),
    api.vehicles.list().catch(() => []),
    api.maintenance.list({ limit: 50 }).catch(() => []),
  ]);

  const activeVehicles = (vehicles || []).filter(v => (v.status || '').toUpperCase() === 'ACTIVE');
  const totalVehicles = (vehicles || []).length;
  const vehicleHealthPct = totalVehicles > 0 ? Math.round((activeVehicles.length / totalVehicles) * 100) : 0;

  // Maintenance due count
  const pendingMaintenance = (maintenance || []).filter(m =>
    (m.status || '').toLowerCase() === 'scheduled' || (m.status || '').toLowerCase() === 'created'
  ).length;

  return {
    fuelEfficiency: { value: 0, unit: 'km/L', trend: 0, status: 'neutral' },
    vehicleHealth: { value: vehicleHealthPct, unit: '%', trend: 0, status: vehicleHealthPct > 80 ? 'good' : vehicleHealthPct > 50 ? 'warning' : 'critical' },
    driverScore: { value: 0, unit: '/5', trend: 0, status: 'neutral' },
    maintenance: { value: pendingMaintenance, unit: 'due', trend: 0, status: pendingMaintenance > 5 ? 'warning' : 'good' },
    monthlySavings: {
      value: kpis?.monthly_expenses || 0,
      unit: '₹',
      trend: 0,
      status: 'neutral',
    },
  };
}

/**
 * Compute upcoming alerts from real backend data.
 * Replaces MOCK_UPCOMING_ALERTS.
 * 
 * @returns {Promise<Array>}
 */
export async function getUpcomingAlerts() {
  const alerts = [];

  try {
    // Get fuel theft alerts
    const fuelAlerts = await api.fuel.getAlerts({ days: 7 }) || [];
    fuelAlerts.slice(0, 3).forEach((a, i) => {
      alerts.push({
        id: `fuel-${a.id || i}`,
        text: `${a.truck_plate || 'Vehicle'} — fuel drop of ${a.fuel_drop_liters?.toFixed(1)}L detected`,
        severity: a.fuel_drop_liters > 25 ? 'critical' : 'medium',
      });
    });
  } catch {
    // No fuel alerts
  }

  try {
    // Get pending maintenance
    const maintenance = await api.maintenance.list({ status: 'SCHEDULED', limit: 5 }) || [];
    maintenance.forEach(m => {
      const daysUntil = m.scheduled_date ? Math.ceil((new Date(m.scheduled_date) - Date.now()) / 86400000) : null;
      if (daysUntil !== null) {
        alerts.push({
          id: `mnt-${m.id}`,
          text: `${m.business_id || 'Maintenance'} — scheduled in ${daysUntil} days`,
          severity: daysUntil <= 3 ? 'critical' : daysUntil <= 7 ? 'medium' : 'low',
        });
      }
    });
  } catch {
    // No maintenance data
  }

  return alerts;
}

/**
 * Get recent operational actions from backend events.
 * Replaces MOCK_RECENT_AI_ACTIONS.
 * 
 * @returns {Promise<Array>}
 */
export async function getRecentActions() {
  try {
    const events = await api.events.list({ limit: 10 }) || [];
    return events.map(e => ({
      id: e.id,
      action: e.event_type ? e.event_type.replace(/_/g, ' ').replace(/\./g, ' — ') : 'System event',
      time: formatRelativeTime(e.timestamp || e.created_at),
    }));
  } catch {
    return [];
  }
}

/**
 * Compute trend data from real backend data.
 * Replaces MOCK_TRENDS.
 * 
 * @returns {Promise<object>}
 */
export async function getDashboardTrends() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  let fuelTrend = [];
  let revenueTrend = [];
  let utilizationTrend = [];
  let maintenanceTrend = [];

  try {
    // Get vehicles for utilization
    const vehicles = await api.vehicles.list().catch(() => []);
    const totalVehicles = vehicles.length || 1;

    // Get recent trips for utilization
    const trips = await api.trips.list({ limit: 100 }).catch(() => []);
    
    // Get recent maintenance for cost trend
    const maintenance = await api.maintenance.list({ limit: 50 }).catch(() => []);

    // Get recent tickets for revenue/expense trend
    const tickets = await api.tickets.list({ limit: 100 }).catch(() => []);

    // Build day-indexed data
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const dayName = days[d.getDay() === 0 ? 6 : d.getDay() - 1];
      const dateStr = d.toISOString().split('T')[0];

      // Trips active on this day for utilization
      const dayTrips = (trips || []).filter(t => {
        const start = t.actual_start_time || t.planned_start_time;
        const end = t.actual_end_time;
        return start && new Date(start).toISOString().split('T')[0] <= dateStr &&
               (!end || new Date(end).toISOString().split('T')[0] >= dateStr);
      });
      utilizationTrend.push({ day: dayName, value: totalVehicles > 0 ? Math.round((dayTrips.length / totalVehicles) * 100) : 0 });

      // Maintenance cost on this day
      const dayMaint = (maintenance || []).filter(m => {
        const mDate = m.completed_date || m.scheduled_date;
        return mDate && new Date(mDate).toISOString().split('T')[0] === dateStr;
      });
      maintenanceTrend.push({ day: dayName, value: dayMaint.reduce((sum, m) => sum + (m.cost || 0), 0) });

      // Ticket amounts on this day
      const dayTickets = (tickets || []).filter(t => {
        return t.created_at && new Date(t.created_at).toISOString().split('T')[0] === dateStr;
      });
      revenueTrend.push({ day: dayName, value: dayTickets.reduce((sum, t) => sum + (t.amount || 0), 0) });

      // Fuel efficiency — aggregate from fuel data if available
      fuelTrend.push({ day: dayName, value: null });
    }
  } catch {
    // Return empty trends on error
  }

  return {
    fuel: fuelTrend,
    revenue: revenueTrend,
    utilization: utilizationTrend,
    maintenance: maintenanceTrend,
  };
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return 'Unknown';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}
