import { renderWithMemoryRouter, screen, waitFor } from '../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import Dashboard from './Dashboard';
import * as dashboardApi from '../api/dashboardApi';
import * as authApi from '../api/authApi';

// Mock the API module
vi.mock('@/api/dashboardApi', () => ({
  getFleetHealth: vi.fn(),
  getDashboardData: vi.fn(),
  getUpcomingAlerts: vi.fn(),
}));

vi.mock('@/api/telematicsApi', () => ({
  getLiveTracking: vi.fn(),
}));

vi.mock('@/api/authApi', () => ({
  getCurrentUser: vi.fn().mockResolvedValue({ id: '1', name: 'Admin User', role: 'owner' }),
}));

describe('Dashboard Component', () => {
  it('renders dashboard layout and loading state initially', async () => {
    // Return promises that don't resolve to keep it in loading state
    dashboardApi.getFleetHealth.mockReturnValue(new Promise(() => {}));
    dashboardApi.getDashboardData.mockReturnValue(new Promise(() => {}));
    dashboardApi.getUpcomingAlerts.mockReturnValue(new Promise(() => {}));
    
    // getLiveTracking needs to be imported or mocked implicitly, but wait, 
    // it's not imported here. The component will call the mocked version.
    
    renderWithMemoryRouter(<Dashboard />, { initialEntries: ['/'] });
    
    // The page title or section should be visible after lazy loading
    await waitFor(() => {
      expect(screen.getByText('Financial Overview')).toBeInTheDocument();
    });
  });

  it('calls API methods on mount', async () => {
    dashboardApi.getFleetHealth.mockResolvedValue({
      status: 'healthy', active_vehicles: 50, maintenance_due: 2, total_distance: 10000,
    });
    dashboardApi.getDashboardData.mockResolvedValue({
      kpis: { active_trucks: 50, pending_approvals: 2, theft_alerts: 0, total_expenses_month: 5000 },
      recentActivity: [],
      fuelChart: []
    });
    dashboardApi.getUpcomingAlerts.mockResolvedValue([]);
    
    renderWithMemoryRouter(<Dashboard />, { initialEntries: ['/'] });
    
    await waitFor(() => {
      expect(dashboardApi.getFleetHealth).toHaveBeenCalled();
      expect(dashboardApi.getDashboardData).toHaveBeenCalled();
    });
  });
});
