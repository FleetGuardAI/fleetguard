import { useState } from 'react';
import {
  Search,
  SlidersHorizontal,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';
import {
  VEHICLE_TYPES,
  SOURCE_OPTIONS,
  STATUS_OPTIONS,
} from '@/data/opportunityConfig';

/**
 * Comprehensive filter bar for the opportunity feed.
 * Contains search, dropdowns, range sliders, and a collapsible advanced section.
 */
export function OpportunityFilters({ filters, onChange, onReset }) {
  const [expanded, setExpanded] = useState(false);

  const update = (key, value) => {
    onChange({ ...filters, [key]: value });
  };

  const activeFilterCount = Object.values(filters).filter(
    (v) => v !== '' && v !== undefined && v !== null
  ).length;

  return (
    <div className="bg-surface border border-border rounded-2xl overflow-hidden transition-all duration-300 animate-fade-in">
      {/* Primary row */}
      <div className="p-4 flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-content-muted" />
          <input
            id="opp-search"
            type="text"
            placeholder="Search by customer, load number, or location…"
            value={filters.search || ''}
            onChange={(e) => update('search', e.target.value)}
            className={cn(
              'w-full h-10 pl-10 pr-4 rounded-xl border border-border bg-surface-secondary text-sm text-content',
              'placeholder:text-content-muted transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500'
            )}
          />
          {filters.search && (
            <button
              onClick={() => update('search', '')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-content-muted hover:text-content"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Vehicle Type */}
        <FilterSelect
          id="opp-vehicle-type"
          placeholder="Vehicle Type"
          value={filters.vehicleType || ''}
          onChange={(v) => update('vehicleType', v)}
          options={VEHICLE_TYPES.map((t) => ({ value: t, label: t }))}
        />

        {/* Source */}
        <FilterSelect
          id="opp-source"
          placeholder="Source"
          value={filters.source || ''}
          onChange={(v) => update('source', v)}
          options={SOURCE_OPTIONS}
        />

        {/* Status */}
        <FilterSelect
          id="opp-status"
          placeholder="Status"
          value={filters.status || ''}
          onChange={(v) => update('status', v)}
          options={STATUS_OPTIONS}
        />

        {/* Toggle advanced */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          icon={
            expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <SlidersHorizontal className="h-4 w-4" />
            )
          }
          className="text-content-secondary"
        >
          {expanded ? 'Less' : 'More'}
        </Button>

        {/* Reset */}
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            icon={<RotateCcw className="h-3.5 w-3.5" />}
            className="text-content-muted hover:text-red-500"
          >
            Reset
            <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 rounded-full">
              {activeFilterCount}
            </span>
          </Button>
        )}
      </div>

      {/* Expanded row */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 flex flex-wrap items-end gap-4 border-t border-border mt-0 pt-4 animate-fade-in">
          {/* Date Range */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-content-muted uppercase tracking-wider">
              Date Range
            </label>
            <div className="flex items-center gap-2">
              <input
                id="opp-date-from"
                type="date"
                value={filters.dateFrom || ''}
                onChange={(e) => update('dateFrom', e.target.value)}
                className="h-9 px-3 rounded-lg border border-border bg-surface-secondary text-sm text-content focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
              <span className="text-xs text-content-muted">to</span>
              <input
                id="opp-date-to"
                type="date"
                value={filters.dateTo || ''}
                onChange={(e) => update('dateTo', e.target.value)}
                className="h-9 px-3 rounded-lg border border-border bg-surface-secondary text-sm text-content focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
            </div>
          </div>

          {/* Price Range */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-content-muted uppercase tracking-wider">
              Price Range (₹)
            </label>
            <div className="flex items-center gap-2">
              <input
                id="opp-price-min"
                type="number"
                placeholder="Min"
                value={filters.priceMin || ''}
                onChange={(e) => update('priceMin', e.target.value)}
                className="h-9 w-28 px-3 rounded-lg border border-border bg-surface-secondary text-sm text-content focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
              <span className="text-xs text-content-muted">–</span>
              <input
                id="opp-price-max"
                type="number"
                placeholder="Max"
                value={filters.priceMax || ''}
                onChange={(e) => update('priceMax', e.target.value)}
                className="h-9 w-28 px-3 rounded-lg border border-border bg-surface-secondary text-sm text-content focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
            </div>
          </div>

          {/* Distance Range */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-content-muted uppercase tracking-wider">
              Distance (km)
            </label>
            <div className="flex items-center gap-2">
              <input
                id="opp-dist-min"
                type="number"
                placeholder="Min"
                value={filters.distanceMin || ''}
                onChange={(e) => update('distanceMin', e.target.value)}
                className="h-9 w-28 px-3 rounded-lg border border-border bg-surface-secondary text-sm text-content focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
              <span className="text-xs text-content-muted">–</span>
              <input
                id="opp-dist-max"
                type="number"
                placeholder="Max"
                value={filters.distanceMax || ''}
                onChange={(e) => update('distanceMax', e.target.value)}
                className="h-9 w-28 px-3 rounded-lg border border-border bg-surface-secondary text-sm text-content focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Minimal styled filter select dropdown.
 */
function FilterSelect({ id, placeholder, value, onChange, options }) {
  return (
    <div className="relative">
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          'h-10 pl-3 pr-8 rounded-xl border border-border bg-surface-secondary text-sm appearance-none cursor-pointer',
          'transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500',
          value ? 'text-content font-medium' : 'text-content-muted'
        )}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-content-muted pointer-events-none" />
    </div>
  );
}
