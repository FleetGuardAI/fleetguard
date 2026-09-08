import React, { useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { renderToStaticMarkup } from 'react-dom/server';
import { MapPin, Navigation } from 'lucide-react';
import { cn } from '@/utils/cn';

// Auto-adjust map bounds to fit markers and route
function MapBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, bounds]);
  return null;
}

const createCustomIcon = (type) => {
  const isOrigin = type === 'origin';
  const iconHtml = renderToStaticMarkup(
    <div className="group relative" style={{ width: '32px', height: '32px' }}>
      <div className={cn(
        "absolute -inset-2 rounded-full blur-md opacity-30",
        isOrigin ? "bg-blue-500" : "bg-red-500"
      )} />
      <div className={cn(
        "relative flex items-center justify-center w-full h-full rounded-full shadow-lg border-2 text-white",
        isOrigin ? "bg-blue-600 border-blue-400" : "bg-red-600 border-red-400"
      )}>
        {isOrigin ? <Navigation className="w-4 h-4" /> : <MapPin className="w-4 h-4" />}
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

export function RouteMap({ 
  origin, 
  destination, 
  routePolyline, // Array of [lat, lng]
  className 
}) {
  const defaultCenter = useMemo(() => [20.5937, 78.9629], []); // India center

  const bounds = useMemo(() => {
    const b = [];
    if (origin?.lat && origin?.lng) b.push([origin.lat, origin.lng]);
    if (destination?.lat && destination?.lng) b.push([destination.lat, destination.lng]);
    if (routePolyline && routePolyline.length > 0) {
      // Add first, middle, and last point of polyline to bounds to ensure it fits
      b.push(routePolyline[0]);
      b.push(routePolyline[Math.floor(routePolyline.length / 2)]);
      b.push(routePolyline[routePolyline.length - 1]);
    }
    return b.length > 1 ? b : null;
  }, [origin, destination, routePolyline]);

  return (
    <div className={cn("w-full h-[300px] rounded-xl overflow-hidden border border-border shadow-inner relative z-0", className)}>
      <MapContainer 
        center={defaultCenter} 
        zoom={5} 
        style={{ height: '100%', width: '100%', zIndex: 0 }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        {bounds && <MapBounds bounds={bounds} />}

        {origin?.lat && origin?.lng && (
          <Marker position={[origin.lat, origin.lng]} icon={createCustomIcon('origin')}>
            <Popup className="custom-leaflet-popup">
              <p className="font-semibold text-sm m-0">Pickup</p>
              <p className="text-xs text-content-muted m-0">{origin.address || origin.description}</p>
            </Popup>
          </Marker>
        )}

        {destination?.lat && destination?.lng && (
          <Marker position={[destination.lat, destination.lng]} icon={createCustomIcon('destination')}>
            <Popup className="custom-leaflet-popup">
              <p className="font-semibold text-sm m-0">Dropoff</p>
              <p className="text-xs text-content-muted m-0">{destination.address || destination.description}</p>
            </Popup>
          </Marker>
        )}

        {routePolyline && routePolyline.length > 0 && (
          <Polyline 
            positions={routePolyline} 
            color="#2563EB" // blue-600
            weight={4}
            opacity={0.8}
            lineJoin="round"
          />
        )}
      </MapContainer>
      <style>{`
        .custom-leaflet-icon {
          background: transparent;
          border: none;
        }
        .custom-leaflet-popup .leaflet-popup-content-wrapper {
          border-radius: 8px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .custom-leaflet-popup .leaflet-popup-content {
          margin: 12px 16px;
        }
      `}</style>
    </div>
  );
}
