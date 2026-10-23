import React from 'react';
import {
  Search, Users, Truck, Navigation, Clock,
  CheckCircle, ArrowUpDown, Shield, AlertCircle
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatRelativeTime } from '@/utils/dateTime';

export function DriverSidebar({
  drivers = [],
  selectedDriver = null,
  onSelectDriver,
  loading = false,
  searchTerm = '',
  onSearchChange,
  dutyStatusFilter = 'all',
  onDutyStatusChange,
  hasTripsFilter = false,
  onHasTripsFilterToggle,
  sortBy = 'latest_activity',
  onSortByChange,
}) {
  // Filter and sort drivers locally if already loaded, but also controlled
  const filteredDrivers = drivers.filter(d => {
    if (dutyStatusFilter !== 'all' && d.duty_status !== dutyStatusFilter) return false;
    if (hasTripsFilter && d.total_trips === 0) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchName = d.name?.toLowerCase().includes(q);
      const matchPhone = d.phone_number?.includes(q);
      const matchVeh = d.vehicle_registration?.toLowerCase().includes(q);
      const matchEmp = d.employee_id?.toLowerCase().includes(q);
      if (!matchName && !matchPhone && !matchVeh && !matchEmp) return false;
    }
    return true;
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
            {filteredDrivers.length} of {drivers.length}
          </span>
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-content-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search driver, vehicle plate, phone..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-border rounded-lg placeholder:text-content-muted focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 transition-all shadow-xs"
          />
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
          <select
            value={dutyStatusFilter}
            onChange={(e) => onDutyStatusChange(e.target.value)}
            className="text-[11px] py-1 px-2 bg-white border border-border rounded-md text-content font-medium focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="all">All Statuses</option>
            <option value="ON_DUTY">On Duty</option>
            <option value="OFF_DUTY">Off Duty</option>
            <option value="ON_BREAK">On Break</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => onSortByChange(e.target.value)}
            className="text-[11px] py-1 px-2 bg-white border border-border rounded-md text-content font-medium focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="latest_activity">Latest Activity</option>
            <option value="name">Name (A-Z)</option>
            <option value="trips_count">Most Trips</option>
            <option value="gps_points">GPS Points Count</option>
          </select>

          <button
            type="button"
            onClick={() => onHasTripsFilterToggle(!hasTripsFilter)}
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
        {loading && drivers.length === 0 ? (
          <div className="p-8 text-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin mx-auto" />
            <p className="text-xs text-content-secondary font-medium">Loading fleet drivers...</p>
          </div>
        ) : filteredDrivers.length === 0 ? (
          <div className="p-8 text-center space-y-2">
            <AlertCircle className="w-8 h-8 text-content-muted mx-auto" />
            <p className="text-xs font-semibold text-content">No drivers match your filter</p>
            <p className="text-[11px] text-content-muted">Try clearing the search or status filters</p>
          </div>
        ) : (
          filteredDrivers.map((driver) => {
            const isSelected = selectedDriver?.id === driver.id;
            const isOnline = driver.duty_status === 'ON_DUTY';
            const hasGps = driver.gps_point_count > 0;

            return (
              <div
                key={driver.id}
                onClick={() => onSelectDriver(driver)}
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
                          driver.name.slice(0, 2).toUpperCase()
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
                    {driver.total_trips} {driver.total_trips === 1 ? 'trip' : 'trips'}
                  </span>

                  <span className={cn(
                    "font-mono px-1.5 py-0.5 rounded border",
                    hasGps
                      ? "bg-surface-secondary text-content font-medium border-border"
                      : "bg-neutral-50 text-neutral-400 border-neutral-100"
                  )}>
                    {driver.gps_point_count.toLocaleString()} pts
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
