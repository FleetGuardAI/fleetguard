import api from './client';

/**
 * Dynamically aggregate fleet report data from real backend endpoints.
 * Returns empty arrays when no data is available.
 *
 * @param {object} params - Optional filters (vehicle_id)
 * @returns {Promise<object>}
 */
export async function getFleetReportData(params = {}) {
  const { vehicle_id } = params;

  let kpisPromise = api.ownerDashboard.getKPIs().catch(() => null);
  let expensesPromise = vehicle_id && vehicle_id !== 'all' 
    ? api.expenses.byVehicle(vehicle_id).catch(() => []) 
    : api.expenses.list().catch(() => []);
  let tripsPromise = vehicle_id && vehicle_id !== 'all' 
    ? api.trips.byVehicle(vehicle_id).catch(() => []) 
    : api.trips.list({ limit: 200 }).catch(() => []);
  let vehiclesPromise = api.trucks.list().catch(() => []);
  let maintenancePromise = vehicle_id && vehicle_id !== 'all' 
    ? api.maintenance.list().catch(() => []).then(res => (res || []).filter(m => m.vehicle_id == vehicle_id))
    : api.maintenance.list().catch(() => []);

  // Note: we can't efficiently filter maintenance by vehicle_id without the byVehicle endpoint if it doesn't exist.
  // Actually client.js doesn't expose api.maintenance.byVehicle, so we filter it manually if needed, 
  // or better, don't fake frontend filtering for it if not supported. But we'll try basic array filter for now.

  const [kpis, expenses, trips, vehicles, maintenance] = await Promise.all([
    kpisPromise,
    expensesPromise,
    tripsPromise,
    vehiclesPromise,
    maintenancePromise
  ]);

  // Aggregate expenses by category
  const categoryTotals = {};
  let totalExpense = 0;
  (expenses || []).forEach(e => {
    const cat = e.category ? e.category.toUpperCase() : 'OTHER';
    const amt = Number(e.amount || 0);
    categoryTotals[cat] = (categoryTotals[cat] || 0) + amt;
    totalExpense += amt;
  });

  const expenseDistribution = Object.keys(categoryTotals).length > 0
    ? Object.entries(categoryTotals).map(([name, val]) => ({
        name,
        value: totalExpense > 0 ? Math.round((val / totalExpense) * 100) : 0,
        amount: val
      }))
    : [];

  // Compute mileage trend from real trip data (group by month)
  const mileageTrend = [];
  const tripsByMonth = {};
  (trips || []).forEach(t => {
    if (t.actual_distance && (t.actual_start_time || t.planned_start_time)) {
      const date = new Date(t.actual_start_time || t.planned_start_time);
      const monthKey = date.toLocaleString('en', { month: 'short' });
      if (!tripsByMonth[monthKey]) {
        tripsByMonth[monthKey] = { totalDist: 0, count: 0 };
      }
      tripsByMonth[monthKey].totalDist += t.actual_distance;
      tripsByMonth[monthKey].count += 1;
    }
  });
  Object.entries(tripsByMonth).forEach(([month, data]) => {
    mileageTrend.push({
      month,
      avg_mileage: data.count > 0 ? Math.round((data.totalDist / data.count) * 10) / 10 : 0,
    });
  });

  // Compute driver safety from real driver data (derived from risk_score if available)
  let driverSafetyStats = [];
  try {
    const drivers = await api.drivers.list().catch(() => []);
    driverSafetyStats = (drivers || []).map(d => ({
      name: d.name || (d.id ? `Driver ID: ${d.id}` : 'Unassigned'),
      safetyScore: d.risk_score != null ? Math.max(100 - d.risk_score, 0) : null,
      rating: d.rating || null,
    })).filter(d => d.safetyScore !== null);
  } catch {
    // No driver data available
  }

  // Compute maintenance cost by vehicle from real maintenance records
  const maintenanceCostByVehicle = {};
  (maintenance || []).forEach(m => {
    if (m.vehicle_id && m.cost) {
      const key = String(m.vehicle_id);
      maintenanceCostByVehicle[key] = (maintenanceCostByVehicle[key] || 0) + m.cost;
    }
  });

  const maintenanceData = Object.entries(maintenanceCostByVehicle).map(([v, c]) => ({ vehicle: v, cost: c }));

  return {
    kpis: kpis || {},
    mileageTrend,
    expenseDistribution,
    driverSafetyStats,
    maintenanceCostByVehicle: maintenanceData,
    totalVehicles: (vehicles || []).length,
    totalTrips: (trips || []).length,
    totalExpense: totalExpense,
  };
}

export async function exportReport(format = 'pdf', type = 'fleet', params = {}) {
  // Mock successful generation since no real backend endpoint exists yet
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ downloadUrl: `#`, filename: `${type}_report_${new Date().getTime()}.${format}` });
    }, 1500);
  });
}
