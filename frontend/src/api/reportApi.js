import api from './client';

/**
 * Dynamically aggregate fleet report data from real backend endpoints.
 * No hardcoded fallback data — returns empty arrays when no data is available.
 *
 * @returns {Promise<object>}
 */
export async function getFleetReportData() {
  const [kpis, tickets, trips, vehicles, maintenance] = await Promise.all([
    api.dashboard.getKPIs().catch(() => null),
    api.tickets.list().catch(() => []),
    api.trips.list({ limit: 200 }).catch(() => []),
    api.vehicles.list().catch(() => []),
    api.maintenance.list().catch(() => []),
  ]);

  // Aggregate expenses by issue type / category from tickets
  const categoryTotals = {};
  let totalExpense = 0;
  (tickets || []).forEach(t => {
    const cat = t.issue_type ? t.issue_type.toUpperCase() : 'OTHER';
    const amt = Number(t.amount || 0);
    categoryTotals[cat] = (categoryTotals[cat] || 0) + amt;
    totalExpense += amt;
  });

  const expenseDistribution = Object.keys(categoryTotals).length > 0
    ? Object.entries(categoryTotals).map(([name, val]) => ({
        name,
        value: totalExpense > 0 ? Math.round((val / totalExpense) * 100) : 0,
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
    const drivers = await api.driversDomain.list().catch(() => api.drivers.list().catch(() => []));
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
      const key = m.vehicle_id;
      maintenanceCostByVehicle[key] = (maintenanceCostByVehicle[key] || 0) + m.cost;
    }
  });

  return {
    kpis: kpis || {},
    mileageTrend,
    expenseDistribution,
    driverSafetyStats,
    maintenanceCostByVehicle,
    totalVehicles: (vehicles || []).length,
    totalTrips: (trips || []).length,
    totalExpense,
  };
}

export async function exportReport(format = 'pdf', type = 'fleet') {
  return { downloadUrl: `#`, filename: `${type}_report.${format}` };
}
