import React from 'react';
import { MapPin, Navigation, Truck } from 'lucide-react';

export default function MapPanel() {
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

          {/* Active green routes */}
          <path d="M 250,220 T 450,200 T 650,260" fill="none" stroke="#10b981" strokeWidth="3" opacity="0.8" strokeLinecap="round" />

          {/* Zones */}
          <circle cx="250" cy="220" r="40" fill="#10b981" fillOpacity="0.05" />
          <circle cx="650" cy="260" r="30" fill="#ef4444" fillOpacity="0.05" />
        </svg>

        {/* Live Truck Markers */}
        <div className="absolute top-[210px] left-[240px] flex flex-col items-center animate-bounce duration-1000">
          <div className="p-1.5 rounded bg-emerald-500 text-white shadow-lg text-[9px] font-bold flex items-center gap-1">
            <Truck className="w-2.5 h-2.5" /> RJ14 XX 1234
          </div>
          <MapPin className="w-4 h-4 text-emerald-500 -mt-1" />
        </div>

        <div className="absolute top-[250px] left-[640px] flex flex-col items-center">
          <div className="p-1.5 rounded bg-red-500 text-white shadow-lg text-[9px] font-bold flex items-center gap-1 animate-pulse">
            <AlertTriangleIcon className="w-2.5 h-2.5" /> Fuel Alert
          </div>
          <MapPin className="w-4 h-4 text-red-500 -mt-1" />
        </div>

        <div className="absolute top-[180px] left-[440px] flex flex-col items-center opacity-80">
          <div className="p-1 rounded bg-white border border-slate-200 text-slate-600 shadow-sm text-[9px] font-bold">
            MH12 AB 5678
          </div>
          <MapPin className="w-4 h-4 text-slate-400 -mt-1" />
        </div>

        {/* Map Legend */}
        <div className="absolute bottom-3 left-3 p-3 rounded-lg bg-white/90 border border-slate-200 shadow-sm space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-slate-700">Truck En-Route</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-[10px] text-slate-700">Theft Warning Zone</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertTriangleIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}
