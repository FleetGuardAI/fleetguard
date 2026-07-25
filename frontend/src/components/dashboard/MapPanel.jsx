import React, { useState, useEffect } from 'react';
import { MapPin, Navigation, Truck } from 'lucide-react';
import api from '@/api/client';

export default function MapPanel() {
  const [vehicles, setVehicles] = useState([]);

  useEffect(() => {
    async function loadMapVehicles() {
      try {
        const data = await api.vehicles.list({ is_active: true }).catch(() => []);
        setVehicles(data || []);
      } catch {
        setVehicles([]);
      }
    }
    loadMapVehicles();
  }, []);

  return (
    <div
      className="relative rounded-xl dashboard-card overflow-hidden flex flex-col h-[400px]"
      id="map-panel"
    >
      {/* Top Controls */}
      <div className="absolute top-3 left-3 right-3 z-10 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/90 border border-slate-200 shadow-sm pointer-events-auto">
          <Navigation className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
          <span className="text-[11px] font-semibold text-slate-700">Live Route Map</span>
        </div>
        
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/90 border border-slate-200 shadow-sm pointer-events-auto">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-[10px] font-medium text-emerald-600">GPRS Live</span>
        </div>
      </div>

      {/* SVG Map Grid Canvas */}
      <div className="flex-1 bg-slate-50 relative overflow-hidden select-none bg-grid">
        <svg className="w-full h-full opacity-80" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg">
          {/* Main roads */}
          <path d="M 50,200 Q 150,150 250,220 T 450,200 T 650,260 T 750,150" fill="none" stroke="#e2e8f0" strokeWidth="8" strokeLinecap="round" />
          <path d="M 50,200 Q 150,150 250,220 T 450,200 T 650,260 T 750,150" fill="none" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="5 5" />
          <path d="M 200,50 L 250,220 L 320,380" fill="none" stroke="#e2e8f0" strokeWidth="6" />
          <path d="M 200,50 L 250,220 L 320,380" fill="none" stroke="#cbd5e1" strokeWidth="1.5" />
          <path d="M 250,220 T 450,200 T 650,260" fill="none" stroke="#10b981" strokeWidth="3" opacity="0.8" strokeLinecap="round" />
        </svg>

        {/* Dynamic Markers */}
        {vehicles.length === 0 ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50/80 backdrop-blur-xs">
            <MapPin className="w-8 h-8 text-slate-400 mb-2 opacity-50" />
            <p className="text-xs font-medium text-slate-600">No active vehicles registered on map</p>
          </div>
        ) : (
          vehicles.map((v, idx) => {
            const posX = 200 + (idx * 150) % 500;
            const posY = 150 + (idx * 60) % 200;
            return (
              <div
                key={v.id}
                style={{ top: `${posY}px`, left: `${posX}px` }}
                className="absolute flex flex-col items-center animate-bounce duration-1000"
              >
                <div className="p-1.5 rounded bg-emerald-500 text-white shadow-lg text-[9px] font-bold flex items-center gap-1">
                  <Truck className="w-2.5 h-2.5" /> {v.registration_number}
                </div>
                <MapPin className="w-4 h-4 text-emerald-500 -mt-1" />
              </div>
            );
          })
        )}

        {/* Map Legend */}
        <div className="absolute bottom-3 left-3 p-3 rounded-lg bg-white/90 border border-slate-200 shadow-sm space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-slate-700">Truck En-Route ({vehicles.length})</span>
          </div>
        </div>
      </div>
    </div>
  );
}
