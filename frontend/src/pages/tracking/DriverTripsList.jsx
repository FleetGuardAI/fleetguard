import React, { useState } from 'react';
import { Route, Clock, Navigation, AlertTriangle, CheckCircle, Play, ChevronRight, Calendar, ArrowUpDown, Filter } from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatDateTime, formatDurationMinutes } from '@/utils/dateTime';

/**
 * DriverTripsList
 * Renders real historical trips for the selected driver.
 * Allows filtering, sorting, selecting a trip to isolate its route, or clearing selection to see all trips.
 */
export function DriverTripsList({
  trips = [],
  selectedTrip = null,
  onSelectTrip,
  onClearTrip,
  isLoading = false,
  driverName = ''
}) {
  const [sortBy, setSortBy] = useState('newest'); // newest, oldest, distance, duration
  const [statusFilter, setStatusFilter] = useState('ALL'); // ALL, COMPLETED, IN_PROGRESS, SCHEDULED, CANCELLED

  // Filter trips
  const filteredTrips = trips.filter((trip) => {
    if (statusFilter === 'ALL') return true;
    const status = (trip.status || '').toUpperCase();
    if (statusFilter === 'IN_PROGRESS') return status === 'IN_PROGRESS' || status === 'ON-TRIP';
    return status === statusFilter;
  });

  // Sort trips
  const sortedTrips = [...filteredTrips].sort((a, b) => {
    const timeA = new Date(a.start_time || a.start_date || a.created_at || 0).getTime();
    const timeB = new Date(b.start_time || b.start_date || b.created_at || 0).getTime();

    if (sortBy === 'newest') return timeB - timeA;
    if (sortBy === 'oldest') return timeA - timeB;
    if (sortBy === 'distance') return (b.distance_km || 0) - (a.distance_km || 0);
    if (sortBy === 'duration') return (b.duration_minutes || 0) - (a.duration_minutes || 0);
    return 0;
  });

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'COMPLETED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
          <CheckCircle className="w-2.5 h-2.5" /> Completed
        </span>
      );
    }
    if (s === 'IN_PROGRESS' || s === 'ON-TRIP') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-full border border-brand-200 animate-pulse">
          <Play className="w-2.5 h-2.5 fill-brand-600" /> Active Trip
        </span>
      );
    }
    if (s === 'CANCELLED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
          Cancelled
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
        {status || 'Scheduled'}
      </span>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white border-t border-slate-200">
      {/* Header */}
      <div className="p-3 border-b border-slate-100 bg-slate-50/70">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Route className="w-4 h-4 text-brand-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Driver Trips ({trips.length})
            </h3>
          </div>
          {selectedTrip && (
            <button
              onClick={onClearTrip}
              className="text-[11px] font-semibold text-brand-600 hover:text-brand-800 underline transition-colors"
            >
              View Full History
            </button>
          )}
        </div>

        {/* Filters and Sorting bar */}
        <div className="mt-2 flex items-center gap-2">
          <div className="relative flex-1">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full text-[11px] py-1 pl-2 pr-6 bg-white border border-slate-200 rounded-md text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="ALL">All Statuses ({trips.length})</option>
              <option value="IN_PROGRESS">Active / In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div className="relative flex-1">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full text-[11px] py-1 pl-2 pr-6 bg-white border border-slate-200 rounded-md text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="newest">Sort: Newest</option>
              <option value="oldest">Sort: Oldest</option>
              <option value="distance">Sort: Distance</option>
              <option value="duration">Sort: Duration</option>
            </select>
          </div>
        </div>
      </div>

      {/* Trips list */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((n) => (
              <div key={n} className="animate-pulse space-y-2 p-2 rounded-lg bg-slate-50">
                <div className="h-3 bg-slate-200 rounded w-1/3" />
                <div className="h-4 bg-slate-200 rounded w-3/4" />
                <div className="h-3 bg-slate-200 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : sortedTrips.length === 0 ? (
          <div className="p-6 text-center text-slate-400">
            <Route className="w-8 h-8 mx-auto mb-2 text-slate-300 stroke-1" />
            <p className="text-xs font-medium text-slate-600">No trips recorded</p>
            <p className="text-[11px] text-slate-400 mt-1">
              {statusFilter !== 'ALL'
                ? `No trips found matching '${statusFilter}'.`
                : `No historical trips on file for ${driverName || 'this driver'}.`}
            </p>
          </div>
        ) : (
          sortedTrips.map((trip) => {
            const isSelected = selectedTrip && (selectedTrip.id === trip.id || selectedTrip.trip_id === trip.trip_id);
            const startTime = trip.start_time || trip.start_date || trip.created_at;
            const endTime = trip.end_time || trip.end_date;
            const distance = typeof trip.distance_km === 'number' ? `${trip.distance_km.toFixed(1)} km` : 'Not available';
            const duration = trip.duration_minutes
              ? formatDurationMinutes(trip.duration_minutes)
              : 'Not available';

            return (
              <button
                key={trip.id || trip.trip_id}
                type="button"
                onClick={() => onSelectTrip(trip)}
                className={cn(
                  "w-full text-left p-3 transition-all flex flex-col gap-1.5 relative border-l-4",
                  isSelected
                    ? "bg-brand-50/70 border-brand-500 shadow-sm"
                    : "border-transparent hover:bg-slate-50/80"
                )}
              >
                {/* Top Row: Trip ID + Status */}
                <div className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="font-mono text-[11px] font-bold text-slate-800 truncate">
                      {trip.trip_id || `TRP-${trip.id}`}
                    </span>
                    {trip.gps_points_count > 0 && (
                      <span className="inline-flex items-center text-[9px] font-bold text-brand-700 bg-brand-100/80 px-1.5 py-0.2 rounded">
                        {trip.gps_points_count} pts
                      </span>
                    )}
                  </div>
                  {getStatusBadge(trip.status)}
                </div>

                {/* Route Names */}
                <div className="text-[11px] font-medium text-slate-700 leading-snug">
                  {trip.start_point && trip.end_point ? (
                    <div className="flex items-center gap-1">
                      <span className="truncate">{trip.start_point}</span>
                      <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
                      <span className="truncate">{trip.end_point}</span>
                    </div>
                  ) : (
                    <span className="text-slate-500 italic">Route endpoints not specified</span>
                  )}
                </div>

                {/* Metrics: Distance, Duration, Start Date */}
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-100/80">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-700">{distance}</span>
                    <span>•</span>
                    <span>{duration}</span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-400">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{startTime ? formatDateTime(startTime, 'dd MMM, HH:mm') : 'N/A'}</span>
                  </div>
                </div>

                {/* Warning if 0 points recorded */}
                {trip.gps_points_count === 0 && (
                  <div className="flex items-center gap-1 text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded mt-0.5">
                    <AlertTriangle className="w-2.5 h-2.5 shrink-0" />
                    <span>No GPS breadcrumbs persisted for this trip</span>
                  </div>
                )}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
