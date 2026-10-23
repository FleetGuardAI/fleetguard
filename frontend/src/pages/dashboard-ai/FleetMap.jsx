import React, { useMemo, useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  MapContainer, 
  TileLayer, 
  Marker, 
  Tooltip, 
  Popup, 
  Polyline, 
  CircleMarker, 
  useMap 
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { renderToStaticMarkup } from 'react-dom/server';
import { 
  Navigation, 
  Clock, 
  Route as RouteIcon, 
  X, 
  Maximize2, 
  Minimize2, 
  RefreshCw, 
  BarChart3, 
  ChevronLeft, 
  ChevronRight, 
  LocateFixed, 
  Layers, 
  Play, 
  Square, 
  Coffee, 
  AlertTriangle, 
  ExternalLink, 
  Copy, 
  Check, 
  Truck, 
  Users, 
  AlertCircle 
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Telematics and Date Utilities
import { 
  getTrackingDrivers, 
  getDriverTrips, 
  getDriverLocations, 
  getDriverAnalytics, 
  getTripRoute 
} from '@/api/telematicsApi';
import { getTimeFilterRange, formatDateTime, formatDurationMinutes } from '@/utils/dateTime';

// Tracking Subcomponents
import { DriverSidebar } from '../tracking/DriverSidebar';
import { DriverTripsList } from '../tracking/DriverTripsList';
import { TimeFilterBar } from '../tracking/TimeFilterBar';
import { PlaybackControls } from '../tracking/PlaybackControls';
import { TripAnalyticsDrawer } from '../tracking/TripAnalyticsDrawer';

// ── Invalidate Map Size upon layout transitions ─────────────────────────────
function MapInvalidator({ isExpanded, sidebarCollapsed }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    const t1 = setTimeout(() => map.invalidateSize(), 100);
    const t2 = setTimeout(() => map.invalidateSize(), 300);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [map, isExpanded, sidebarCollapsed]);
  return null;
}

// ── Auto-adjust map bounds to fit markers or route ──────────────────────────
function MapBoundsController({ trucks, routeBounds, fitTrigger }) {
  const map = useMap();
  useEffect(() => {
    if (routeBounds && routeBounds.length >= 2) {
      try {
        map.fitBounds(routeBounds, { padding: [60, 60], maxZoom: 16 });
      } catch (e) {}
    } else if (trucks && trucks.length > 0) {
      const validTrucks = trucks.filter(t => t.lat && t.lng && !isNaN(t.lat) && !isNaN(t.lng));
      if (validTrucks.length > 0) {
        const bounds = validTrucks.map(t => [t.lat, t.lng]);
        if (bounds.length === 1) {
          map.setView(bounds[0], 13);
        } else {
          try {
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
          } catch (e) {}
        }
      }
    }
  }, [map, routeBounds, trucks, fitTrigger]);
  return null;
}

// ── Follow playback vehicle ─────────────────────────────────────────────────
function MapFollower({ currentPoint, isPlaying }) {
  const map = useMap();
  useEffect(() => {
    if (isPlaying && currentPoint?.latitude && currentPoint?.longitude) {
      const bounds = map.getBounds();
      const pointLatLng = L.latLng(currentPoint.latitude, currentPoint.longitude);
      if (!bounds.pad(-0.15).contains(pointLatLng)) {
        map.panTo(pointLatLng, { animate: true, duration: 0.5 });
      }
    }
  }, [map, currentPoint, isPlaying]);
  return null;
}

// ── Custom Leaflet HTML Markers ─────────────────────────────────────────────
const createTruckIcon = (truck, isSelected) => {
  const isIdle = truck.status === 'idle';
  const iconHtml = renderToStaticMarkup(
    <div className="group relative cursor-pointer" style={{ width: '32px', height: '32px' }}>
      <div className={cn(
        "absolute -inset-2 rounded-full blur-xs opacity-0 transition-opacity",
        isSelected ? "bg-brand-500/40 opacity-100 animate-pulse" : "bg-brand-500/20"
      )} />
      <div className={cn(
        "relative flex items-center justify-center w-full h-full rounded-full shadow-lg border-2 transition-all",
        isIdle && !isSelected ? "bg-white border-slate-300 text-slate-500" : "bg-brand-600 border-white text-white",
        isSelected && "scale-110 shadow-brand-500/40 ring-2 ring-brand-500"
      )}>
        <Navigation className="w-4 h-4 transition-transform" style={{ transform: `rotate(${truck.heading || 0}deg)` }} />
      </div>
    </div>
  );

  return L.divIcon({
    html: iconHtml,
    className: 'custom-leaflet-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

const createStartIcon = () => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-emerald-600 text-white shadow-lg border-2 border-white ring-2 ring-emerald-500/40">
      <Play className="w-4 h-4 fill-white ml-0.5" />
    </div>
  );
  return L.divIcon({
    html,
    className: 'custom-leaflet-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
};

const createEndIcon = () => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-rose-600 text-white shadow-lg border-2 border-white ring-2 ring-rose-500/40">
      <Square className="w-3.5 h-3.5 fill-white" />
    </div>
  );
  return L.divIcon({
    html,
    className: 'custom-leaflet-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
};

const createStopIcon = () => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center w-7 h-7 rounded-full bg-amber-500 text-white shadow-md border-2 border-white ring-1 ring-amber-400">
      <Coffee className="w-3.5 h-3.5" />
    </div>
  );
  return L.divIcon({
    html,
    className: 'custom-leaflet-icon',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  });
};

const createGapIcon = () => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 text-amber-400 shadow-md border-2 border-amber-400">
      <AlertTriangle className="w-3 h-3" />
    </div>
  );
  return L.divIcon({
    html,
    className: 'custom-leaflet-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
};

const createPlaybackVehicleIcon = (heading = 0) => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center" style={{ width: '40px', height: '40px' }}>
      <div className="absolute inset-0 rounded-full bg-emerald-500/30 animate-ping" />
      <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-emerald-600 border-2 border-white text-white shadow-xl">
        <Navigation 
          className="w-4 h-4 transition-transform duration-200" 
          style={{ transform: `rotate(${heading || 0}deg)` }} 
        />
      </div>
    </div>
  );
  return L.divIcon({
    html,
    className: 'custom-leaflet-icon',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -22],
  });
};

export function FleetMap({ 
  trucks = [], 
  onRefresh = null, 
  isRefreshing = false 
}) {
  const [searchParams, setSearchParams] = useSearchParams();

  // ── Expand/Collapse State ──────────────────────────────────────────────────
  const [isExpanded, setIsExpanded] = useState(() => searchParams.get('expand') === 'true');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [analyticsDrawerOpen, setAnalyticsDrawerOpen] = useState(false);
  const [showAllPointDots, setShowAllPointDots] = useState(false);

  // ── Historical Tracking State ──────────────────────────────────────────────
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [driverTrips, setDriverTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);

  // Time filters
  const [timePreset, setTimePreset] = useState('7d');
  const [activeDateRange, setActiveDateRange] = useState(() => getTimeFilterRange('7d'));

  // Telemetry data
  const [locations, setLocations] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [stops, setStops] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [fitTrigger, setFitTrigger] = useState(0);

  // Loading and error states
  const [isLoadingDrivers, setIsLoadingDrivers] = useState(false);
  const [isLoadingTrips, setIsLoadingTrips] = useState(false);
  const [isLoadingLocations, setIsLoadingLocations] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [driversError, setDriversError] = useState(null);
  const [tripsError, setTripsError] = useState(null);
  const [telemetryError, setTelemetryError] = useState(null);

  // Driver Sidebar filter controls
  const [driverSearchTerm, setDriverSearchTerm] = useState('');
  const [driverDutyStatus, setDriverDutyStatus] = useState('all');
  const [driverSortBy, setDriverSortBy] = useState('latest_activity');
  const [driverHasTripsFilter, setDriverHasTripsFilter] = useState(false);

  // ── Playback State & Request Cancellation Refs ─────────────────────────────
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);
  const playbackTimerRef = useRef(null);
  const tripsAbortRef = useRef(null);
  const telemetryAbortRef = useRef(null);
  const tripsRequestIdRef = useRef(0);
  const telemetryRequestIdRef = useRef(0);

  // Coordinates copy feedback
  const [copiedCoords, setCopiedCoords] = useState(false);

  // Default center (Bangalore / India or first truck)
  const defaultCenter = useMemo(() => {
    if (trucks.length > 0 && trucks[0].lat && trucks[0].lng) {
      return [trucks[0].lat, trucks[0].lng];
    }
    return [30.3165, 78.0322]; // Dehradun / India
  }, [trucks]);

  // Clean up timers and in-flight requests on component unmount
  useEffect(() => {
    return () => {
      if (tripsAbortRef.current) tripsAbortRef.current.abort();
      if (telemetryAbortRef.current) telemetryAbortRef.current.abort();
      if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);
    };
  }, []);

  // ── Escape Key Handler to exit expanded mode ──────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isExpanded) {
        setIsExpanded(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isExpanded]);

  // Sync expanded state with URL query
  const toggleExpanded = () => {
    setIsExpanded((prev) => {
      const next = !prev;
      if (next) {
        setSearchParams((params) => {
          params.set('expand', 'true');
          return params;
        });
      } else {
        setSearchParams((params) => {
          params.delete('expand');
          return params;
        });
      }
      return next;
    });
  };

  // ── Fetch Drivers when expanded or URL specifies ───────────────────────────
  const loadDriversList = useCallback(async () => {
    setIsLoadingDrivers(true);
    setDriversError(null);
    setErrorMessage(null);
    try {
      const data = await getTrackingDrivers();
      setDrivers(data || []);

      const driverIdParam = searchParams.get('driver_id');
      if (driverIdParam) {
        const found = (data || []).find((d) => String(d.id) === String(driverIdParam));
        if (found) {
          setSelectedDriver(found);
          return;
        }
      }

      if (!selectedDriver && data && data.length > 0) {
        setSelectedDriver(data[0]);
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        const msg = err.message || 'Failed to load fleet drivers.';
        setDriversError(msg);
        setErrorMessage(msg);
      }
    } finally {
      setIsLoadingDrivers(false);
    }
  }, [searchParams, selectedDriver]);

  useEffect(() => {
    if (isExpanded) {
      loadDriversList();
    }
  }, [isExpanded]);

  // ── Load Driver Trips Independently ────────────────────────────────────────
  const loadDriverTripsData = useCallback(async (driverId, targetTripId = null) => {
    if (!driverId) return;

    if (tripsAbortRef.current) {
      tripsAbortRef.current.abort();
    }
    const controller = new AbortController();
    tripsAbortRef.current = controller;
    const signal = controller.signal;
    const currentReqId = ++tripsRequestIdRef.current;

    setIsLoadingTrips(true);
    setTripsError(null);

    try {
      const tripsData = await getDriverTrips(driverId, {}, signal);
      if (signal.aborted || currentReqId !== tripsRequestIdRef.current) return;

      const safeTrips = Array.isArray(tripsData) ? tripsData : [];
      setDriverTrips(safeTrips);

      const tripIdToFind = targetTripId || searchParams.get('trip_id');
      if (tripIdToFind) {
        const found = safeTrips.find(
          (t) => String(t.id) === String(tripIdToFind) || String(t.trip_id) === String(tripIdToFind)
        );
        if (found) {
          setSelectedTrip(found);
        }
      }
    } catch (err) {
      if (err.name === 'AbortError' || signal.aborted) return;
      console.error('Error loading driver trips:', err);
      if (currentReqId === tripsRequestIdRef.current) {
        setTripsError(err.message || 'Failed to retrieve trip history.');
      }
    } finally {
      if (!signal.aborted && currentReqId === tripsRequestIdRef.current) {
        setIsLoadingTrips(false);
      }
    }
  }, [searchParams]);

  // ── Load Driver GPS Telemetry Independently ────────────────────────────────
  const loadDriverTelemetryData = useCallback(async (driverId, trip = null, dateRange = null) => {
    if (!driverId) return;

    if (telemetryAbortRef.current) {
      telemetryAbortRef.current.abort();
    }
    const controller = new AbortController();
    telemetryAbortRef.current = controller;
    const signal = controller.signal;
    const currentReqId = ++telemetryRequestIdRef.current;

    setIsLoadingLocations(true);
    setTelemetryError(null);
    setIsPlaying(false);

    try {
      let locData = null;
      let anData = null;

      if (trip) {
        const tripPoints = await getTripRoute(trip.id || trip.trip_id, signal);
        if (signal.aborted || currentReqId !== telemetryRequestIdRef.current) return;
        locData = { points: tripPoints || [], gaps: [], stops: [], total_points: (tripPoints || []).length };
        try {
          anData = await getDriverAnalytics(driverId, { trip_id: trip.trip_id || trip.id }, signal);
        } catch (e) {
          if (e.name === 'AbortError') return;
          console.warn('Trip analytics unavailable:', e.message);
        }
      } else {
        const params = {
          start_time: dateRange?.startTime ? dateRange.startTime.toISOString() : undefined,
          end_time: dateRange?.endTime ? dateRange.endTime.toISOString() : undefined,
          downsample: 600,
        };
        const [locRes, anRes] = await Promise.all([
          getDriverLocations(driverId, params, signal).catch(e => {
            if (e.name === 'AbortError') throw e;
            console.warn('Historical locations request failed:', e.message);
            return { points: [], gaps: [], stops: [], total_points: 0 };
          }),
          getDriverAnalytics(driverId, params, signal).catch(e => {
            if (e.name === 'AbortError') throw e;
            console.warn('Driver analytics request failed:', e.message);
            return null;
          }),
        ]);
        if (signal.aborted || currentReqId !== telemetryRequestIdRef.current) return;
        locData = locRes;
        anData = anRes;
      }

      if (signal.aborted || currentReqId !== telemetryRequestIdRef.current) return;

      const points = locData?.points || [];
      setLocations(points);
      setGaps(locData?.gaps || []);
      setStops(locData?.stops || []);
      setAnalytics(anData);

      setPlaybackIndex(0);
      setSelectedPoint(points[0] || null);
      setFitTrigger((prev) => prev + 1);
    } catch (err) {
      if (err.name === 'AbortError' || signal.aborted) return;
      console.error('Error loading driver telemetry:', err);
      if (currentReqId === telemetryRequestIdRef.current) {
        setTelemetryError(err.message || 'Failed to retrieve GPS telemetry.');
      }
    } finally {
      if (!signal.aborted && currentReqId === telemetryRequestIdRef.current) {
        setIsLoadingLocations(false);
      }
    }
  }, []);

  // Sync state when driver changes
  useEffect(() => {
    if (isExpanded && selectedDriver?.id) {
      loadDriverTripsData(selectedDriver.id);
      loadDriverTelemetryData(selectedDriver.id, selectedTrip, activeDateRange);
    }
  }, [isExpanded, selectedDriver?.id]);

  // Sync telemetry when active date range changes (only if no specific trip is isolated)
  useEffect(() => {
    if (isExpanded && selectedDriver?.id && !selectedTrip) {
      loadDriverTelemetryData(selectedDriver.id, null, activeDateRange);
    }
  }, [activeDateRange]);

  // ── Driver & Trip Switch Handlers ──────────────────────────────────────────
  const handleSelectDriver = (driver) => {
    if (selectedDriver?.id === driver.id) return;
    setIsPlaying(false);
    setSelectedTrip(null);
    setSelectedPoint(null);
    setLocations([]);
    setGaps([]);
    setStops([]);
    setAnalytics(null);
    setSelectedDriver(driver);
    setSearchParams((params) => {
      params.set('driver_id', driver.id);
      params.delete('trip_id');
      return params;
    });
    loadDriverTripsData(driver.id);
    loadDriverTelemetryData(driver.id, null, activeDateRange);
  };

  const handleSelectTrip = (trip) => {
    setSelectedTrip(trip);
    setSearchParams((params) => {
      params.set('trip_id', trip.trip_id || trip.id);
      return params;
    });
    if (selectedDriver) {
      loadDriverTelemetryData(selectedDriver.id, trip, null);
    }
  };

  const handleClearTrip = () => {
    setSelectedTrip(null);
    setSearchParams((params) => {
      params.delete('trip_id');
      return params;
    });
    if (selectedDriver) {
      loadDriverTelemetryData(selectedDriver.id, null, activeDateRange);
    }
  };

  // ── Split locations by GPS gaps for multi-segment polyline ────────────────
  const segments = useMemo(() => {
    if (!locations || locations.length === 0) return [];
    if (!gaps || gaps.length === 0) return [locations.map(p => [p.latitude, p.longitude])];

    const result = [];
    let currentSegment = [];

    for (let i = 0; i < locations.length; i++) {
      const pt = locations[i];
      if (currentSegment.length > 0) {
        const prevPt = locations[i - 1];
        const prevTime = new Date(prevPt.timestamp).getTime();
        const currTime = new Date(pt.timestamp).getTime();
        if (Math.abs(currTime - prevTime) / 1000 > 900) {
          if (currentSegment.length > 1) result.push(currentSegment);
          currentSegment = [];
        }
      }
      currentSegment.push([pt.latitude, pt.longitude]);
    }
    if (currentSegment.length > 1) result.push(currentSegment);
    return result.length > 0 ? result : [locations.map(p => [p.latitude, p.longitude])];
  }, [locations, gaps]);

  // Route bounding box
  const routeBounds = useMemo(() => {
    if (!locations || locations.length === 0) return null;
    const lats = locations.map(p => p.latitude).filter(l => typeof l === 'number' && !isNaN(l));
    const lngs = locations.map(p => p.longitude).filter(l => typeof l === 'number' && !isNaN(l));
    if (lats.length === 0 || lngs.length === 0) return null;
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    if (minLat === maxLat && minLng === maxLng) {
      return [[minLat - 0.01, minLng - 0.01], [maxLat + 0.01, maxLng + 0.01]];
    }
    return [[minLat, minLng], [maxLat, maxLng]];
  }, [locations]);

  // First & Last Points
  const startPoint = locations && locations.length > 0 ? locations[0] : null;
  const endPoint = locations && locations.length > 1 ? locations[locations.length - 1] : null;

  // ── Playback Loop ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isPlaying || locations.length <= 1) {
      if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
      return;
    }
    if (playbackIndex >= locations.length - 1) {
      setIsPlaying(false);
      return;
    }

    const currentPt = locations[playbackIndex];
    const nextPt = locations[playbackIndex + 1];
    let deltaMs = 500;
    if (currentPt?.timestamp && nextPt?.timestamp) {
      const t1 = new Date(currentPt.timestamp).getTime();
      const t2 = new Date(nextPt.timestamp).getTime();
      const diff = Math.abs(t2 - t1);
      deltaMs = Math.min(1200, Math.max(150, Math.round(diff / (speedMultiplier * 50))));
    }

    playbackTimerRef.current = setTimeout(() => {
      setPlaybackIndex((prev) => {
        const next = prev + 1;
        if (locations[next]) setSelectedPoint(locations[next]);
        return next;
      });
    }, deltaMs);

    return () => {
      if (playbackTimerRef.current) clearTimeout(playbackTimerRef.current);
    };
  }, [isPlaying, playbackIndex, locations, speedMultiplier]);

  const currentPlaybackPoint = locations[playbackIndex] || null;

  const handleCopyCoords = (lat, lng) => {
    navigator.clipboard?.writeText(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    setCopiedCoords(true);
    setTimeout(() => setCopiedCoords(false), 2000);
  };

  return (
    <div 
      className={cn(
        "transition-all duration-300 select-none bg-white",
        isExpanded
          ? "fixed inset-0 z-50 flex flex-col w-screen h-screen overflow-hidden"
          : "w-full h-full min-h-[400px] rounded-2xl overflow-hidden border border-border shadow-card relative z-0 flex flex-col"
      )}
    >
      {/* ── EXPANDED MODE: Top Toolbar ─────────────────────────────────────── */}
      {isExpanded && (
        <header className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-white border-b border-slate-200 z-20 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-brand-50 text-brand-600 border border-brand-200">
                <Navigation className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-slate-800 leading-tight">
                  Fleet GPS Tracking & Trip History
                </h1>
                <p className="text-[11px] text-slate-500">
                  The Vahan Geospatial Fleet Intelligence
                </p>
              </div>
            </div>

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

          {/* Right Toolbar Actions */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={loadHistoricalTelemetry}
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

            {/* Collapse Button */}
            <button
              type="button"
              onClick={toggleExpanded}
              title="Collapse to Dashboard (Esc)"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 border border-slate-200 rounded-lg hover:bg-slate-200 hover:text-slate-900 transition-colors shadow-xs ml-1"
            >
              <Minimize2 className="w-4 h-4 text-slate-600" />
              <span>Collapse</span>
            </button>
          </div>
        </header>
      )}

      {/* ── EXPANDED MODE: Time Filter Bar ─────────────────────────────────── */}
      {isExpanded && (
        <div className="shrink-0 bg-white border-b border-slate-200">
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
      )}

      {/* ── EXPANDED MODE: Error Banner ────────────────────────────────────── */}
      {isExpanded && errorMessage && (
        <div className="px-4 py-2 bg-rose-50 border-b border-rose-200 text-rose-700 text-xs flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-500 hover:text-rose-800 font-semibold">
            Dismiss
          </button>
        </div>
      )}

      {/* ── Body Container ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden relative w-full h-full">
        {/* Left Sidebar (Only in Expanded Mode) */}
        {isExpanded && (
          <aside
            className={cn(
              "h-full bg-white border-r border-slate-200 flex flex-col transition-all duration-200 z-10 shrink-0",
              sidebarCollapsed ? "w-0 overflow-hidden border-none" : "w-80 sm:w-96"
            )}
          >
            {/* Driver list */}
            <div className="h-[55%] flex flex-col min-h-0 border-b border-slate-200">
              <DriverSidebar
                drivers={drivers}
                selectedDriver={selectedDriver}
                onSelectDriver={handleSelectDriver}
                loading={isLoadingDrivers}
                error={driversError}
                onRetry={loadDriversList}
                searchTerm={driverSearchTerm}
                onSearchChange={setDriverSearchTerm}
                dutyStatusFilter={driverDutyStatus}
                onDutyStatusChange={setDriverDutyStatus}
                sortBy={driverSortBy}
                onSortByChange={setDriverSortBy}
                hasTripsFilter={driverHasTripsFilter}
                onHasTripsFilterToggle={setDriverHasTripsFilter}
              />
            </div>

            {/* Historical Trips list */}
            <div className="h-[45%] flex flex-col min-h-0">
              <DriverTripsList
                trips={driverTrips}
                selectedTrip={selectedTrip}
                onSelectTrip={handleSelectTrip}
                onClearTrip={handleClearTrip}
                isLoading={isLoadingTrips}
                error={tripsError}
                onRetry={loadHistoricalTelemetry}
                driverName={selectedDriver?.name}
              />
            </div>
          </aside>
        )}

        {/* Sidebar Toggle Chevron (Only in Expanded Mode) */}
        {isExpanded && (
          <button
            type="button"
            onClick={() => setSidebarCollapsed(prev => !prev)}
            title={sidebarCollapsed ? "Expand Driver Panel" : "Collapse Driver Panel"}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white border border-slate-300 text-slate-600 p-1 rounded-r-lg shadow-md hover:text-brand-600 transition-colors"
            style={{ left: sidebarCollapsed ? '0px' : undefined }}
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        )}

        {/* ── Main Map Area (Same MapContainer) ──────────────────────────────── */}
        <main className="flex-1 h-full relative overflow-hidden flex flex-col">
          <MapContainer 
            center={defaultCenter} 
            zoom={11} 
            style={{ height: '100%', width: '100%', zIndex: 0 }}
            zoomControl={false}
          >
            {/* OpenStreetMap Keyless Tile Layer with standard attribution */}
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              maxZoom={19}
            />

            {/* Resize invalidator */}
            <MapInvalidator isExpanded={isExpanded} sidebarCollapsed={sidebarCollapsed} />

            {/* Bounds Controller */}
            <MapBoundsController 
              trucks={trucks} 
              routeBounds={isExpanded ? routeBounds : null} 
              fitTrigger={fitTrigger} 
            />

            {/* Follow Playback Marker */}
            {isExpanded && (
              <MapFollower currentPoint={currentPlaybackPoint} isPlaying={isPlaying} />
            )}

            {/* NORMAL MODE: Live Fleet Markers */}
            {!isExpanded && trucks.map(truck => (
              <Marker 
                key={truck.id} 
                position={[truck.lat, truck.lng]} 
                icon={createTruckIcon(truck, selectedDriver?.id === truck.id)}
                eventHandlers={{
                  click: () => {
                    const matchDriver = drivers.find(d => String(d.id) === String(truck.id));
                    if (matchDriver) setSelectedDriver(matchDriver);
                  },
                }}
              >
                <Tooltip direction="top" offset={[0, -15]} opacity={1} className="custom-leaflet-tooltip">
                  <div className="text-center px-1">
                    <p className="text-xs font-semibold text-slate-800 m-0">{truck.driver_name || truck.id}</p>
                    {truck.speed > 0 && <p className="text-[10px] text-slate-500 m-0">{truck.speed} km/h</p>}
                    <p className="text-[10px] text-brand-600 font-medium m-0 mt-0.5">Click Expand for GPS History</p>
                  </div>
                </Tooltip>
              </Marker>
            ))}

            {/* EXPANDED MODE: Multi-segment Polylines (broken across GPS gaps) */}
            {isExpanded && segments.map((seg, idx) => (
              <Polyline 
                key={`route-seg-${idx}`}
                positions={seg}
                color="#2563EB"
                weight={5}
                opacity={0.85}
                lineCap="round"
                lineJoin="round"
              />
            ))}

            {/* EXPANDED MODE: Gap dashed indicators */}
            {isExpanded && gaps.map((gap, idx) => {
              if (gap.start_point?.latitude && gap.end_point?.latitude) {
                return (
                  <Polyline
                    key={`gap-line-${idx}`}
                    positions={[
                      [gap.start_point.latitude, gap.start_point.longitude],
                      [gap.end_point.latitude, gap.end_point.longitude],
                    ]}
                    color="#EF4444"
                    dashArray="6, 8"
                    weight={2}
                    opacity={0.65}
                  />
                );
              }
              return null;
            })}

            {/* EXPANDED MODE: Start Marker */}
            {isExpanded && startPoint && (
              <Marker
                position={[startPoint.latitude, startPoint.longitude]}
                icon={createStartIcon()}
                eventHandlers={{ click: () => setSelectedPoint(startPoint) }}
              >
                <Popup className="custom-vahan-popup">
                  <div className="p-1 space-y-1">
                    <div className="flex items-center gap-1.5 text-emerald-700 font-bold text-xs">
                      <Play className="w-3.5 h-3.5 fill-emerald-600" />
                      <span>Trip Origin / First Ping</span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      {formatDateTime(startPoint.timestamp, 'dd MMM yyyy, HH:mm:ss')}
                    </p>
                    <div className="text-[10px] text-slate-600 font-mono">
                      {startPoint.latitude.toFixed(6)}, {startPoint.longitude.toFixed(6)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* EXPANDED MODE: End Marker */}
            {isExpanded && endPoint && (
              <Marker
                position={[endPoint.latitude, endPoint.longitude]}
                icon={createEndIcon()}
                eventHandlers={{ click: () => setSelectedPoint(endPoint) }}
              >
                <Popup className="custom-vahan-popup">
                  <div className="p-1 space-y-1">
                    <div className="flex items-center gap-1.5 text-rose-700 font-bold text-xs">
                      <Square className="w-3 h-3 fill-rose-600" />
                      <span>Trip Destination / Latest Ping</span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      {formatDateTime(endPoint.timestamp, 'dd MMM yyyy, HH:mm:ss')}
                    </p>
                    <div className="text-[10px] text-slate-600 font-mono">
                      {endPoint.latitude.toFixed(6)}, {endPoint.longitude.toFixed(6)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* EXPANDED MODE: Stops Markers */}
            {isExpanded && stops.map((stop, idx) => (
              <Marker
                key={`stop-${idx}`}
                position={[stop.latitude, stop.longitude]}
                icon={createStopIcon()}
                eventHandlers={{ click: () => setSelectedPoint(stop) }}
              >
                <Popup className="custom-vahan-popup">
                  <div className="p-1 space-y-1">
                    <div className="flex items-center gap-1.5 text-amber-700 font-bold text-xs">
                      <Coffee className="w-3.5 h-3.5" />
                      <span>Stationary Stop ({formatDurationMinutes(stop.duration_minutes)})</span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      {formatDateTime(stop.start_time, 'HH:mm')} – {formatDateTime(stop.end_time, 'HH:mm')}
                    </p>
                  </div>
                </Popup>
              </Marker>
            ))}

            {/* EXPANDED MODE: Gap Markers */}
            {isExpanded && gaps.map((gap, idx) => {
              if (gap.start_point?.latitude) {
                return (
                  <Marker
                    key={`gap-m-${idx}`}
                    position={[gap.start_point.latitude, gap.start_point.longitude]}
                    icon={createGapIcon()}
                  >
                    <Popup className="custom-vahan-popup">
                      <div className="p-1 space-y-1">
                        <div className="flex items-center gap-1.5 text-rose-600 font-bold text-xs">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>GPS Signal Lost ({formatDurationMinutes(gap.duration_minutes)})</span>
                        </div>
                        <p className="text-[11px] text-slate-500">
                          Telemetry unavailable between points. No movement recorded.
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                );
              }
              return null;
            })}

            {/* EXPANDED MODE: Raw Point Dots */}
            {isExpanded && showAllPointDots && locations.map((pt, i) => (
              <CircleMarker
                key={`dot-${i}`}
                center={[pt.latitude, pt.longitude]}
                radius={3}
                color="#3B82F6"
                fillColor="#ffffff"
                fillOpacity={0.9}
                weight={1.5}
                eventHandlers={{ click: () => setSelectedPoint(pt) }}
              />
            ))}

            {/* EXPANDED MODE: Playback Marker */}
            {isExpanded && currentPlaybackPoint?.latitude && currentPlaybackPoint?.longitude && (
              <Marker
                position={[currentPlaybackPoint.latitude, currentPlaybackPoint.longitude]}
                icon={createPlaybackVehicleIcon(currentPlaybackPoint.heading || 0)}
                zIndexOffset={1000}
              />
            )}
          </MapContainer>

          {/* ── Top-Right Map Controls ───────────────────────────────────────── */}
          <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
            {/* Refresh Button */}
            <button
              onClick={isExpanded ? loadHistoricalTelemetry : onRefresh}
              disabled={isRefreshing || (isExpanded && (isLoadingLocations || isLoadingTrips))}
              className="p-2.5 bg-white/95 backdrop-blur-xs border border-slate-200 rounded-xl shadow-md text-slate-600 hover:text-brand-600 hover:border-brand-300 transition-all focus:outline-none disabled:opacity-50"
              title="Refresh Telemetry"
            >
              <RefreshCw className={cn("w-4 h-4", (isRefreshing || (isExpanded && isLoadingLocations)) && "animate-spin")} />
            </button>

            {/* Expand / Collapse Button */}
            <button
              onClick={toggleExpanded}
              className={cn(
                "flex items-center gap-1.5 py-2.5 px-3 bg-white/95 backdrop-blur-xs border rounded-xl shadow-md transition-all focus:outline-none text-xs font-semibold",
                isExpanded 
                  ? "border-slate-300 text-slate-700 hover:bg-slate-50"
                  : "border-brand-300 text-brand-700 bg-brand-50/80 hover:bg-brand-100/80"
              )}
              title={isExpanded ? "Collapse to Dashboard (Esc)" : "Expand GPS Trip History Workspace"}
            >
              {isExpanded ? (
                <>
                  <Minimize2 className="w-4 h-4 text-slate-600" />
                  <span className="hidden sm:inline">Collapse</span>
                </>
              ) : (
                <>
                  <Maximize2 className="w-4 h-4 text-brand-600" />
                  <span>Expand History</span>
                </>
              )}
            </button>

            {/* Additional controls in Expanded mode */}
            {isExpanded && (
              <>
                <button
                  type="button"
                  onClick={() => setFitTrigger(prev => prev + 1)}
                  title="Fit Route to Screen"
                  className="p-2.5 bg-white/95 backdrop-blur-xs border border-slate-200 rounded-xl shadow-md text-slate-600 hover:text-brand-600 transition-colors"
                >
                  <LocateFixed className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setShowAllPointDots(prev => !prev)}
                  title={showAllPointDots ? "Hide Individual GPS Points" : "Show All GPS Points"}
                  className={cn(
                    "p-2.5 rounded-xl shadow-md transition-colors border",
                    showAllPointDots 
                      ? "bg-brand-50 border-brand-300 text-brand-700" 
                      : "bg-white/95 backdrop-blur-xs border-slate-200 text-slate-600 hover:text-brand-600"
                  )}
                >
                  <Layers className="w-4 h-4" />
                </button>
              </>
            )}
          </div>

          {/* ── EXPANDED MODE: Legend Bottom-Left ───────────────────────────── */}
          {isExpanded && (
            <div className="absolute bottom-4 left-4 z-10 bg-white/95 backdrop-blur-xs px-3 py-2 rounded-xl border border-slate-200 shadow-md text-[11px] text-slate-600 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block" />
                <span className="font-medium">Origin</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-600 inline-block" />
                <span className="font-medium">Destination</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
                <span className="font-medium">Stop (&ge;5m)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 border-t-2 border-dashed border-rose-500 inline-block" />
                <span className="font-medium">GPS Gap</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-1 bg-blue-600 rounded-sm inline-block" />
                <span className="font-medium">Route</span>
              </div>
            </div>
          )}

          {/* ── EXPANDED MODE: Inspected Point Popover ──────────────────────── */}
          {isExpanded && selectedPoint && (
            <div className="absolute top-4 left-4 z-10 max-w-sm bg-white/95 backdrop-blur-xs p-3 rounded-xl border border-slate-200 shadow-xl text-xs space-y-2 animate-fade-in">
              <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-1.5">
                <div className="flex items-center gap-1.5 font-bold text-slate-800">
                  <Navigation className="w-3.5 h-3.5 text-brand-600" />
                  <span>GPS Telemetry Point</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">
                  {formatDateTime(selectedPoint.timestamp, 'HH:mm:ss')}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-semibold">Speed</span>
                  <span className="font-bold text-slate-800">
                    {typeof selectedPoint.speed_kmh === 'number'
                      ? `${selectedPoint.speed_kmh.toFixed(1)} km/h`
                      : typeof selectedPoint.speed === 'number'
                      ? `${(selectedPoint.speed * 3.6).toFixed(1)} km/h`
                      : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-semibold">Heading</span>
                  <span className="font-bold text-slate-800">
                    {typeof selectedPoint.heading === 'number' ? `${Math.round(selectedPoint.heading)}°` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-semibold">Accuracy</span>
                  <span className="font-bold text-slate-800">
                    {typeof selectedPoint.accuracy === 'number' ? `±${selectedPoint.accuracy.toFixed(1)}m` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px] uppercase font-semibold">Recorded</span>
                  <span className="font-medium text-slate-700">
                    {formatDateTime(selectedPoint.timestamp, 'dd MMM, HH:mm')}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1.5 border-t border-slate-100 gap-2">
                <span className="font-mono text-[10px] text-slate-500 truncate">
                  {selectedPoint.latitude.toFixed(5)}, {selectedPoint.longitude.toFixed(5)}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleCopyCoords(selectedPoint.latitude, selectedPoint.longitude)}
                    className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-600 hover:text-brand-600 px-1.5 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition-colors"
                  >
                    {copiedCoords ? <Check className="w-2.5 h-2.5 text-emerald-600" /> : <Copy className="w-2.5 h-2.5" />}
                    <span>{copiedCoords ? 'Copied' : 'Copy'}</span>
                  </button>
                  <a
                    href={`https://www.google.com/maps?q=${selectedPoint.latitude},${selectedPoint.longitude}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-600 hover:text-brand-600 px-1.5 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition-colors"
                  >
                    <ExternalLink className="w-2.5 h-2.5" />
                    <span>Maps</span>
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* ── EXPANDED MODE: GPS Telemetry Unavailable Notice ────────────── */}
          {isExpanded && locations.length === 0 && !isLoadingLocations && selectedDriver && !driversError && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 z-20 max-w-md bg-white/95 backdrop-blur-md px-4 py-3 rounded-xl border border-slate-200 shadow-xl text-center space-y-1.5 animate-fade-in pointer-events-auto">
              <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-slate-800">
                <Navigation className="w-4 h-4 text-slate-400" />
                <span>GPS Telemetry Unavailable</span>
              </div>
              <p className="text-[11px] text-slate-500">
                No historical GPS breadcrumbs recorded for {selectedDriver.name || 'this driver'} during the selected window.
              </p>
              <div className="flex items-center justify-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setTimePreset('30d');
                    setActiveDateRange(getTimeFilterRange('30d'));
                  }}
                  className="text-[11px] font-semibold text-brand-600 hover:text-brand-800 underline"
                >
                  Expand to Last 30 Days
                </button>
                {selectedTrip && (
                  <>
                    <span className="text-slate-300">•</span>
                    <button
                      type="button"
                      onClick={handleClearTrip}
                      className="text-[11px] font-semibold text-brand-600 hover:text-brand-800 underline"
                    >
                      Clear Trip Filter
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* ── EXPANDED MODE: Floating Playback Dock ──────────────────────── */}
          {isExpanded && locations.length > 0 && (
            <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-20 w-[95%] max-w-2xl pointer-events-auto">
              <PlaybackControls
                points={locations}
                currentIndex={playbackIndex}
                isPlaying={isPlaying}
                speedMultiplier={speedMultiplier}
                onPlayPause={() => {
                  if (playbackIndex >= locations.length - 1) setPlaybackIndex(0);
                  setIsPlaying(prev => !prev);
                }}
                onSeek={(idx) => {
                  setPlaybackIndex(idx);
                  if (locations[idx]) setSelectedPoint(locations[idx]);
                }}
                onRestart={() => {
                  setPlaybackIndex(0);
                  if (locations[0]) setSelectedPoint(locations[0]);
                }}
                onSpeedChange={setSpeedMultiplier}
                onStepBack={() => {
                  setPlaybackIndex(prev => {
                    const next = Math.max(0, prev - 1);
                    if (locations[next]) setSelectedPoint(locations[next]);
                    return next;
                  });
                }}
                onStepForward={() => {
                  setPlaybackIndex(prev => {
                    const next = Math.min(locations.length - 1, prev + 1);
                    if (locations[next]) setSelectedPoint(locations[next]);
                    return next;
                  });
                }}
                onJumpStart={() => {
                  setPlaybackIndex(0);
                  if (locations[0]) setSelectedPoint(locations[0]);
                }}
                onJumpEnd={() => {
                  const last = locations.length - 1;
                  setPlaybackIndex(last);
                  if (locations[last]) setSelectedPoint(locations[last]);
                }}
              />
            </div>
          )}
        </main>

        {/* ── EXPANDED MODE: Right Analytics Drawer ─────────────────────────── */}
        {isExpanded && (
          <TripAnalyticsDrawer
            isOpen={analyticsDrawerOpen}
            onClose={() => setAnalyticsDrawerOpen(false)}
            analytics={analytics}
            locations={locations}
            selectedPoint={selectedPoint}
            onSelectPoint={(pt) => {
              setSelectedPoint(pt);
              const idx = locations.findIndex(p => p.id === pt.id);
              if (idx >= 0) setPlaybackIndex(idx);
            }}
            driverName={selectedDriver?.name}
            vehiclePlate={selectedDriver?.vehicle_plate}
            activeTrip={selectedTrip}
          />
        )}
      </div>

      <style>{`
        .custom-leaflet-icon {
          background: transparent;
          border: none;
        }
        .custom-leaflet-tooltip {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(8px);
          border: 1px solid #E2E8F0;
          border-radius: 8px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          color: #1E293B;
          padding: 6px 10px;
        }
        .custom-vahan-popup .leaflet-popup-content-wrapper {
          border-radius: 8px;
          box-shadow: 0 4px 14px rgba(0,0,0,0.1);
          border: 1px solid #E2E8F0;
          padding: 2px 4px;
        }
        .custom-vahan-popup .leaflet-popup-content {
          margin: 6px 8px;
          line-height: 1.4;
        }
      `}</style>
    </div>
  );
}
