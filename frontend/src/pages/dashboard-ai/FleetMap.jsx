import React, { useMemo, useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Tooltip, useMap, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { renderToStaticMarkup } from 'react-dom/server';
import { Navigation, Clock, Route as RouteIcon, X } from 'lucide-react';
import { cn } from '@/utils/cn';
import { getDriverHistory, getTripRoute } from '@/api/telematicsApi';

// Leaflet setup for custom HTML markers
const createCustomIcon = (truck, isSelected) => {
  const isIdle = truck.status === 'idle';
  const iconHtml = renderToStaticMarkup(
    <div className="group relative cursor-pointer" style={{ width: '28px', height: '28px' }}>
      <div className={cn(
        "absolute -inset-2 rounded-full blur-md opacity-0 transition-opacity custom-hover-effect",
        isSelected ? "bg-brand-500/40 opacity-100 animate-pulse" : "bg-brand-500/15"
      )} />
      <div className={cn(
        "relative flex items-center justify-center w-full h-full rounded-full shadow-lg border transition-all",
        isIdle && !isSelected ? "bg-white border-border" : "bg-brand-500 border-brand-400 text-white",
        isSelected && "scale-110 shadow-brand-500/30"
      )}>
        <Navigation className={cn(
          "w-4 h-4 transition-transform", 
          isIdle && !isSelected ? "text-content-muted" : "text-white"
        )} style={{ transform: `rotate(${truck.heading || 0}deg)` }} />
      </div>
    </div>
  );

  return L.divIcon({
    html: iconHtml,
    className: 'custom-leaflet-icon',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
};

// Auto-adjust map bounds to fit markers or route
function MapBounds({ trucks, route }) {
  const map = useMap();
  React.useEffect(() => {
    if (route && route.length > 0) {
      map.fitBounds(route, { padding: [50, 50], maxZoom: 14 });
    } else if (trucks && trucks.length > 0) {
      const bounds = trucks.map(t => [t.lat, t.lng]);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [map, trucks, route]);
  return null;
}

export function FleetMap({ trucks = [] }) {
  // Default center (Bangalore, India as example)
  const defaultCenter = useMemo(() => [12.9716, 77.5946], []);

  const [selectedTruck, setSelectedTruck] = useState(null);
  const [historyRoute, setHistoryRoute] = useState([]);
  const [historyMode, setHistoryMode] = useState('24h'); // '1h', '12h', '24h', 'trip'
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    if (!selectedTruck) {
      setHistoryRoute([]);
      return;
    }
    const fetchHistory = async () => {
      setIsLoadingHistory(true);
      try {
        if (historyMode === 'trip' && selectedTruck.trip_id) {
          const data = await getTripRoute(selectedTruck.trip_id);
          setHistoryRoute(data.map(d => [d.latitude, d.longitude]));
        } else {
          const now = new Date();
          const start = new Date();
          if (historyMode === '1h') start.setHours(now.getHours() - 1);
          if (historyMode === '12h') start.setHours(now.getHours() - 12);
          if (historyMode === '24h') start.setHours(now.getHours() - 24);
          
          const data = await getDriverHistory(selectedTruck.id, start, now);
          setHistoryRoute(data.map(d => [d.latitude, d.longitude]));
        }
      } catch (e) {
        console.error("Failed to fetch route", e);
      } finally {
        setIsLoadingHistory(false);
      }
    };
    fetchHistory();
  }, [selectedTruck, historyMode]);

  return (
    <div className="w-full h-full min-h-[400px] rounded-2xl overflow-hidden border border-border shadow-card relative z-0 flex">
      
      {/* Map Area */}
      <div className="flex-1 relative h-full">
        <MapContainer 
          center={defaultCenter} 
          zoom={11} 
          style={{ height: '100%', width: '100%', zIndex: 0 }}
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <MapBounds trucks={trucks} route={historyRoute} />
          
          {historyRoute.length > 0 && (
            <Polyline 
              positions={historyRoute} 
              pathOptions={{ color: '#22C55E', weight: 4, opacity: 0.8 }} 
            />
          )}

          {trucks.map(truck => (
            <Marker 
              key={truck.id} 
              position={[truck.lat, truck.lng]} 
              icon={createCustomIcon(truck, selectedTruck?.id === truck.id)}
              eventHandlers={{
                click: () => {
                  if (selectedTruck?.id === truck.id) {
                    setSelectedTruck(null);
                  } else {
                    setSelectedTruck(truck);
                    setHistoryMode('24h');
                  }
                },
              }}
            >
              <Tooltip direction="top" offset={[0, -15]} opacity={1} className="custom-leaflet-tooltip" permanent={false}>
                <div className="text-center px-1">
                  <p className="text-xs font-semibold text-content m-0">{truck.driver_name || truck.id}</p>
                  {truck.speed > 0 && <p className="text-[10px] text-content-muted m-0">{truck.speed} km/h</p>}
                  {!truck.speed && <p className="text-[10px] text-content-muted m-0 mt-0.5">Click to view history</p>}
                </div>
              </Tooltip>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Slide-out History Panel */}
      {selectedTruck && (
        <div className="absolute top-4 left-4 z-10 w-72 bg-white/95 backdrop-blur-md rounded-2xl shadow-elevated border border-border p-4 animate-fade-in-up">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold text-content">{selectedTruck.driver_name}</h3>
              <p className="text-[11px] text-content-muted mt-0.5">{selectedTruck.vehicle_registration || 'No Vehicle'}</p>
            </div>
            <button 
              onClick={() => setSelectedTruck(null)}
              className="p-1.5 rounded-full hover:bg-surface-secondary text-content-muted hover:text-content transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest mb-2">Time Filter</p>
              <div className="grid grid-cols-3 gap-2">
                {['1h', '12h', '24h'].map(mode => (
                  <button
                    key={mode}
                    onClick={() => setHistoryMode(mode)}
                    className={cn(
                      "py-1.5 px-2 rounded-lg text-xs font-medium transition-all",
                      historyMode === mode 
                        ? "bg-brand-500 text-white shadow-sm" 
                        : "bg-surface text-content-secondary hover:bg-surface-secondary border border-border"
                    )}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            {selectedTruck.trip_id && (
              <div>
                <p className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest mb-2">Active Trip</p>
                <button
                  onClick={() => setHistoryMode('trip')}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium transition-all",
                    historyMode === 'trip' 
                      ? "bg-brand-500 text-white shadow-sm" 
                      : "bg-surface text-content-secondary hover:bg-surface-secondary border border-border"
                  )}
                >
                  <RouteIcon className="w-3.5 h-3.5" />
                  Show Trip Route
                </button>
              </div>
            )}
            
            <div className="pt-2 border-t border-border/50 flex items-center justify-between">
              <span className="text-[11px] text-content-muted flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                {historyRoute.length} points loaded
              </span>
              {isLoadingHistory && (
                <span className="text-[11px] text-brand-500 font-medium animate-pulse">Loading...</span>
              )}
            </div>
          </div>
        </div>
      )}

      <style>{`
        .custom-leaflet-icon {
          background: transparent;
          border: none;
        }
        .custom-leaflet-icon:hover .custom-hover-effect {
          opacity: 1 !important;
        }
        .custom-leaflet-tooltip {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(8px);
          border: 1px solid #E5EDE7;
          border-radius: 8px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          color: #17201A;
          padding: 6px 10px;
        }
        .leaflet-tooltip-top:before {
          border-top-color: #E5EDE7;
        }
      `}</style>
    </div>
  );
}
