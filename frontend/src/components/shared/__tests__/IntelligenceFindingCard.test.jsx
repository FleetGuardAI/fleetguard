import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import IntelligenceFindingCard from '../IntelligenceFindingCard';

describe('IntelligenceFindingCard Component', () => {
  it('renders null when finding is not provided', () => {
    const { container } = render(
      <MemoryRouter>
        <IntelligenceFindingCard finding={null} />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders critical finding with severity badge, title, entity, and metrics', () => {
    const mockFinding = {
      finding_id: 'FIND-MAINT-001',
      category: 'MAINTENANCE',
      severity: 'CRITICAL',
      title: 'Overdue Maintenance: MH12AB1001',
      summary: 'Vehicle has exceeded its scheduled maintenance interval by 1,200 km.',
      entity_name: 'MH12AB1001 (Tata Prima)',
      measured_value: 'OVERDUE by 1,200 km',
      baseline_value: 'Interval: 10,000 km',
      observation_period: 'Active Schedule Evaluation',
      evidence_records: ['Maintenance Schedule #44'],
      recommended_action: 'Schedule workshop inspection immediately before next dispatch.'
    };

    render(
      <MemoryRouter>
        <IntelligenceFindingCard finding={mockFinding} />
      </MemoryRouter>
    );

    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('MAINTENANCE')).toBeInTheDocument();
    expect(screen.getByText('MH12AB1001 (Tata Prima)')).toBeInTheDocument();
    expect(screen.getByText('Overdue Maintenance: MH12AB1001')).toBeInTheDocument();
    expect(screen.getByText(/exceeded its scheduled maintenance interval/)).toBeInTheDocument();
    expect(screen.getByText('OVERDUE by 1,200 km')).toBeInTheDocument();
    expect(screen.getByText('Interval: 10,000 km')).toBeInTheDocument();
    expect(screen.getByText(/Schedule workshop inspection immediately/)).toBeInTheDocument();
    expect(screen.getByText(/Maintenance Schedule #44/)).toBeInTheDocument();
  });

  it('renders action handoff button and handles navigation or action click', () => {
    const onActionMock = vi.fn();
    const mockFindingWithHandoff = {
      finding_id: 'FIND-TRIP-002',
      category: 'TRIP_OPERATIONS',
      severity: 'HIGH',
      title: 'Dispatch Delay: TRP-101',
      summary: 'Trip is 3.5 hours overdue for departure.',
      entity_name: 'TRP-101',
      recommended_action: 'Assign available driver.',
      action_handoff: {
        screen: 'trips',
        route: '/trips',
        action_label: 'View in Fleetguard Trips'
      }
    };

    render(
      <MemoryRouter>
        <IntelligenceFindingCard finding={mockFindingWithHandoff} onAction={onActionMock} />
      </MemoryRouter>
    );

    const btn = screen.getByText('View in Fleetguard Trips');
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
  });
});
