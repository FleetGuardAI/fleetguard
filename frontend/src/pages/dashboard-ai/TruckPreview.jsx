import React from 'react';

/**
 * Premium SVG-based isometric truck previews with custom visual treatments
 * and clean embedded hardware-accelerated animations.
 */
export function TruckPreview({ category = 'fuel_waste' }) {
  const getTruckDetails = () => {
    switch (category) {
      case 'fuel_waste':
      case 'duplicate_fuel':
        return {
          highlightColor: '#f43f5e', // rose/red
          iconType: 'fuel',
          tooltip: 'Active Fuel Sensor telematics overlay',
        };
      case 'high_maintenance':
      case 'unexpected_expense':
      case 'permit_expiry':
      case 'insurance_renewal':
        return {
          highlightColor: '#f59e0b', // amber/orange
          iconType: 'engine',
          tooltip: 'Engine blocks diagnostic scan active',
        };
      case 'route_optimization':
      case 'idle_time':
      case 'unused_truck':
        return {
          highlightColor: '#0ea5e9', // sky blue
          iconType: 'route',
          tooltip: 'Route corridor trajectory plotting',
        };
      case 'delayed_payment':
      case 'invoice_delay':
      case 'emergency_cash':
        return {
          highlightColor: '#8b5cf6', // purple
          iconType: 'invoice',
          tooltip: 'Ledger synchronization active',
        };
      default:
        return {
          highlightColor: '#6366f1', // indigo
          iconType: 'default',
          tooltip: 'Sensors linked',
        };
    }
  };

  const details = getTruckDetails();

  return (
    <div className="relative w-28 h-20 flex-shrink-0 flex items-center justify-center select-none group">
      {/* Floating Ambient Shadow below the truck */}
      <div className="absolute bottom-2 w-20 h-3 bg-black/10 dark:bg-black/40 blur-md rounded-full transform scale-x-110 group-hover:scale-x-120 group-hover:opacity-80 transition-transform duration-500" />

      {/* Isometric SVG Truck */}
      <svg
        viewBox="0 0 160 120"
        className="w-full h-full transform group-hover:-translate-y-1.5 transition-transform duration-500 ease-out"
      >
        <defs>
          {/* Gradients */}
          <linearGradient id="truckBody" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#475569" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>
          <linearGradient id="cabinColor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#64748b" />
            <stop offset="100%" stopColor="#475569" />
          </linearGradient>
          <radialGradient id="highlightGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={details.highlightColor} stopOpacity="0.8" />
            <stop offset="100%" stopColor={details.highlightColor} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="headlightBeam" cx="0%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fef08a" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#fef08a" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* --- TRUCK CONTAINER (Chassis Backend) --- */}
        <g className="animate-body-jiggle">
          {/* Flatbed/Container Base */}
          <path d="M 40,75 L 110,40 L 140,55 L 70,90 Z" fill="url(#truckBody)" />
          
          {/* Upper Cargo Box (Container) */}
          <path d="M 40,35 L 110,0 L 140,15 L 70,50 Z" fill="#334155" opacity="0.9" />
          <path d="M 40,35 L 70,50 L 70,90 L 40,75 Z" fill="#1e293b" />
          <path d="M 70,50 L 140,15 L 140,55 L 70,90 Z" fill="#0f172a" />
          
          {/* Custom cargo overlays based on type */}
          {details.iconType === 'fuel' && (
            <path
              d="M 85,55 L 125,35 L 125,55 L 85,75 Z"
              fill="url(#highlightGlow)"
              className="animate-pulse"
              style={{ animationDuration: '2s' }}
            />
          )}
          {details.iconType === 'route' && (
            <path
              d="M 20,95 L 60,75 Q 85,80 120,65 L 145,55"
              fill="none"
              stroke={details.highlightColor}
              strokeWidth="2.5"
              strokeDasharray="6,4"
              className="animate-route-flow"
            />
          )}
        </g>

        {/* --- WHEELS --- */}
        {/* Front Wheel */}
        <circle cx="100" cy="85" r="9" fill="#0f172a" />
        <circle cx="100" cy="85" r="4" fill="#64748b" className="animate-spin-slow" />
        
        {/* Back Wheels */}
        <circle cx="55" cy="105" r="9" fill="#0f172a" />
        <circle cx="55" cy="105" r="4" fill="#64748b" />
        <circle cx="68" cy="99" r="9" fill="#0f172a" />
        <circle cx="68" cy="99" r="4" fill="#64748b" />

        {/* --- CABIN (Front Hood) --- */}
        <g className="animate-body-jiggle" style={{ animationDelay: '0.1s' }}>
          {/* Cabin Base */}
          <path d="M 110,65 L 140,50 L 155,57 L 125,72 Z" fill="url(#cabinColor)" />
          {/* Main Cabin Box */}
          <path d="M 110,45 L 140,30 L 140,50 L 110,65 Z" fill="#64748b" />
          <path d="M 140,30 L 155,37 L 155,57 L 140,50 Z" fill="#475569" />
          
          {/* Windshield */}
          <path d="M 142,33 L 152,38 L 152,48 L 142,43 Z" fill="#f1f5f9" opacity="0.9" />
          
          {/* Engine highlighting glow */}
          {details.iconType === 'engine' && (
            <circle
              cx="135"
              cy="52"
              r="14"
              fill="url(#highlightGlow)"
              className="animate-pulse"
              style={{ animationDuration: '1.5s' }}
            />
          )}

          {/* Invoice graphic overlay */}
          {details.iconType === 'invoice' && (
            <g transform="translate(112, 10) scale(0.6)">
              <rect x="0" y="0" width="30" height="40" rx="3" fill="#ffffff" stroke="#8b5cf6" strokeWidth="2" />
              <line x1="6" y1="10" x2="24" y2="10" stroke="#cbd5e1" strokeWidth="2" />
              <line x1="6" y1="18" x2="24" y2="18" stroke="#cbd5e1" strokeWidth="2" />
              <line x1="6" y1="26" x2="16" y2="26" stroke="#8b5cf6" strokeWidth="2.5" />
            </g>
          )}

          {/* Headlights beam overlay */}
          <path
            d="M 152,50 Q 170,55 190,65 Q 170,68 152,56 Z"
            fill="url(#headlightBeam)"
            className="animate-headlight-pulse"
          />
        </g>
      </svg>

      {/* Clean micro-tooltip on hover */}
      <span className="absolute bottom-[-16px] scale-0 group-hover:scale-100 transition-transform duration-200 text-[9px] bg-slate-950 text-white px-2 py-0.5 rounded-md whitespace-nowrap z-20 font-medium">
        {details.tooltip}
      </span>

      {/* Keyframe animations */}
      <style>{`
        @keyframes bodyJiggle {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-0.8px); }
        }
        .animate-body-jiggle {
          animation: bodyJiggle 3s ease-in-out infinite;
        }
        @keyframes headlightPulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.75; }
        }
        .animate-headlight-pulse {
          animation: headlightPulse 2.5s ease-in-out infinite;
        }
        @keyframes routeFlow {
          from { stroke-dashoffset: 20; }
          to { stroke-dashoffset: 0; }
        }
        .animate-route-flow {
          animation: routeFlow 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
