import React, { useState } from 'react';
import {
  Calendar, Clock, Filter, RotateCcw, Check,
  ChevronDown, Globe, AlertTriangle
} from 'lucide-react';
import { cn } from '@/utils/cn';
import {
  FLEET_TIMEZONE_LABEL,
  formatFleetDateTime,
  calculatePresetRange,
  toUtcIsoString
} from '@/utils/dateTime';

const PRESETS = [
  { key: '1h', label: 'Last 1h' },
  { key: '6h', label: 'Last 6h' },
  { key: '12h', label: 'Last 12h' },
  { key: '24h', label: 'Last 24h' },
  { key: 'today', label: 'Today' },
  { key: 'yesterday', label: 'Yesterday' },
  { key: '7d', label: 'Last 7d' },
  { key: '30d', label: 'Last 30d' },
];

export function TimeFilterBar({
  activePreset = '30d',
  startTime,
  endTime,
  onApplyRange,
  onReset,
  selectedTrip = null,
  onClearTrip,
}) {
  const [isCustomOpen, setIsCustomOpen] = useState(false);

  // Form states for custom range
  const [customStartDate, setCustomStartDate] = useState('');
  const [customStartTime, setCustomStartTime] = useState('00:00');
  const [customEndDate, setCustomEndDate] = useState('');
  const [customEndTime, setCustomEndTime] = useState('23:59');
  const [validationError, setValidationError] = useState('');

  const handleSelectPreset = (presetKey) => {
    setIsCustomOpen(false);
    setValidationError('');
    const range = calculatePresetRange(presetKey);
    if (typeof onApplyRange === 'function') {
      onApplyRange({
        preset: presetKey,
        startTime: range.startTime,
        endTime: range.endTime,
      });
    }
  };

  const handleApplyCustom = (e) => {
    e.preventDefault();
    setValidationError('');

    if (!customStartDate || !customEndDate) {
      setValidationError('Please select both start and end dates.');
      return;
    }

    const startIso = toUtcIsoString(customStartDate, customStartTime);
    const endIso = toUtcIsoString(customEndDate, customEndTime);

    if (!startIso || !endIso) {
      setValidationError('Invalid date or time format.');
      return;
    }

    if (new Date(startIso) >= new Date(endIso)) {
      setValidationError('Start time must be before end time.');
      return;
    }

    if (typeof onApplyRange === 'function') {
      onApplyRange({
        preset: 'custom',
        startTime: startIso,
        endTime: endIso,
      });
    }
    setIsCustomOpen(false);
  };

  const handleResetFilters = () => {
    setValidationError('');
    setIsCustomOpen(false);
    if (typeof onReset === 'function') {
      onReset();
    }
  };

  return (
    <div className="bg-white border-b border-border p-3 space-y-2.5">
      {/* Top Bar: Presets & Timezone badge */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-bold text-content-secondary uppercase tracking-wider mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3 text-brand-600" />
            Time Filter:
          </span>

          {PRESETS.map((p) => {
            const isActive = activePreset === p.key && !selectedTrip;
            return (
              <button
                key={p.key}
                type="button"
                onClick={() => handleSelectPreset(p.key)}
                className={cn(
                  "px-2.5 py-1 rounded-md text-xs font-semibold transition-all shadow-xs border",
                  isActive
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-surface text-content-secondary border-border hover:bg-surface-secondary hover:text-content"
                )}
              >
                {p.label}
              </button>
            );
          })}

          <button
            type="button"
            onClick={() => setIsCustomOpen(!isCustomOpen)}
            className={cn(
              "px-2.5 py-1 rounded-md text-xs font-semibold transition-all border flex items-center gap-1 shadow-xs",
              activePreset === 'custom'
                ? "bg-brand-600 text-white border-brand-600"
                : "bg-surface text-content-secondary border-border hover:bg-surface-secondary"
            )}
          >
            <Calendar className="w-3 h-3" />
            Custom
            <ChevronDown className={cn("w-3 h-3 transition-transform", isCustomOpen && "rotate-180")} />
          </button>

          {(activePreset !== '30d' || selectedTrip) && (
            <button
              type="button"
              onClick={handleResetFilters}
              title="Reset to 30d default"
              className="p-1 rounded-md text-content-muted hover:text-content hover:bg-surface-secondary border border-transparent hover:border-border transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Timezone & active range badge */}
        <div className="flex items-center gap-2 text-[11px]">
          <span className="flex items-center gap-1 font-medium text-content-muted bg-surface-secondary px-2 py-0.5 rounded-full border border-border">
            <Globe className="w-3 h-3 text-content-muted" />
            {FLEET_TIMEZONE_LABEL}
          </span>
        </div>
      </div>

      {/* Selected Trip Active Alert Banner */}
      {selectedTrip && (
        <div className="flex items-center justify-between bg-brand-50 border border-brand-200 rounded-lg px-3 py-1.5 text-xs text-brand-900 animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="font-bold bg-brand-600 text-white text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider">
              Filtered to Trip
            </span>
            <span className="font-semibold">{selectedTrip.trip_id}</span>
            <span className="text-content-muted">•</span>
            <span className="text-content-secondary">
              {selectedTrip.origin_location?.split(',')[0]} → {selectedTrip.destination_location?.split(',')[0]}
            </span>
          </div>

          <button
            type="button"
            onClick={() => {
              if (typeof onClearTrip === 'function') onClearTrip();
            }}
            className="text-[11px] font-semibold text-brand-700 hover:text-brand-900 underline ml-3"
          >
            View Full Driver History
          </button>
        </div>
      )}

      {/* Custom Range Drawer */}
      {isCustomOpen && (
        <form onSubmit={handleApplyCustom} className="p-3 bg-surface-secondary/50 rounded-xl border border-border space-y-3 animate-fade-in-up">
          <div className="text-xs font-bold text-content flex items-center justify-between">
            <span>Select Custom Date & Time Range</span>
            <span className="text-[10px] font-normal text-content-muted">All times in {FLEET_TIMEZONE_LABEL}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {/* Start */}
            <div className="space-y-1">
              <label className="block text-[11px] font-semibold text-content-secondary">Start Window</label>
              <div className="flex gap-1.5">
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  className="w-2/3 px-2 py-1.5 bg-white border border-border rounded-md text-xs text-content focus:ring-1 focus:ring-brand-500"
                  required
                />
                <input
                  type="time"
                  value={customStartTime}
                  onChange={(e) => setCustomStartTime(e.target.value)}
                  className="w-1/3 px-2 py-1.5 bg-white border border-border rounded-md text-xs text-content focus:ring-1 focus:ring-brand-500"
                  required
                />
              </div>
            </div>

            {/* End */}
            <div className="space-y-1">
              <label className="block text-[11px] font-semibold text-content-secondary">End Window</label>
              <div className="flex gap-1.5">
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="w-2/3 px-2 py-1.5 bg-white border border-border rounded-md text-xs text-content focus:ring-1 focus:ring-brand-500"
                  required
                />
                <input
                  type="time"
                  value={customEndTime}
                  onChange={(e) => setCustomEndTime(e.target.value)}
                  className="w-1/3 px-2 py-1.5 bg-white border border-border rounded-md text-xs text-content focus:ring-1 focus:ring-brand-500"
                  required
                />
              </div>
            </div>
          </div>

          {validationError && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 bg-red-50 p-2 rounded-md border border-red-200">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-1 border-t border-border/60">
            <button
              type="button"
              onClick={() => setIsCustomOpen(false)}
              className="px-3 py-1 text-xs font-semibold text-content-secondary hover:text-content hover:bg-surface-secondary rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3.5 py-1 text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 rounded-md shadow-xs transition-colors flex items-center gap-1"
            >
              <Check className="w-3.5 h-3.5" />
              Apply Range
            </button>
          </div>
        </form>
      )}

      {/* Active Time Span Indicator */}
      <div className="flex items-center justify-between text-[11px] text-content-muted bg-surface px-2.5 py-1 rounded-md border border-border/60">
        <div className="flex items-center gap-1.5 truncate">
          <Clock className="w-3 h-3 text-brand-600 shrink-0" />
          <span className="font-semibold text-content">Active Range:</span>
          <span className="truncate">
            {startTime ? formatFleetDateTime(startTime) : 'Beginning of records'}
            {' → '}
            {endTime ? formatFleetDateTime(endTime) : 'Latest available'}
          </span>
        </div>
      </div>
    </div>
  );
}
