import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { renderToStaticMarkup } from 'react-dom/server';
import { Navigation } from 'lucide-react';
import { cn } from '@/utils/cn';

// Leaflet setup for custom HTML markers
const createCustomIcon = (truck) => {
  const isIdle = truck.status === 'idle';
  const iconHtml = renderToStaticMarkup(
    <div className="group relative cursor-pointer" style={{ width: '28px', height: '28px' }}>
      <div className="absolute -inset-2 bg-brand-500/15 rounded-full blur-md opacity-0 transition-opacity custom-hover-effect" />
      <div className={cn(
        "relative flex items-center justify-center w-full h-full rounded-full shadow-lg border",
        isIdle ? "bg-white border-border" : "bg-brand-500 border-brand-400 text-white"
      )}>
        <Navigation className={cn("w-4 h-4", isIdle ? "text-content-muted" : "text-white")} />
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

export function FleetMap({ trucks = [] }) {
  // Default center (Bangalore, India as example)
  const defaultCenter = useMemo(() => [12.9716, 77.5946], []);

  return (
    <div className="w-full h-full min-h-[400px] rounded-2xl overflow-hidden border border-border shadow-card relative z-0">
      <MapContainer 
        center={defaultCenter} 
        zoom={11} 
        style={{ height: '100%', width: '100%', zIndex: 0 }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        {trucks.map(truck => (
          <Marker 
            key={truck.id} 
            position={[truck.lat, truck.lng]} 
            icon={createCustomIcon(truck)}
          >
            <Tooltip direction="top" offset={[0, -15]} opacity={1} className="custom-leaflet-tooltip" permanent={false}>
              <div className="text-center px-1">
                <p className="text-xs font-semibold text-content m-0">{truck.id}</p>
                {truck.speed && <p className="text-[10px] text-content-muted m-0">{truck.speed}</p>}
              </div>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>
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
