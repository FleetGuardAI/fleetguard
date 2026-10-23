import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DriverSidebar } from '../DriverSidebar';

const mockDrivers = [
  {
    id: 1,
    name: 'Aarav Sharma',
    phone_number: '+919876543210',
    employee_id: 'EMP-001',
    vehicle_registration: 'KA-01-AB-1234',
    duty_status: 'ON_DUTY',
    total_trips: 12,
    gps_point_count: 540,
    last_location_at: '2026-10-23T10:00:00Z',
  },
  {
    id: 2,
    name: 'Bhavin Patel',
    phone_number: '+919876543211',
    employee_id: 'EMP-002',
    vehicle_registration: 'MH-02-CD-5678',
    duty_status: 'OFF_DUTY',
    total_trips: 0,
    gps_point_count: 0,
    last_location_at: '2026-10-22T10:00:00Z',
  },
];

describe('DriverSidebar Component & onChange Crash Prevention', () => {
  it('renders safely without optional callbacks and typing does NOT throw TypeError', () => {
    // When callbacks like onSearchChange, onDutyStatusChange are omitted (as happened in FleetMap),
    // typing or clicking MUST NOT throw "k is not a function"
    render(
      <DriverSidebar
        drivers={mockDrivers}
        selectedDriver={mockDrivers[0]}
      />
    );

    const searchInput = screen.getByPlaceholderText(/search driver/i);
    expect(searchInput).toBeDefined();

    // Fire onChange without onSearchChange callback provided
    expect(() => {
      fireEvent.change(searchInput, { target: { value: 'Aarav' } });
    }).not.toThrow();

    // Fire dutyStatus onChange without onDutyStatusChange callback provided
    const statusSelect = screen.getByDisplayValue('All Statuses');
    expect(() => {
      fireEvent.change(statusSelect, { target: { value: 'ON_DUTY' } });
    }).not.toThrow();

    // Fire sortBy onChange without onSortByChange callback provided
    const sortSelect = screen.getByDisplayValue('Latest Activity');
    expect(() => {
      fireEvent.change(sortSelect, { target: { value: 'name' } });
    }).not.toThrow();

    // Fire hasTrips toggle without callback
    const hasTripsBtn = screen.getByText('Has Trips');
    expect(() => {
      fireEvent.click(hasTripsBtn);
    }).not.toThrow();
  });

  it('correctly filters and sorts drivers with provided callbacks', () => {
    const onSearchChange = vi.fn();
    const onSelectDriver = vi.fn();

    render(
      <DriverSidebar
        drivers={mockDrivers}
        selectedDriver={mockDrivers[0]}
        onSelectDriver={onSelectDriver}
        onSearchChange={onSearchChange}
      />
    );

    const searchInput = screen.getByPlaceholderText(/search driver/i);
    fireEvent.change(searchInput, { target: { value: 'Bhavin' } });
    expect(onSearchChange).toHaveBeenCalledWith('Bhavin');

    const driverCard = screen.getByText('Bhavin Patel');
    fireEvent.click(driverCard);
    expect(onSelectDriver).toHaveBeenCalledWith(mockDrivers[1]);
  });

  it('renders actionable error state with retry button when error occurs', () => {
    const onRetry = vi.fn();

    render(
      <DriverSidebar
        drivers={[]}
        error="404 Not Found: Could not connect to API"
        onRetry={onRetry}
      />
    );

    expect(screen.getByText(/Failed to load drivers/i)).toBeDefined();
    expect(screen.getByText(/404 Not Found/i)).toBeDefined();

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
