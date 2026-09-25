import React, { useState, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Tooltip, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { renderToStaticMarkup } from 'react-dom/server';
import { Navigation, MapPin } from 'lucide-react';
import { cn } from '@/utils/cn';
import { VehicleDetailOverlay } from './VehicleDetailOverlay';

// ── Demo data for when no real telematics is available ──
const DEMO_VEHICLES = [
  { id: 'RJ14-XX-4821', lat: 26.9124, lng: 75.7873, speed: 68, status: 'active', fuel: 37, driver_name: 'Rajesh Kumar', trip: '#4092', route: 'Delhi → Jaipur', eta: '14:42' },
  { id: 'MH12-AB-3901', lat: 19.076, lng: 72.8777, speed: 45, status: 'active', fuel: 62, driver_name: 'Suresh Patil', trip: '#4088', route: 'Mumbai → Pune', eta: '16:10' },
  { id: 'KA01-CD-7722', lat: 12.9716, lng: 77.5946, speed: 0, status: 'idle', fuel: 81, driver_name: 'Venkat R.', trip: '—', route: 'Bangalore Depot', eta: '—' },
  { id: 'DL01-EF-5543', lat: 28.6139, lng: 77.209, speed: 72, status: 'active', fuel: 28, driver_name: 'Amit Singh', trip: '#4095', route: 'Delhi → Agra', eta: '13:15' },
  { id: 'GJ05-GH-1190', lat: 23.0225, lng: 72.5714, speed: 55, status: 'delayed', fuel: 44, driver_name: 'Prakash Joshi', trip: '#4091', route: 'Ahmedabad → Surat', eta: '15:30' },
  { id: 'TN09-JK-8834', lat: 13.0827, lng: 80.2707, speed: 38, status: 'active', fuel: 55, driver_name: 'Karthik M.', trip: '#4097', route: 'Chennai → Vellore', eta: '17:00' },
  { id: 'RJ07-LM-2210', lat: 26.2389, lng: 73.0243, speed: 0, status: 'alert', fuel: 12, driver_name: 'Mohan Lal', trip: '#4089', route: 'Jodhpur → Jaisalmer', eta: 'STALLED' },
  { id: 'UP32-NO-6678', lat: 26.8467, lng: 80.9462, speed: 61, status: 'active', fuel: 70, driver_name: 'Deepak Verma', trip: '#4093', route: 'Lucknow → Kanpur', eta: '14:50' },
];

const DEMO_ROUTES = [
  [[28.6139, 77.209], [27.1767, 78.0081], [26.9124, 75.7873]],  // Delhi → Agra → Jaipur
  [[19.076, 72.8777], [18.5204, 73.8567]],  // Mumbai → Pune
  [[23.0225, 72.5714], [21.1702, 72.8311]],  // Ahmedabad → Surat
];

// ── Custom marker icons ──
const createVehicleIcon = (vehicle) => {
  const colorMap = {
    active: { bg: '#1F5C42', border: '#22C55E', text: 'white' },
    idle: { bg: '#FFFFFF', border: '#E5EDE7', text: '#98A49C' },
    delayed: { bg: '#FEF3C7', border: '#E8A33D', text: '#92400E' },
    alert: { bg: '#FEE2E2', border: '#C4483A', text: '#991B1B' },
  };
  const colors = colorMap[vehicle.status] || colorMap.active;

  const html = renderToStaticMarkup(
    <div style={{ width: '24px', height: '24px', position: 'relative' }}>
      <div style={{
        width: '24px', height: '24px', borderRadius: '50%',
        backgroundColor: colors.bg, border: `2px solid ${colors.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: vehicle.status === 'active' ? `0 0 12px ${colors.border}40` : '0 2px 4px rgba(0,0,0,0.2)',
      }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={colors.text} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 19 21 12 17 5 21 12 2" />
        </svg>
      </div>
    </div>
  );

  return L.divIcon({
    html,
    className: 'fleet-canvas-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

export function FleetCanvas({ trucks = [], onVehicleSelect }) {
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  const vehicles = useMemo(() => {
    if (trucks.length > 0) {
      return trucks.map(t => ({
        ...t,
        status: t.status || 'active',
        fuel: t.fuel || Math.floor(Math.random() * 80 + 20),
        driver_name: t.driver_name || 'Unknown',
        trip: t.trip || '—',
        route: t.route || '—',
        eta: t.eta || '—',
        speed: t.speed || 0,
      }));
    }
    return DEMO_VEHICLES;
  }, [trucks]);

  const isDemo = trucks.length === 0;
  const defaultCenter = useMemo(() => [22.5, 78.5], []); // Center of India

  const handleMarkerClick = useCallback((vehicle) => {
    setSelectedVehicle(vehicle);
    onVehicleSelect?.(vehicle);
  }, [onVehicleSelect]);

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden border border-[#1e293b]/60 shadow-[0_8px_32px_rgba(0,0,0,0.3)]">
      {/* LIVE FLEET badge */}
      <div className="absolute top-3 left-3 z-[500] flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[#0B1018]/90 backdrop-blur-sm border border-white/5">
        <div className="w-1.5 h-1.5 rounded-full bg-fg-green animate-pulse" />
        <span className="text-[9px] font-bold text-white/80 uppercase tracking-[0.15em]">Live Fleet</span>
      </div>

      {/* Demo badge */}
      {isDemo && (
        <div className="absolute top-3 right-3 z-[500] px-2 py-1 rounded-md bg-fg-amber/20 border border-fg-amber/30">
          <span className="text-[9px] font-bold text-fg-amber uppercase tracking-widest">Demo Data</span>
        </div>
      )}

      {/* Vehicle count */}
      <div className="absolute bottom-3 left-3 z-[500] flex items-center gap-3 px-3 py-2 rounded-lg bg-[#0B1018]/90 backdrop-blur-sm border border-white/5">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-fg-green" />
          <span className="text-[10px] text-white/70 font-medium">{vehicles.filter(v => v.status === 'active').length} active</span>
        </div>
        <div className="w-px h-3 bg-white/10" />
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-fg-amber" />
          <span className="text-[10px] text-white/70 font-medium">{vehicles.filter(v => v.status === 'delayed').length} delayed</span>
        </div>
        <div className="w-px h-3 bg-white/10" />
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-fg-red" />
          <span className="text-[10px] text-white/70 font-medium">{vehicles.filter(v => v.status === 'alert').length} alert</span>
        </div>
      </div>

      <MapContainer
        center={defaultCenter}
        zoom={5}
        style={{ height: '100%', width: '100%', zIndex: 0, background: '#0B1018' }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        {/* Route lines */}
        {isDemo && DEMO_ROUTES.map((route, i) => (
          <Polyline
            key={i}
            positions={route}
            pathOptions={{
              color: '#1F5C42',
              weight: 2,
              opacity: 0.4,
              dashArray: '6 8',
            }}
          />
        ))}

        {/* Vehicle markers */}
        {vehicles.map(vehicle => (
          <Marker
            key={vehicle.id}
            position={[vehicle.lat, vehicle.lng]}
            icon={createVehicleIcon(vehicle)}
            eventHandlers={{
              click: () => handleMarkerClick(vehicle),
            }}
          >
            <Tooltip
              direction="top"
              offset={[0, -14]}
              opacity={1}
              className="fleet-canvas-tooltip"
              permanent={false}
            >
              <div className="text-center">
                <p className="text-[10px] font-bold text-white m-0">{vehicle.id}</p>
                {vehicle.speed > 0 && (
                  <p className="text-[9px] text-white/60 m-0">{vehicle.speed} km/h</p>
                )}
              </div>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>

      {/* Vehicle Detail Overlay */}
      {selectedVehicle && (
        <VehicleDetailOverlay
          vehicle={selectedVehicle}
          onClose={() => setSelectedVehicle(null)}
        />
      )}

      <style>{`
        .fleet-canvas-marker {
          background: transparent !important;
          border: none !important;
        }
        .fleet-canvas-tooltip {
          background: rgba(11, 16, 24, 0.92) !important;
          backdrop-filter: blur(8px);
          border: 1px solid rgba(255,255,255,0.08) !important;
          border-radius: 8px !important;
          box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
          color: white !important;
          padding: 6px 10px !important;
        }
        .fleet-canvas-tooltip .leaflet-tooltip-arrow {
          display: none;
        }
        .leaflet-tooltip-top.fleet-canvas-tooltip::before {
          border-top-color: rgba(11, 16, 24, 0.92) !important;
        }
      `}</style>
    </div>
  );
}
