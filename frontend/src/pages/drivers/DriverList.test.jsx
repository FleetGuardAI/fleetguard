import { renderWithMemoryRouter, screen, waitFor } from '../../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import DriverList from './DriverList';
import * as driverApi from '../../api/driverApi';

// Mock the API module
vi.mock('../../api/driverApi', () => ({
  getDrivers: vi.fn(),
  updateDriverStatus: vi.fn(),
}));

describe('DriverList Component', () => {
  it('renders a list of drivers fetched from the API', async () => {
    // Mock the API response
    driverApi.getDrivers.mockResolvedValue([
      { id: '1', name: 'John Doe', status: 'ACTIVE', phone: '1234567890' },
      { id: '2', name: 'Jane Smith', status: 'INACTIVE', phone: '0987654321' },
    ]);

    renderWithMemoryRouter(<DriverList />, { initialEntries: ['/drivers'] });

    // Wait for the mock drivers to be rendered
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('calls getDrivers on mount', () => {
    driverApi.getDrivers.mockReturnValue(new Promise(() => {})); // Never resolves
    renderWithMemoryRouter(<DriverList />, { initialEntries: ['/drivers'] });
    expect(driverApi.getDrivers).toHaveBeenCalled();
  });
});
