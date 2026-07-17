import { mockKPIs, mockTickets, mockDrivers, generateMockFuelData } from '@/data/mockData';

export async function getDashboardData() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        kpis: mockKPIs,
        recentActivity: mockTickets.slice(0, 5),
        flaggedDrivers: mockDrivers.filter(d => d.risk_score > 40),
        fuelChart: generateMockFuelData(),
      });
    }, 600);
  });
}
