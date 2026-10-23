import React, { useState, useMemo } from 'react';
import { 
  X, 
  BarChart3, 
  ListFilter, 
  Compass, 
  Gauge, 
  Clock, 
  Route, 
  MapPin, 
  AlertTriangle, 
  CheckCircle, 
  Coffee, 
  ExternalLink, 
  Copy, 
  Check, 
  Search,
  Crosshair,
  TrendingUp,
  Activity
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatDateTime, formatDurationMinutes } from '@/utils/dateTime';

/**
 * TripAnalyticsDrawer
 * Collapsible right drawer containing operational telemetry analytics 
 * and a searchable raw GPS points inspector table.
 */
export function TripAnalyticsDrawer({
  isOpen = false,
  onClose,
  analytics = null,
  locations = [],
  selectedPoint = null,
  onSelectPoint,
  driverName = '',
  vehiclePlate = '',
  activeTrip = null
}) {
  const [activeTab, setActiveTab] = useState('analytics'); // 'analytics' | 'points'
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedCoords, setCopiedCoords] = useState(false);

  // Filtered raw points for inspector table
  const filteredPoints = useMemo(() => {
    if (!searchTerm.trim()) return locations;
    const term = searchTerm.toLowerCase();
    return locations.filter((pt) => {
      const timeStr = formatDateTime(pt.timestamp, 'HH:mm:ss dd MMM').toLowerCase();
      const coords = `${pt.latitude},${pt.longitude}`;
      return timeStr.includes(term) || coords.includes(term);
    });
  }, [locations, searchTerm]);

  const handleCopy = (lat, lng) => {
    navigator.clipboard?.writeText(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    setCopiedCoords(true);
    setTimeout(() => setCopiedCoords(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <aside className="w-80 sm:w-96 h-full bg-white border-l border-slate-200 flex flex-col shadow-xl z-20 transition-all select-none">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Trip Analytics & GPS Inspector
          </h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 rounded-md transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-slate-200 bg-slate-50/40 text-xs font-semibold">
        <button
          type="button"
          onClick={() => setActiveTab('analytics')}
          className={cn(
            "flex-1 py-2 text-center border-b-2 transition-colors flex items-center justify-center gap-1.5",
            activeTab === 'analytics'
              ? "border-brand-600 text-brand-700 bg-white"
              : "border-transparent text-slate-500 hover:text-slate-800"
          )}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Operational Analytics</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('points')}
          className={cn(
            "flex-1 py-2 text-center border-b-2 transition-colors flex items-center justify-center gap-1.5",
            activeTab === 'points'
              ? "border-brand-600 text-brand-700 bg-white"
              : "border-transparent text-slate-500 hover:text-slate-800"
          )}
        >
          <ListFilter className="w-3.5 h-3.5" />
          <span>Raw Points ({locations.length})</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'analytics' ? (
          /* ── Tab 1: Operational Analytics ───────────────────────────────── */
          <div className="space-y-4">
            {/* Context Badge */}
            <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs space-y-1">
              <div className="flex justify-between items-center text-slate-500">
                <span>Driver</span>
                <span className="font-semibold text-slate-800">{driverName || 'Selected Driver'}</span>
              </div>
              {vehiclePlate && (
                <div className="flex justify-between items-center text-slate-500">
                  <span>Assigned Vehicle</span>
                  <span className="font-mono font-semibold text-slate-800">{vehiclePlate}</span>
                </div>
              )}
              {activeTrip && (
                <div className="flex justify-between items-center text-slate-500">
                  <span>Active Trip Filter</span>
                  <span className="font-mono font-semibold text-brand-700">
                    {activeTrip.trip_id || `TRP-${activeTrip.id}`}
                  </span>
                </div>
              )}
            </div>

            {/* Core Metrics Grid */}
            <div className="grid grid-cols-2 gap-2.5">
              {/* Distance */}
              <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">
                  <Route className="w-3.5 h-3.5 text-brand-600" />
                  <span>Total Distance</span>
                </div>
                <div className="text-lg font-bold text-slate-800">
                  {analytics && typeof analytics.total_distance_km === 'number'
                    ? `${analytics.total_distance_km.toFixed(1)} km`
                    : 'Not available'}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">Haversine route length</p>
              </div>

              {/* Total Trips */}
              <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">
                  <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                  <span>Total Trips</span>
                </div>
                <div className="text-lg font-bold text-slate-800">
                  {analytics?.total_trips !== undefined ? analytics.total_trips : '0'}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">In selected time range</p>
              </div>

              {/* Moving Time */}
              <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">
                  <Clock className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Moving Time</span>
                </div>
                <div className="text-sm font-bold text-slate-800">
                  {analytics?.moving_duration_minutes !== undefined
                    ? formatDurationMinutes(analytics.moving_duration_minutes)
                    : 'Not available'}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">Speed &gt; 3 km/h</p>
              </div>

              {/* Stationary / Parked */}
              <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">
                  <Coffee className="w-3.5 h-3.5 text-amber-500" />
                  <span>Stationary Time</span>
                </div>
                <div className="text-sm font-bold text-slate-800">
                  {analytics?.stationary_duration_minutes !== undefined
                    ? formatDurationMinutes(analytics.stationary_duration_minutes)
                    : 'Not available'}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">Stops &ge; 5 mins</p>
              </div>

              {/* Avg Speed */}
              <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">
                  <Gauge className="w-3.5 h-3.5 text-slate-600" />
                  <span>Avg Speed</span>
                </div>
                <div className="text-base font-bold text-slate-800">
                  {analytics && typeof analytics.avg_speed_kmh === 'number'
                    ? `${analytics.avg_speed_kmh.toFixed(1)} km/h`
                    : 'Not available'}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">Moving speed</p>
              </div>

              {/* Max Speed */}
              <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-xs">
                <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">
                  <Gauge className="w-3.5 h-3.5 text-rose-600" />
                  <span>Max Speed</span>
                </div>
                <div className="text-base font-bold text-slate-800">
                  {analytics && typeof analytics.max_speed_kmh === 'number'
                    ? `${analytics.max_speed_kmh.toFixed(1)} km/h`
                    : 'Not available'}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">Recorded peak</p>
              </div>
            </div>

            {/* Quality & Coverage Card */}
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700">GPS Telemetry Quality</span>
                <span className="font-semibold text-brand-700">
                  {analytics?.gps_coverage_percentage !== undefined
                    ? `${analytics.gps_coverage_percentage}% Coverage`
                    : '100%'}
                </span>
              </div>

              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-brand-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, analytics?.gps_coverage_percentage || 100)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                <span className="flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-amber-500" />
                  <span>GPS Gaps (&gt;15m):</span>
                </span>
                <span className="font-bold text-slate-700">
                  {analytics?.gps_gaps_count !== undefined ? analytics.gps_gaps_count : 0}
                </span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span className="flex items-center gap-1">
                  <Crosshair className="w-3 h-3 text-emerald-500" />
                  <span>Total Recorded Points:</span>
                </span>
                <span className="font-bold text-slate-700">
                  {analytics?.total_points || locations.length}
                </span>
              </div>
            </div>

            {/* Selected Point Telemetry Card */}
            {selectedPoint && (
              <div className="p-3.5 bg-brand-50/60 border border-brand-200 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-brand-800 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-brand-600" />
                    Inspected Point Telemetry
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {formatDateTime(selectedPoint.timestamp, 'HH:mm:ss')}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                  <div>
                    <span className="text-slate-400 block text-[9px] uppercase font-bold">Speed</span>
                    <span className="font-bold text-slate-800">
                      {typeof selectedPoint.speed_kmh === 'number'
                        ? `${selectedPoint.speed_kmh.toFixed(1)} km/h`
                        : typeof selectedPoint.speed === 'number'
                        ? `${(selectedPoint.speed * 3.6).toFixed(1)} km/h`
                        : 'Not available'}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[9px] uppercase font-bold">Bearing</span>
                    <span className="font-bold text-slate-800">
                      {typeof selectedPoint.heading === 'number' ? `${Math.round(selectedPoint.heading)}°` : 'Not available'}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[9px] uppercase font-bold">GPS Accuracy</span>
                    <span className="font-bold text-slate-800">
                      {typeof selectedPoint.accuracy === 'number' ? `±${selectedPoint.accuracy.toFixed(1)}m` : 'Not available'}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[9px] uppercase font-bold">Trip ID</span>
                    <span className="font-mono text-slate-700 truncate block">
                      {selectedPoint.trip_id ? `TRP-${selectedPoint.trip_id}` : 'Unassigned'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-brand-200/60 text-[10px]">
                  <span className="font-mono text-slate-600">
                    {selectedPoint.latitude.toFixed(5)}, {selectedPoint.longitude.toFixed(5)}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleCopy(selectedPoint.latitude, selectedPoint.longitude)}
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-700 hover:text-brand-600 font-medium"
                    >
                      {copiedCoords ? <Check className="w-2.5 h-2.5 text-emerald-600" /> : <Copy className="w-2.5 h-2.5" />}
                      <span>{copiedCoords ? 'Copied' : 'Copy'}</span>
                    </button>
                    <a
                      href={`https://www.google.com/maps?q=${selectedPoint.latitude},${selectedPoint.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-700 hover:text-brand-600 font-medium"
                    >
                      <ExternalLink className="w-2.5 h-2.5" />
                      <span>Maps</span>
                    </a>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* ── Tab 2: Raw GPS Points Table ────────────────────────────────── */
          <div className="space-y-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search time (HH:mm) or coords..."
                className="w-full text-xs py-1.5 pl-8 pr-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            {/* Table */}
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-[11px] text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[9px]">
                  <tr>
                    <th className="py-1.5 px-2">#</th>
                    <th className="py-1.5 px-2">Time</th>
                    <th className="py-1.5 px-2">Speed</th>
                    <th className="py-1.5 px-2">Coords</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {filteredPoints.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-slate-400 font-sans text-xs">
                        No points found
                      </td>
                    </tr>
                  ) : (
                    filteredPoints.slice(0, 150).map((pt, i) => {
                      const isSel = selectedPoint && selectedPoint.id === pt.id;
                      const spd = typeof pt.speed_kmh === 'number'
                        ? pt.speed_kmh
                        : typeof pt.speed === 'number'
                        ? pt.speed * 3.6
                        : null;

                      return (
                        <tr
                          key={pt.id || i}
                          onClick={() => onSelectPoint && onSelectPoint(pt)}
                          className={cn(
                            "cursor-pointer hover:bg-slate-50 transition-colors",
                            isSel && "bg-brand-50 font-bold text-brand-900"
                          )}
                        >
                          <td className="py-1 px-2 text-slate-400">{i + 1}</td>
                          <td className="py-1 px-2 text-slate-700">
                            {formatDateTime(pt.timestamp, 'HH:mm:ss')}
                          </td>
                          <td className="py-1 px-2 text-slate-700">
                            {spd !== null ? `${spd.toFixed(1)}k` : '—'}
                          </td>
                          <td className="py-1 px-2 text-slate-500 text-[10px] truncate max-w-[100px]">
                            {pt.latitude.toFixed(4)}, {pt.longitude.toFixed(4)}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
              {filteredPoints.length > 150 && (
                <div className="p-2 text-center text-[10px] text-slate-400 bg-slate-50 border-t border-slate-100">
                  Showing first 150 of {filteredPoints.length} points
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
