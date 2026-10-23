import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { TimeFilterBar } from '../TimeFilterBar';

describe('TimeFilterBar Component', () => {
  it('renders presets including 1h, 6h, 12h, 24h, today, yesterday, 7d, 30d, custom', () => {
    const handleApplyRange = vi.fn();

    render(
      <TimeFilterBar
        activePreset="7d"
        onApplyRange={handleApplyRange}
      />
    );

    expect(screen.getByText('Last 1h')).toBeInTheDocument();
    expect(screen.getByText('Last 6h')).toBeInTheDocument();
    expect(screen.getByText('Last 12h')).toBeInTheDocument();
    expect(screen.getByText('Last 24h')).toBeInTheDocument();
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Yesterday')).toBeInTheDocument();
    expect(screen.getByText('Last 7d')).toBeInTheDocument();
    expect(screen.getByText('Last 30d')).toBeInTheDocument();
    expect(screen.getByText('Custom')).toBeInTheDocument();
    expect(screen.getByText('IST (UTC+05:30)')).toBeInTheDocument();
  });

  it('triggers onApplyRange when a preset pill is clicked', () => {
    const handleApplyRange = vi.fn();

    render(
      <TimeFilterBar
        activePreset="7d"
        onApplyRange={handleApplyRange}
      />
    );

    const pill24h = screen.getByText('Last 24h');
    fireEvent.click(pill24h);

    expect(handleApplyRange).toHaveBeenCalledWith(
      expect.objectContaining({
        preset: '24h',
      })
    );
  });

  it('displays selected trip and triggers onClearTrip', () => {
    const handleClearTrip = vi.fn();

    render(
      <TimeFilterBar
        activePreset="7d"
        onApplyRange={vi.fn()}
        selectedTrip={{ id: 42, trip_id: 'TRP-D4857279' }}
        onClearTrip={handleClearTrip}
      />
    );

    expect(screen.getByText(/TRP-D4857279/)).toBeInTheDocument();
    const clearBtn = screen.getByText('View Full Driver History');
    fireEvent.click(clearBtn);
    expect(handleClearTrip).toHaveBeenCalled();
  });
});
