import React, { useState } from 'react';
import {
  Search, Users, Truck, Navigation, Clock,
  CheckCircle, ArrowUpDown, Shield, AlertCircle, RefreshCw
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatRelativeTime } from '@/utils/dateTime';

export function DriverSidebar({
  drivers = [],
  selectedDriver = null,
  onSelectDriver,
  loading = false,
  isLoading = false,
  error = null,
  onRetry = null,
  searchTerm: controlledSearchTerm,
  onSearchChange,
  dutyStatusFilter: controlledDutyStatus,
  onDutyStatusChange,
  hasTripsFilter: controlledHasTrips,
  onHasTripsFilterToggle,
  sortBy: controlledSortBy,
  onSortByChange,
}) {
  const isActualLoading = Boolean(loading || isLoading);

  // Local fallback states if parent does not control them
  const [internalSearch, setInternalSearch] = useState('');
  const [internalDuty, setInternalDuty] = useState('all');
  const [internalSort, setInternalSort] = useState('latest_activity');
  const [internalHasTrips, setInternalHasTrips] = useState(false);

  const searchTerm = controlledSearchTerm !== undefined ? controlledSearchTerm : internalSearch;
  const dutyStatusFilter = controlledDutyStatus !== undefined ? controlledDutyStatus : internalDuty;
  const sortBy = controlledSortBy !== undefined ? controlledSortBy : internalSort;
  const hasTripsFilter = controlledHasTrips !== undefined ? controlledHasTrips : internalHasTrips;

  const handleSearchChange = (val) => {
    setInternalSearch(val);
    if (typeof onSearchChange === 'function') {
      try {
        onSearchChange(val);
      } catch (err) {
        console.error('Error in onSearchChange callback:', err);
      }
    }
  };

  const handleDutyStatusChange = (val) => {
    setInternalDuty(val);
    if (typeof onDutyStatusChange === 'function') {
      try {
        onDutyStatusChange(val);
      } catch (err) {
        console.error('Error in onDutyStatusChange callback:', err);
      }
    }
  };

  const handleSortByChange = (val) => {
    setInternalSort(val);
    if (typeof onSortByChange === 'function') {
      try {
        onSortByChange(val);
      } catch (err) {
        console.error('Error in onSortByChange callback:', err);
      }
    }
  };

  const handleHasTripsToggle = (val) => {
    setInternalHasTrips(val);
    if (typeof onHasTripsFilterToggle === 'function') {
      try {
        onHasTripsFilterToggle(val);
      } catch (err) {
        console.error('Error in onHasTripsFilterToggle callback:', err);
      }
    }
  };

  // Filter drivers locally
  const filteredDrivers = (drivers || []).filter(d => {
    if (!d) return false;
    if (dutyStatusFilter !== 'all' && d.duty_status !== dutyStatusFilter) return false;
    if (hasTripsFilter && (d.total_trips || 0) === 0) return false;
    if (searchTerm) {
      const q = String(searchTerm).toLowerCase().trim();
      const matchName = d.name?.toLowerCase().includes(q);
      const matchPhone = d.phone_number?.includes(q);
      const matchVeh = d.vehicle_registration?.toLowerCase().includes(q);
      const matchEmp = d.employee_id?.toLowerCase().includes(q);
      if (!matchName && !matchPhone && !matchVeh && !matchEmp) return false;
    }
    return true;
  });

  // Sort drivers
  const sortedDrivers = [...filteredDrivers].sort((a, b) => {
    if (sortBy === 'name') {
      return (a.name || '').localeCompare(b.name || '');
    }
    if (sortBy === 'trips_count') {
      return (b.total_trips || 0) - (a.total_trips || 0);
    }
    if (sortBy === 'gps_points') {
      return (b.gps_point_count || 0) - (a.gps_point_count || 0);
    }
    // latest_activity default: most recent timestamp first
    const timeA = new Date(a.last_location_at || a.updated_at || a.created_at || 0).getTime();
    const timeB = new Date(b.last_location_at || b.updated_at || b.created_at || 0).getTime();
    return timeB - timeA;
  });

  return (
    <div className="flex flex-col h-full bg-white border-r border-border select-none">
      {/* Sidebar Header & Search */}
      <div className="p-3.5 border-b border-border space-y-2.5 bg-surface-secondary/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-brand-600" />
            <h2 className="text-sm font-semibold text-content tracking-tight">Fleet Drivers</h2>
          </div>
          <span className="text-[11px] font-medium text-content-muted bg-white px-2 py-0.5 rounded-full border border-border shadow-xs">
            {error ? '0 of 0' : `${sortedDrivers.length} of ${(drivers || []).length}`}
          </span>
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-content-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search driver, vehicle plate, phone..."
            value={searchTerm || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-border rounded-lg placeholder:text-content-muted focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 transition-all shadow-xs"
          />
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
          <select
            value={dutyStatusFilter || 'all'}
            onChange={(e) => handleDutyStatusChange(e.target.value)}
            className="text-[11px] py-1 px-2 bg-white border border-border rounded-md text-content font-medium focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="all">All Statuses</option>
            <option value="ON_DUTY">On Duty</option>
            <option value="OFF_DUTY">Off Duty</option>
            <option value="ON_BREAK">On Break</option>
          </select>

          <select
            value={sortBy || 'latest_activity'}
            onChange={(e) => handleSortByChange(e.target.value)}
            className="text-[11px] py-1 px-2 bg-white border border-border rounded-md text-content font-medium focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="latest_activity">Latest Activity</option>
            <option value="name">Name (A-Z)</option>
            <option value="trips_count">Most Trips</option>
            <option value="gps_points">GPS Points Count</option>
          </select>

          <button
            type="button"
            onClick={() => handleHasTripsToggle(!hasTripsFilter)}
            className={cn(
              "text-[10px] font-semibold px-2 py-1 rounded-md border transition-all",
              hasTripsFilter
                ? "bg-brand-50 text-brand-700 border-brand-300"
                : "bg-white text-content-secondary border-border hover:bg-surface-secondary"
            )}
          >
            Has Trips
          </button>
        </div>
      </div>

      {/* Driver List */}
      <div className="flex-1 overflow-y-auto divide-y divide-border/60 p-1.5 space-y-1">
        {error && (drivers || []).length === 0 ? (
          <div className="p-6 text-center space-y-3">
            <div className="w-10 h-10 rounded-full bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-bold text-rose-700">Failed to load drivers</p>
              <p className="text-[11px] text-content-muted mt-1 max-w-[200px] mx-auto leading-relaxed">
                {typeof error === 'string' ? error : 'Unable to connect to the tracking service.'}
              </p>
            </div>
            {typeof onRetry === 'function' && (
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-xs transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry
              </button>
            )}
          </div>
        ) : isActualLoading && (drivers || []).length === 0 ? (
          <div className="p-8 text-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin mx-auto" />
            <p className="text-xs text-content-secondary font-medium">Loading fleet drivers...</p>
          </div>
        ) : sortedDrivers.length === 0 ? (
          <div className="p-8 text-center space-y-2">
            <AlertCircle className="w-8 h-8 text-content-muted mx-auto" />
            <p className="text-xs font-semibold text-content">No drivers match your filter</p>
            <p className="text-[11px] text-content-muted">Try clearing the search or status filters</p>
          </div>
        ) : (
          sortedDrivers.map((driver) => {
            const isSelected = selectedDriver?.id === driver.id;
            const isOnline = driver.duty_status === 'ON_DUTY';
            const hasGps = (driver.gps_point_count || 0) > 0;

            return (
              <div
                key={driver.id}
                onClick={() => {
                  if (typeof onSelectDriver === 'function') {
                    onSelectDriver(driver);
                  }
                }}
                className={cn(
                  "p-3 rounded-xl cursor-pointer transition-all border text-left",
                  isSelected
                    ? "bg-brand-50/70 border-brand-500 shadow-xs ring-1 ring-brand-500/20"
                    : "bg-white border-transparent hover:border-border hover:bg-surface-secondary/50"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {/* Avatar with duty indicator */}
                    <div className="relative shrink-0">
                      <div className="w-8 h-8 rounded-full bg-brand-100/80 border border-brand-200 text-brand-700 font-bold text-xs flex items-center justify-center">
                        {driver.avatar_url ? (
                          <img
                            src={driver.avatar_url}
                            alt={driver.name}
                            className="w-full h-full rounded-full object-cover"
                          />
                        ) : (
                          (driver.name || 'DR').slice(0, 2).toUpperCase()
                        )}
                      </div>
                      <span
                        className={cn(
                          "absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white",
                          isOnline ? "bg-emerald-500" : "bg-neutral-300"
                        )}
                        title={driver.duty_status || 'Offline'}
                      />
                    </div>

                    <div className="min-w-0">
                      <h3 className="text-xs font-bold text-content truncate leading-tight">
                        {driver.name}
                      </h3>
                      <p className="text-[11px] text-content-secondary font-mono truncate mt-0.5">
                        {driver.phone_number}
                      </p>
                    </div>
                  </div>

                  {/* Duty status pill */}
                  <span
                    className={cn(
                      "text-[9px] font-bold px-1.5 py-0.5 rounded-full shrink-0 uppercase tracking-wider",
                      isOnline
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                        : "bg-surface-secondary text-content-muted border border-border"
                    )}
                  >
                    {driver.duty_status === 'ON_DUTY' ? 'ON DUTY' : driver.duty_status || 'IDLE'}
                  </span>
                </div>

                {/* Vehicle & Telemetry details */}
                <div className="mt-2.5 pt-2 border-t border-border/40 grid grid-cols-2 gap-2 text-[11px]">
                  <div className="flex items-center gap-1.5 text-content-secondary min-w-0">
                    <Truck className="w-3 h-3 text-content-muted shrink-0" />
                    <span className="truncate font-mono font-medium">
                      {driver.vehicle_registration || 'No Vehicle'}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 text-content-muted justify-end">
                    <Clock className="w-3 h-3 shrink-0" />
                    <span className="truncate">
                      {driver.last_location_at ? formatRelativeTime(driver.last_location_at) : 'No GPS update'}
                    </span>
                  </div>
                </div>

                {/* Trips & GPS metrics footer */}
                <div className="mt-2 flex items-center justify-between text-[10px] text-content-muted">
                  <span className="flex items-center gap-1 font-medium text-brand-700 bg-brand-50 px-1.5 py-0.5 rounded border border-brand-200/60">
                    <Navigation className="w-2.5 h-2.5" />
                    {driver.total_trips || 0} {(driver.total_trips || 0) === 1 ? 'trip' : 'trips'}
                  </span>

                  <span className={cn(
                    "font-mono px-1.5 py-0.5 rounded border",
                    hasGps
                      ? "bg-surface-secondary text-content font-medium border-border"
                      : "bg-neutral-50 text-neutral-400 border-neutral-100"
                  )}>
                    {(driver.gps_point_count || 0).toLocaleString()} pts
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
