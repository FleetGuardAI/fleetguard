import React, { useMemo, useEffect, useRef, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { renderToStaticMarkup } from 'react-dom/server';
import { 
  Play, 
  Square, 
  MapPin, 
  Navigation, 
  AlertTriangle, 
  Clock, 
  Maximize2, 
  Minimize2, 
  LocateFixed, 
  Layers, 
  ExternalLink, 
  Copy, 
  Check, 
  Gauge, 
  Compass,
  Coffee
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatDateTime, formatDurationMinutes } from '@/utils/dateTime';

// ── Auto-adjust map bounds when dataset changes ──────────────────────────────
function MapBoundsController({ bounds, shouldFitTrigger }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length >= 2) {
      try {
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 });
      } catch (err) {
        // Safe fallback
      }
    }
  }, [map, bounds, shouldFitTrigger]);
  return null;
}

// ── Follow playback vehicle if enabled ───────────────────────────────────────
function MapFollower({ currentPoint, isPlaying }) {
  const map = useMap();
  useEffect(() => {
    if (isPlaying && currentPoint?.latitude && currentPoint?.longitude) {
      const center = map.getCenter();
      const bounds = map.getBounds();
      const pointLatLng = L.latLng(currentPoint.latitude, currentPoint.longitude);
      
      // Only pan map if point is getting close to the boundary (edge threshold)
      if (!bounds.pad(-0.15).contains(pointLatLng)) {
        map.panTo(pointLatLng, { animate: true, duration: 0.5 });
      }
    }
  }, [map, currentPoint, isPlaying]);
  return null;
}

// ── Custom Leaflet Icons ────────────────────────────────────────────────────
const createStartIcon = () => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-emerald-600 text-white shadow-lg border-2 border-white ring-2 ring-emerald-500/40">
      <Play className="w-4 h-4 fill-white ml-0.5" />
    </div>
  );
  return L.divIcon({
    html,
    className: 'custom-map-icon',
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
    className: 'custom-map-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
};

const createStopIcon = (durationMinutes = null) => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center w-7 h-7 rounded-full bg-amber-500 text-white shadow-md border-2 border-white ring-1 ring-amber-400">
      <Coffee className="w-3.5 h-3.5" />
    </div>
  );
  return L.divIcon({
    html,
    className: 'custom-map-icon',
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
    className: 'custom-map-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
};

const createPlaybackVehicleIcon = (heading = 0, speedKmh = 0) => {
  const html = renderToStaticMarkup(
    <div className="relative flex items-center justify-center" style={{ width: '40px', height: '40px' }}>
      {/* Outer Pulse */}
      <div className="absolute inset-0 rounded-full bg-emerald-500/30 animate-ping" />
      {/* Halo */}
      <div className="absolute inset-1 rounded-full bg-emerald-500/20 blur-xs" />
      {/* Main Vehicle Marker */}
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
    className: 'custom-map-icon vehicle-playback-icon',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -22],
  });
};

export function TripTrackingMap({
  locations = [],
  gaps = [],
  stops = [],
  currentPlaybackPoint = null,
  isPlaying = false,
  selectedPoint = null,
  onSelectPoint,
  isLoading = false,
  driverName = '',
  vehiclePlate = '',
  fitBoundsTrigger = 0,
  onTriggerFitBounds
}) {
  const mapContainerRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showAllPointDots, setShowAllPointDots] = useState(false);
  const [copiedCoords, setCopiedCoords] = useState(false);

  // Toggle fullscreen mode
  const toggleFullscreen = () => {
    if (!mapContainerRef.current) return;
    if (!document.fullscreenElement) {
      mapContainerRef.current.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  // Split locations into continuous segments separated by detected GPS gaps
  const segments = useMemo(() => {
    if (!locations || locations.length === 0) return [];

    if (!gaps || gaps.length === 0) {
      return [locations.map((pt) => [pt.latitude, pt.longitude])];
    }

    // Gaps specify start_point and end_point coordinates or timestamps
    // We break locations into segments whenever distance in time >= 900s
    const result = [];
    let currentSegment = [];

    for (let i = 0; i < locations.length; i++) {
      const pt = locations[i];
      if (currentSegment.length > 0) {
        const prevPt = locations[i - 1];
        const prevTime = new Date(prevPt.timestamp).getTime();
        const currTime = new Date(pt.timestamp).getTime();
        const diffSeconds = Math.abs(currTime - prevTime) / 1000;

        if (diffSeconds > 900) {
          // Break segment across this gap
          if (currentSegment.length > 1) {
            result.push(currentSegment);
          }
          currentSegment = [];
        }
      }
      currentSegment.push([pt.latitude, pt.longitude]);
    }

    if (currentSegment.length > 1) {
      result.push(currentSegment);
    } else if (result.length === 0 && locations.length > 0) {
      result.push(locations.map((pt) => [pt.latitude, pt.longitude]));
    }

    return result;
  }, [locations, gaps]);

  // Compute overall bounds
  const bounds = useMemo(() => {
    if (!locations || locations.length === 0) return null;
    const lats = locations.map((p) => p.latitude).filter((lat) => typeof lat === 'number' && !isNaN(lat));
    const lngs = locations.map((p) => p.longitude).filter((lng) => typeof lng === 'number' && !isNaN(lng));
    if (lats.length === 0 || lngs.length === 0) return null;

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    if (minLat === maxLat && minLng === maxLng) {
      // Single point bounding box
      return [
        [minLat - 0.01, minLng - 0.01],
        [maxLat + 0.01, maxLng + 0.01],
      ];
    }

    return [
      [minLat, minLng],
      [maxLat, maxLng],
    ];
  }, [locations]);

  const defaultCenter = useMemo(() => {
    if (locations && locations.length > 0) {
      return [locations[0].latitude, locations[0].longitude];
    }
    return [30.3165, 78.0322]; // Default: Dehradun / India region
  }, [locations]);

  // First & last points for Start/End markers
  const startPoint = locations && locations.length > 0 ? locations[0] : null;
  const endPoint = locations && locations.length > 1 ? locations[locations.length - 1] : null;

  // Active point for popup (either manually selected or playback)
  const activeInspectPoint = selectedPoint || currentPlaybackPoint;

  const handleCopyCoords = useCallback((lat, lng) => {
    const text = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    navigator.clipboard?.writeText(text);
    setCopiedCoords(true);
    setTimeout(() => setCopiedCoords(false), 2000);
  }, []);

  return (
    <div 
      ref={mapContainerRef} 
      className={cn(
        "relative w-full h-full bg-slate-100 overflow-hidden select-none",
        isFullscreen && "fixed inset-0 z-50"
      )}
    >
      {/* Main Map Container */}
      <MapContainer
        center={defaultCenter}
        zoom={13}
        style={{ width: '100%', height: '100%', zIndex: 0 }}
        zoomControl={false}
      >
        {/* Carto Positron clean map tiles with standard OSM fallback */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          maxZoom={19}
        />

        {/* Bound Controller */}
        {bounds && <MapBoundsController bounds={bounds} shouldFitTrigger={fitBoundsTrigger} />}

        {/* Follow Vehicle during playback */}
        <MapFollower currentPoint={currentPlaybackPoint} isPlaying={isPlaying} />

        {/* Route Polylines (split by gaps) */}
        {segments.map((seg, idx) => (
          <Polyline
            key={`route-seg-${idx}`}
            positions={seg}
            color="#2563EB" // blue-600
            weight={5}
            opacity={0.85}
            lineCap="round"
            lineJoin="round"
          />
        ))}

        {/* Gaps: dashed connectors indicating missing telemetry */}
        {gaps.map((gap, idx) => {
          if (gap.start_point?.latitude && gap.end_point?.latitude) {
            return (
              <Polyline
                key={`gap-line-${idx}`}
                positions={[
                  [gap.start_point.latitude, gap.start_point.longitude],
                  [gap.end_point.latitude, gap.end_point.longitude],
                ]}
                color="#EF4444" // red-500
                dashArray="6, 8"
                weight={2}
                opacity={0.65}
              />
            );
          }
          return null;
        })}

        {/* Start Marker */}
        {startPoint && (
          <Marker
            position={[startPoint.latitude, startPoint.longitude]}
            icon={createStartIcon()}
            eventHandlers={{
              click: () => onSelectPoint && onSelectPoint(startPoint),
            }}
          >
            <Popup className="custom-vahan-popup">
              <div className="p-1 space-y-1">
                <div className="flex items-center gap-1.5 text-emerald-700 font-bold text-xs">
                  <Play className="w-3.5 h-3.5 fill-emerald-600" />
                  <span>Trip Origin / First GPS Ping</span>
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

        {/* End Marker */}
        {endPoint && (
          <Marker
            position={[endPoint.latitude, endPoint.longitude]}
            icon={createEndIcon()}
            eventHandlers={{
              click: () => onSelectPoint && onSelectPoint(endPoint),
            }}
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

        {/* Stop Markers */}
        {stops.map((stop, idx) => (
          <Marker
            key={`stop-${idx}`}
            position={[stop.latitude, stop.longitude]}
            icon={createStopIcon(stop.duration_minutes)}
            eventHandlers={{
              click: () => onSelectPoint && onSelectPoint(stop),
            }}
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
                <div className="text-[10px] text-slate-600 font-mono">
                  {stop.latitude.toFixed(6)}, {stop.longitude.toFixed(6)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Gap Markers (Signal Lost Indicators) */}
        {gaps.map((gap, idx) => {
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

        {/* Optional raw GPS point dots (when zoomed or toggled) */}
        {showAllPointDots &&
          locations.map((pt, i) => (
            <CircleMarker
              key={`dot-${i}`}
              center={[pt.latitude, pt.longitude]}
              radius={3}
              color="#3B82F6"
              fillColor="#ffffff"
              fillOpacity={0.9}
              weight={1.5}
              eventHandlers={{
                click: () => onSelectPoint && onSelectPoint(pt),
              }}
            />
          ))}

        {/* Animated Playback Vehicle Marker */}
        {currentPlaybackPoint && currentPlaybackPoint.latitude && currentPlaybackPoint.longitude && (
          <Marker
            position={[currentPlaybackPoint.latitude, currentPlaybackPoint.longitude]}
            icon={createPlaybackVehicleIcon(currentPlaybackPoint.heading, currentPlaybackPoint.speed_kmh)}
            zIndexOffset={1000}
          />
        )}
      </MapContainer>

      {/* ── Floating Map Controls Top-Right ───────────────────────────────── */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1.5 bg-white/95 backdrop-blur-xs p-1 rounded-lg border border-slate-200 shadow-md">
        <button
          type="button"
          onClick={onTriggerFitBounds}
          title="Fit Route to Screen"
          className="p-2 text-slate-700 hover:text-brand-600 hover:bg-slate-50 rounded-md transition-colors"
        >
          <LocateFixed className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={() => setShowAllPointDots((prev) => !prev)}
          title={showAllPointDots ? "Hide Individual GPS Points" : "Show All GPS Points"}
          className={cn(
            "p-2 rounded-md transition-colors",
            showAllPointDots ? "bg-brand-50 text-brand-600" : "text-slate-700 hover:text-brand-600 hover:bg-slate-50"
          )}
        >
          <Layers className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Map"}
          className="p-2 text-slate-700 hover:text-brand-600 hover:bg-slate-50 rounded-md transition-colors"
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* ── Map Legend Bottom-Left ────────────────────────────────────────── */}
      <div className="absolute bottom-3 left-3 z-10 bg-white/95 backdrop-blur-xs px-3 py-2 rounded-lg border border-slate-200 shadow-md text-[11px] text-slate-600 flex flex-wrap items-center gap-3">
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
          <span className="font-medium">Tracked Path</span>
        </div>
      </div>

      {/* ── Selected Point Inspector Overlay (Top-Left) ───────────────────── */}
      {activeInspectPoint && (
        <div className="absolute top-3 left-3 z-10 max-w-sm bg-white/95 backdrop-blur-xs p-3 rounded-lg border border-slate-200 shadow-lg text-xs space-y-2 animate-in fade-in duration-150">
          <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-1.5">
            <div className="flex items-center gap-1.5 font-bold text-slate-800">
              <Navigation className="w-3.5 h-3.5 text-brand-600" />
              <span>GPS Telemetry Point</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              {formatDateTime(activeInspectPoint.timestamp, 'HH:mm:ss')}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-semibold">Speed</span>
              <span className="font-bold text-slate-800">
                {typeof activeInspectPoint.speed_kmh === 'number'
                  ? `${activeInspectPoint.speed_kmh.toFixed(1)} km/h`
                  : typeof activeInspectPoint.speed === 'number'
                  ? `${(activeInspectPoint.speed * 3.6).toFixed(1)} km/h`
                  : 'N/A'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-semibold">Heading / Bearing</span>
              <span className="font-bold text-slate-800">
                {typeof activeInspectPoint.heading === 'number' ? `${Math.round(activeInspectPoint.heading)}°` : 'N/A'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-semibold">Accuracy</span>
              <span className="font-bold text-slate-800">
                {typeof activeInspectPoint.accuracy === 'number' ? `±${activeInspectPoint.accuracy.toFixed(1)}m` : 'N/A'}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-semibold">Recorded Time</span>
              <span className="font-medium text-slate-700">
                {formatDateTime(activeInspectPoint.timestamp, 'dd MMM, HH:mm')}
              </span>
            </div>
          </div>

          {/* Coordinates and Actions */}
          <div className="flex items-center justify-between pt-1.5 border-t border-slate-100 gap-2">
            <span className="font-mono text-[10px] text-slate-500 truncate">
              {activeInspectPoint.latitude.toFixed(5)}, {activeInspectPoint.longitude.toFixed(5)}
            </span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => handleCopyCoords(activeInspectPoint.latitude, activeInspectPoint.longitude)}
                className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-600 hover:text-brand-600 px-1.5 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition-colors"
                title="Copy coordinates"
              >
                {copiedCoords ? <Check className="w-2.5 h-2.5 text-emerald-600" /> : <Copy className="w-2.5 h-2.5" />}
                <span>{copiedCoords ? 'Copied' : 'Copy'}</span>
              </button>
              <a
                href={`https://www.google.com/maps?q=${activeInspectPoint.latitude},${activeInspectPoint.longitude}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-600 hover:text-brand-600 px-1.5 py-0.5 rounded bg-slate-100 hover:bg-slate-200 transition-colors"
                title="Open in Google Maps"
              >
                <ExternalLink className="w-2.5 h-2.5" />
                <span>Maps</span>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* ── Empty State / Loading Overlay ─────────────────────────────────── */}
      {isLoading && (
        <div className="absolute inset-0 z-20 bg-white/70 backdrop-blur-xs flex items-center justify-center">
          <div className="flex flex-col items-center gap-2 p-4 rounded-xl bg-white shadow-xl border border-slate-200">
            <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs font-semibold text-slate-700">Loading GPS Telemetry...</p>
          </div>
        </div>
      )}

      {!isLoading && locations.length === 0 && (
        <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
          <div className="max-w-md p-6 bg-white/90 backdrop-blur-sm rounded-xl border border-slate-200 shadow-xl text-center pointer-events-auto">
            <MapPin className="w-10 h-10 text-slate-300 mx-auto mb-2 stroke-1" />
            <h4 className="text-sm font-bold text-slate-700">No GPS Points in Selected Window</h4>
            <p className="text-xs text-slate-500 mt-1">
              No historical location records were found for {driverName || 'this driver'} within the active time filter.
            </p>
            <p className="text-[11px] text-slate-400 mt-2">
              Try choosing a broader preset (such as "Last 7 Days" or "Last 30 Days") or check if the driver was on an assigned trip.
            </p>
          </div>
        </div>
      )}

      {/* Custom popup styles */}
      <style>{`
        .custom-map-icon {
          background: transparent;
          border: none;
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
