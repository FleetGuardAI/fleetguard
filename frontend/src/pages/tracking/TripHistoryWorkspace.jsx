import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Navigation, 
  MapPin, 
  Truck, 
  Users, 
  Calendar, 
  RefreshCw, 
  BarChart3, 
  Maximize2, 
  Minimize2, 
  ChevronLeft, 
  ChevronRight, 
  AlertCircle,
  Clock,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { 
  getTrackingDrivers, 
  getDriverTrips, 
  getDriverLocations, 
  getDriverAnalytics, 
  getTripRoute 
} from '@/api/telematicsApi';
import { getTimeFilterRange, formatDateTime } from '@/utils/dateTime';

import { DriverSidebar } from './DriverSidebar';
import { DriverTripsList } from './DriverTripsList';
import { TimeFilterBar } from './TimeFilterBar';
import { TripTrackingMap } from './TripTrackingMap';
import { PlaybackControls } from './PlaybackControls';
import { TripAnalyticsDrawer } from './TripAnalyticsDrawer';

export default function TripHistoryWorkspace() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // ── Selection State ────────────────────────────────────────────────────────
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [driverTrips, setDriverTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);

  // ── Time Filter State (Defaults to '7d') ───────────────────────────────────
  const [timePreset, setTimePreset] = useState('7d');
  const [customRange, setCustomRange] = useState({
    startDate: '',
    startTime: '00:00',
    endDate: '',
    endTime: '23:59',
  });
  const [activeDateRange, setActiveDateRange] = useState(() => getTimeFilterRange('7d'));

  // ── Location & Telemetry Data ───────────────────────────────────────────────
  const [locations, setLocations] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [stops, setStops] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [selectedPoint, setSelectedPoint] = useState(null);

  // ── UI States ──────────────────────────────────────────────────────────────
  const [isLoadingDrivers, setIsLoadingDrivers] = useState(false);
  const [isLoadingTrips, setIsLoadingTrips] = useState(false);
  const [isLoadingLocations, setIsLoadingLocations] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [analyticsDrawerOpen, setAnalyticsDrawerOpen] = useState(false);
  const [fitBoundsTrigger, setFitBoundsTrigger] = useState(0);

  // ── Playback State ─────────────────────────────────────────────────────────
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);
  const playbackTimerRef = useRef(null);

  // Active AbortController ref to cancel stale requests
  const abortControllerRef = useRef(null);

  // ── 1. Fetch Drivers on Mount ──────────────────────────────────────────────
  const loadDrivers = useCallback(async () => {
    setIsLoadingDrivers(true);
    setErrorMessage(null);
    try {
      const data = await getTrackingDrivers();
      setDrivers(data || []);

      // If URL has driver_id param, select it
      const driverIdParam = searchParams.get('driver_id');
      if (driverIdParam) {
        const found = data.find((d) => String(d.id) === String(driverIdParam));
        if (found) {
          setSelectedDriver(found);
          return;
        }
      }

      // Default select first driver if none selected
      if (!selectedDriver && data && data.length > 0) {
        setSelectedDriver(data[0]);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setErrorMessage(err.message || 'Failed to load drivers for fleet.');
      }
    } finally {
      setIsLoadingDrivers(false);
    }
  }, [searchParams, selectedDriver]);

  useEffect(() => {
    loadDrivers();
  }, []);

  // ── 2. Load Driver Trips and Telemetry ──────────────────────────────────────
  const loadDriverData = useCallback(async () => {
    if (!selectedDriver) return;

    // Abort previous in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    setIsLoadingTrips(true);
    setIsLoadingLocations(true);
    setErrorMessage(null);
    setIsPlaying(false);

    try {
      // 1. Fetch driver trips
      const tripsData = await getDriverTrips(selectedDriver.id, {}, { signal });
      setDriverTrips(tripsData || []);

      // Check if URL specified a trip_id
      const tripIdParam = searchParams.get('trip_id');
      let targetTrip = null;
      if (tripIdParam) {
        targetTrip = tripsData.find(
          (t) => String(t.id) === String(tripIdParam) || String(t.trip_id) === String(tripIdParam)
        );
        if (targetTrip) {
          setSelectedTrip(targetTrip);
        }
      }

      // 2. Fetch locations and analytics
      let locData;
      let analyticsData;

      if (targetTrip) {
        // Fetch specific trip route
        const tripPoints = await getTripRoute(targetTrip.id || targetTrip.trip_id, { signal });
        locData = {
          points: tripPoints || [],
          gaps: [],
          stops: [],
          total_points: (tripPoints || []).length,
        };
        analyticsData = await getDriverAnalytics(selectedDriver.id, {}, { signal });
      } else {
        // Fetch locations for driver within active date range
        const params = {
          start_time: activeDateRange.startTime.toISOString(),
          end_time: activeDateRange.endTime.toISOString(),
          downsample: 600, // keep rendering silky smooth
        };
        const [locRes, anRes] = await Promise.all([
          getDriverLocations(selectedDriver.id, params, { signal }),
          getDriverAnalytics(selectedDriver.id, params, { signal }),
        ]);
        locData = locRes;
        analyticsData = anRes;
      }

      const points = locData?.points || [];
      setLocations(points);
      setGaps(locData?.gaps || []);
      setStops(locData?.stops || []);
      setAnalytics(analyticsData);

      // Reset playback index to 0
      setPlaybackIndex(0);
      setSelectedPoint(points[0] || null);
      setFitBoundsTrigger((prev) => prev + 1);
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Error loading driver telemetry:', err);
        setErrorMessage(err.message || 'Failed to retrieve location telemetry.');
      }
    } finally {
      setIsLoadingTrips(false);
      setIsLoadingLocations(false);
    }
  }, [selectedDriver, activeDateRange, searchParams]);

  useEffect(() => {
    loadDriverData();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [selectedDriver, activeDateRange]);

  // ── 3. Handle Driver Switch ────────────────────────────────────────────────
  const handleSelectDriver = (driver) => {
    if (selectedDriver?.id === driver.id) return;
    setIsPlaying(false);
    setSelectedTrip(null);
    setSelectedPoint(null);
    setSelectedDriver(driver);
    setSearchParams({ driver_id: driver.id });
  };

  // ── 4. Handle Trip Selection ───────────────────────────────────────────────
  const handleSelectTrip = async (trip) => {
    setSelectedTrip(trip);
    setIsPlaying(false);
    setIsLoadingLocations(true);
    setErrorMessage(null);

    // Abort previous in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    try {
      const tripPoints = await getTripRoute(trip.id || trip.trip_id, { signal });
      setLocations(tripPoints || []);
      setGaps([]);
      setStops([]);
      setPlaybackIndex(0);
      setSelectedPoint(tripPoints && tripPoints.length > 0 ? tripPoints[0] : null);
      setFitBoundsTrigger((prev) => prev + 1);

      setSearchParams({ driver_id: selectedDriver.id, trip_id: trip.trip_id || trip.id });
    } catch (err) {
      if (err.name !== 'AbortError') {
        setErrorMessage(err.message || 'Failed to load route for selected trip.');
      }
    } finally {
      setIsLoadingLocations(false);
    }
  };

  const handleClearTrip = () => {
    setSelectedTrip(null);
    setSearchParams({ driver_id: selectedDriver?.id });
    loadDriverData();
  };

  // ── 5. Playback Loop ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!isPlaying || locations.length <= 1) {
      if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
      return;
    }

    if (playbackIndex >= locations.length - 1) {
      // Reached the end
      setIsPlaying(false);
      return;
    }

    const currentPt = locations[playbackIndex];
    const nextPt = locations[playbackIndex + 1];

    // Compute delta between recorded points
    let deltaMs = 500;
    if (currentPt?.timestamp && nextPt?.timestamp) {
      const t1 = new Date(currentPt.timestamp).getTime();
      const t2 = new Date(nextPt.timestamp).getTime();
      const diff = Math.abs(t2 - t1);
      // Scale by speedMultiplier and clamp between 150ms and 1200ms
      deltaMs = Math.min(1200, Math.max(150, Math.round(diff / (speedMultiplier * 50))));
    }

    playbackTimerRef.current = setTimeout(() => {
      setPlaybackIndex((prev) => {
        const next = prev + 1;
        if (locations[next]) {
          setSelectedPoint(locations[next]);
        }
        return next;
      });
    }, deltaMs);

    return () => {
      if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
    };
  }, [isPlaying, playbackIndex, locations, speedMultiplier]);

  // Playback Control Handlers
  const handlePlayPause = () => {
    if (locations.length === 0) return;
    if (playbackIndex >= locations.length - 1) {
      setPlaybackIndex(0);
    }
    setIsPlaying((prev) => !prev);
  };

  const handleSeek = (index) => {
    setPlaybackIndex(index);
    if (locations[index]) {
      setSelectedPoint(locations[index]);
    }
  };

  const handleRestart = () => {
    setPlaybackIndex(0);
    if (locations[0]) {
      setSelectedPoint(locations[0]);
    }
  };

  const handleStepBack = () => {
    setPlaybackIndex((prev) => {
      const next = Math.max(0, prev - 1);
      if (locations[next]) setSelectedPoint(locations[next]);
      return next;
    });
  };

  const handleStepForward = () => {
    setPlaybackIndex((prev) => {
      const next = Math.min(locations.length - 1, prev + 1);
      if (locations[next]) setSelectedPoint(locations[next]);
      return next;
    });
  };

  const handleJumpStart = () => {
    setPlaybackIndex(0);
    if (locations[0]) setSelectedPoint(locations[0]);
  };

  const handleJumpEnd = () => {
    const last = locations.length - 1;
    setPlaybackIndex(last);
    if (locations[last]) setSelectedPoint(locations[last]);
  };

  const currentPlaybackPoint = locations[playbackIndex] || null;

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] w-full overflow-hidden bg-slate-100 select-none">
      {/* ── Top Header Toolbar ──────────────────────────────────────────────── */}
      <header className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-white border-b border-slate-200 z-20 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-brand-50 text-brand-600 border border-brand-200">
              <Navigation className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-800 leading-tight">
                Trip History & GPS Playback
              </h1>
              <p className="text-[11px] text-slate-500">
                The Vahan Geospatial Fleet Intelligence
              </p>
            </div>
          </div>

          {/* Active Context Badges */}
          {selectedDriver && (
            <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-slate-200">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>{selectedDriver.name}</span>
              </div>

              {selectedDriver.vehicle_plate && (
                <div className="flex items-center gap-1.5 text-xs font-mono font-semibold text-slate-700 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                  <Truck className="w-3.5 h-3.5 text-slate-400" />
                  <span>{selectedDriver.vehicle_plate}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadDriverData}
            title="Refresh Telemetry"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:text-brand-600 transition-colors shadow-xs"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", (isLoadingLocations || isLoadingTrips) && "animate-spin")} />
            <span className="hidden md:inline">Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => setAnalyticsDrawerOpen((prev) => !prev)}
            title="Trip Analytics Drawer"
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors shadow-xs",
              analyticsDrawerOpen
                ? "bg-brand-50 border-brand-300 text-brand-700"
                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
            )}
          >
            <BarChart3 className="w-3.5 h-3.5 text-brand-600" />
            <span className="hidden md:inline">Analytics</span>
          </button>
        </div>
      </header>

      {/* ── Time Filter Bar (Below Header) ──────────────────────────────────── */}
      <div className="shrink-0">
        <TimeFilterBar
          activePreset={timePreset}
          startTime={activeDateRange?.startTime}
          endTime={activeDateRange?.endTime}
          onApplyRange={(range) => {
            setTimePreset(range.preset || 'custom');
            setActiveDateRange({
              startTime: range.startTime ? new Date(range.startTime) : null,
              endTime: range.endTime ? new Date(range.endTime) : null,
            });
          }}
          onReset={() => {
            setTimePreset('7d');
            setActiveDateRange(getTimeFilterRange('7d'));
          }}
          selectedTrip={selectedTrip}
          onClearTrip={selectedTrip ? handleClearTrip : null}
        />
      </div>

      {/* ── Error Banner ────────────────────────────────────────────────────── */}
      {errorMessage && (
        <div className="px-4 py-2 bg-rose-50 border-b border-rose-200 text-rose-700 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-500 hover:text-rose-800 font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── Main Workspace Body ─────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar: Driver Selection + Trips List */}
        <aside
          className={cn(
            "h-full bg-white border-r border-slate-200 flex flex-col transition-all duration-200 z-10 shrink-0",
            sidebarCollapsed ? "w-0 overflow-hidden border-none" : "w-80 sm:w-96"
          )}
        >
          {/* Driver Selection Section (Top 55%) */}
          <div className="h-[55%] flex flex-col min-h-0 border-b border-slate-200">
            <DriverSidebar
              drivers={drivers}
              selectedDriver={selectedDriver}
              onSelectDriver={handleSelectDriver}
              isLoading={isLoadingDrivers}
            />
          </div>

          {/* Driver Trips Section (Bottom 45%) */}
          <div className="h-[45%] flex flex-col min-h-0">
            <DriverTripsList
              trips={driverTrips}
              selectedTrip={selectedTrip}
              onSelectTrip={handleSelectTrip}
              onClearTrip={handleClearTrip}
              isLoading={isLoadingTrips}
              driverName={selectedDriver?.name}
            />
          </div>
        </aside>

        {/* Sidebar Toggle Button */}
        <button
          type="button"
          onClick={() => setSidebarCollapsed((prev) => !prev)}
          title={sidebarCollapsed ? "Expand Driver Panel" : "Collapse Driver Panel"}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white/95 border border-slate-300 text-slate-600 p-1 rounded-r-lg shadow-md hover:text-brand-600 transition-colors"
          style={{ left: sidebarCollapsed ? '0px' : undefined }}
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>

        {/* Center: Interactive Map Area */}
        <main className="flex-1 h-full relative overflow-hidden flex flex-col">
          <TripTrackingMap
            locations={locations}
            gaps={gaps}
            stops={stops}
            currentPlaybackPoint={currentPlaybackPoint}
            isPlaying={isPlaying}
            selectedPoint={selectedPoint}
            onSelectPoint={(pt) => setSelectedPoint(pt)}
            isLoading={isLoadingLocations}
            driverName={selectedDriver?.name}
            vehiclePlate={selectedDriver?.vehicle_plate}
            fitBoundsTrigger={fitBoundsTrigger}
            onTriggerFitBounds={() => setFitBoundsTrigger((prev) => prev + 1)}
          />

          {/* Floating Playback Controls Bar */}
          {locations.length > 0 && (
            <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-20 w-[95%] max-w-2xl pointer-events-auto">
              <PlaybackControls
                points={locations}
                currentIndex={playbackIndex}
                isPlaying={isPlaying}
                speedMultiplier={speedMultiplier}
                onPlayPause={handlePlayPause}
                onSeek={handleSeek}
                onRestart={handleRestart}
                onSpeedChange={setSpeedMultiplier}
                onStepBack={handleStepBack}
                onStepForward={handleStepForward}
                onJumpStart={handleJumpStart}
                onJumpEnd={handleJumpEnd}
              />
            </div>
          )}
        </main>

        {/* Right Drawer: Trip Analytics & Raw Points Inspector */}
        <TripAnalyticsDrawer
          isOpen={analyticsDrawerOpen}
          onClose={() => setAnalyticsDrawerOpen(false)}
          analytics={analytics}
          locations={locations}
          selectedPoint={selectedPoint}
          onSelectPoint={(pt) => {
            setSelectedPoint(pt);
            const idx = locations.findIndex((p) => p.id === pt.id);
            if (idx >= 0) setPlaybackIndex(idx);
          }}
          driverName={selectedDriver?.name}
          vehiclePlate={selectedDriver?.vehicle_plate}
          activeTrip={selectedTrip}
        />
      </div>
    </div>
  );
}
