import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

import HardwareSummaryCards from '../HardwareSummaryCards';
import HardwareAssetsDashboard from '../HardwareAssetsDashboard';
import AddDeviceWizardModal from '../AddDeviceWizardModal';
import ReassignVehicleModal from '../ReassignVehicleModal';

// Mock the APIs
vi.mock('@/api/assetApi', () => ({
  getHardwareSummaryStats: vi.fn().mockResolvedValue({
    total_devices: 42,
    connected_devices: 30,
    disconnected_devices: 8,
    pending_devices: 4,
    vehicles_with_gps: 35,
    vehicles_without_gps: 15,
  }),
  getHardwareProtocols: vi.fn().mockResolvedValue([
    { id: 'GT06', name: 'GT06 Protocol', defaultPort: 5023 },
    { id: 'TELTONIKA_CODEC8', name: 'Teltonika Codec 8', defaultPort: 5027 },
  ]),
  getHardwareDevices: vi.fn().mockResolvedValue({
    items: [
      {
        id: 1,
        company_id: 1,
        business_id: 'HW-001',
        device_name: 'Tata Prima Primary GPS',
        imei: '865432019876543',
        manufacturer: 'Teltonika',
        model: 'FMB920',
        protocol: 'TELTONIKA_CODEC8',
        gps_provider: 'Direct TCP',
        connection_status: 'CONNECTED',
        is_stale: false,
        vehicle_registration: 'DL01AA1111',
        last_communication_at: '2026-11-22T10:00:00Z',
        last_known_lat: 28.6139,
        last_known_lng: 77.2090,
        last_known_speed: 45.0,
        last_known_ignition: true,
      },
    ],
    total: 1,
    page: 1,
    page_size: 10,
  }),
  testHardwareConnection: vi.fn().mockResolvedValue({
    connected: true,
    latency_ms: 120,
    message: 'Online',
  }),
  disconnectHardwareDevice: vi.fn().mockResolvedValue({ id: 1, connection_status: 'DISCONNECTED' }),
  removeHardwareDevice: vi.fn().mockResolvedValue({ success: true }),
  registerHardwareDevice: vi.fn().mockResolvedValue({ id: 99, device_name: 'New Tracker' }),
  getGPSProviders: vi.fn().mockResolvedValue([]),
}));

vi.mock('@/api/vehicleApi', () => ({
  getVehicles: vi.fn().mockResolvedValue([
    { id: 1, registration_number: 'DL01AA1111', make: 'Tata', model: 'Prima', has_active_gps: true },
    { id: 2, registration_number: 'MH02BB2222', make: 'Ashok Leyland', model: 'Captain', has_active_gps: false },
  ]),
}));

vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  }),
}));

describe('Hardware Assets Module Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('HardwareSummaryCards', () => {
    it('renders 6 telematics metric cards with correct values', () => {
      const summary = {
        total_devices: 42,
        connected_devices: 30,
        disconnected_devices: 8,
        pending_devices: 4,
        vehicles_with_gps: 35,
        vehicles_without_gps: 15,
      };

      render(<HardwareSummaryCards summary={summary} loading={false} />);

      expect(screen.getByText('Total Devices')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('Pending Config')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('Vehicles With GPS')).toBeInTheDocument();
      expect(screen.getByText('35')).toBeInTheDocument();
      expect(screen.getByText('Vehicles W/O GPS')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
    });
  });

  describe('HardwareAssetsDashboard', () => {
    it('renders dashboard with summary cards, search box, and device row', async () => {
      render(
        <BrowserRouter>
          <HardwareAssetsDashboard />
        </BrowserRouter>
      );

      // Verify Header
      expect(screen.getByText('Hardware Assets & Telematics')).toBeInTheDocument();
      expect(screen.getByText('Add Device')).toBeInTheDocument();
      expect(screen.getByText('Manage Providers')).toBeInTheDocument();

      // Wait for table to load
      await waitFor(() => {
        expect(screen.getByText('Tata Prima Primary GPS')).toBeInTheDocument();
        expect(screen.getByText('865432019876543')).toBeInTheDocument();
        expect(screen.getByText('DL01AA1111')).toBeInTheDocument();
      });
    });
  });

  describe('AddDeviceWizardModal', () => {
    it('renders multi-step wizard and advances through steps', async () => {
      render(
        <AddDeviceWizardModal
          open={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
          vehicles={[
            { id: 1, registration_number: 'DL01AA1111' },
            { id: 2, registration_number: 'MH02BB2222' },
          ]}
        />
      );

      expect(screen.getByText('Step 1: Select Integration Architecture')).toBeInTheDocument();
      expect(screen.getByText('Direct GPS Hardware')).toBeInTheDocument();
      expect(screen.getByText('GPS Provider API')).toBeInTheDocument();

      // Click Continue to Step 2
      const continueBtn = screen.getByText('Continue');
      fireEvent.click(continueBtn);

      await waitFor(() => {
        expect(screen.getByText('Step 2: Hardware Manufacturer & Protocol')).toBeInTheDocument();
      });
    });
  });

  describe('ReassignVehicleModal', () => {
    it('renders reassignment options with conflict warning on active vehicles', () => {
      const mockDev = {
        id: 1,
        device_name: 'Tracker 1',
        vehicle_registration: 'DL01AA1111',
        current_vehicle_id: 1,
      };

      const vehicles = [
        { id: 1, registration_number: 'DL01AA1111', has_active_gps: true },
        { id: 2, registration_number: 'MH02BB2222', has_active_gps: true, current_device_id: 99 },
      ];

      render(
        <ReassignVehicleModal
          open={true}
          onClose={vi.fn()}
          device={mockDev}
          vehicles={vehicles}
          onSuccess={vi.fn()}
        />
      );

      expect(screen.getByText('Mount to Vehicle')).toBeInTheDocument();
      expect(screen.getByText('Unassign to Storage')).toBeInTheDocument();

      // Select vehicle with conflict
      const v2 = screen.getByText('MH02BB2222');
      fireEvent.click(v2);

      expect(screen.getByText(/already has an active GPS tracker/)).toBeInTheDocument();
      expect(screen.getByText(/Force swap/)).toBeInTheDocument();
    });
  });
});
