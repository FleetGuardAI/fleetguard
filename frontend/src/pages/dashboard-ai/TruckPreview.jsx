import React from 'react';

/**
 * Premium 2.5D Style Truck Component (2D side profile with 3D depth details)
 * Features flat horizontal ground alignment, offset far-side wheels for width/depth,
 * bevel extruded top/rear panels, smooth suspension bouncing, spinning wheels,
 * and visual-glitch-proof exhaust smoke.
 */
export function TruckPreview({ category = 'fuel_waste' }) {
  const getTruckDetails = () => {
    switch (category) {
      case 'fuel_waste':
      case 'duplicate_fuel':
        return {
          highlightColor: '#f43f5e', // rose/red
          topColor: '#fda4af',
          leftColor: '#f43f5e',
          rightColor: '#be123c',
          containerGrad: ['#f43f5e', '#be123c'],
          iconType: 'fuel',
          tooltip: 'Active Fuel Sensor telematics overlay',
        };
      case 'high_maintenance':
      case 'unexpected_expense':
      case 'permit_expiry':
      case 'insurance_renewal':
        return {
          highlightColor: '#f59e0b', // amber/orange
          topColor: '#fde047',
          leftColor: '#f59e0b',
          rightColor: '#b45309',
          containerGrad: ['#f59e0b', '#b45309'],
          iconType: 'engine',
          tooltip: 'Engine blocks diagnostic scan active',
        };
      case 'route_optimization':
      case 'idle_time':
      case 'unused_truck':
        return {
          highlightColor: '#0ea5e9', // sky blue
          topColor: '#7dd3fc',
          leftColor: '#0ea5e9',
          rightColor: '#0369a1',
          containerGrad: ['#0ea5e9', '#0369a1'],
          iconType: 'route',
          tooltip: 'Route corridor trajectory plotting',
        };
      case 'delayed_payment':
      case 'invoice_delay':
      case 'emergency_cash':
        return {
          highlightColor: '#8b5cf6', // purple
          topColor: '#c084fc',
          leftColor: '#8b5cf6',
          rightColor: '#6d28d9',
          containerGrad: ['#8b5cf6', '#6d28d9'],
          iconType: 'invoice',
          tooltip: 'Ledger synchronization active',
        };
      default:
        return {
          highlightColor: '#6366f1', // indigo
          topColor: '#a5b4fc',
          leftColor: '#6366f1',
          rightColor: '#4f46e5',
          containerGrad: ['#6366f1', '#4f46e5'],
          iconType: 'default',
          tooltip: 'Sensors linked',
        };
    }
  };

  const details = getTruckDetails();

  return (
    <div className="relative w-28 h-20 flex-shrink-0 flex items-center justify-center select-none group">
      {/* 2.5D Ground Shadow */}
      <div className="absolute bottom-2.5 w-24 h-1.5 bg-black/10 dark:bg-black/40 blur-sm rounded-full transition-all duration-500 group-hover:scale-x-105 group-hover:opacity-70" />

      {/* 2.5D Animated SVG Truck */}
      <svg
        viewBox="0 0 160 120"
        className="w-full h-full transform transition-transform duration-500 ease-out"
      >
        <defs>
          {/* Cabin Gradient */}
          <linearGradient id="cabinGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#475569" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>

          {/* Dynamic Container Gradient per Category */}
          <linearGradient id={`containerGrad-${category}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={details.containerGrad[0]} />
            <stop offset="100%" stopColor={details.containerGrad[1]} />
          </linearGradient>

          {/* Headlight Beam Gradient */}
          <linearGradient id="headlightBeam" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#fef08a" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#fef08a" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* --- STATIC ENVIRONMENT (Flat ground & motion markers) --- */}
        {/* Road Line */}
        <line x1="5" y1="96" x2="155" y2="96" stroke="#94a3b8" strokeWidth="1" opacity="0.3" strokeLinecap="round" />
        
        {/* Road Lane Dashes */}
        <line
          x1="10"
          y1="102"
          x2="150"
          y2="102"
          stroke="#64748b"
          strokeWidth="1.5"
          strokeDasharray="6,12"
          className="animate-road-flow"
          opacity="0.4"
        />

        {/* Parallax Wind Speed Lines */}
        <line x1="140" y1="34" x2="160" y2="34" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="3,8" className="animate-road-flow" opacity="0.25" />
        <line x1="130" y1="44" x2="150" y2="44" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="3,8" className="animate-road-flow" opacity="0.2" />

        {/* --- FAR-SIDE WHEELS (Rendered behind body for 3D depth) --- */}
        <g>
          {/* Far Back Wheel 1 */}
          <g className="wheel-far-1">
            <circle cx="44" cy="81" r="11" fill="#090d16" opacity="0.8" />
            <circle cx="44" cy="81" r="6" fill="#334155" opacity="0.8" />
            <line x1="39" y1="81" x2="49" y2="81" stroke="#1e293b" strokeWidth="1.2" opacity="0.8" />
            <line x1="44" y1="76" x2="44" y2="86" stroke="#1e293b" strokeWidth="1.2" opacity="0.8" />
          </g>
          
          {/* Far Back Wheel 2 */}
          <g className="wheel-far-2">
            <circle cx="68" cy="81" r="11" fill="#090d16" opacity="0.8" />
            <circle cx="68" cy="81" r="6" fill="#334155" opacity="0.8" />
            <line x1="63" y1="81" x2="73" y2="81" stroke="#1e293b" strokeWidth="1.2" opacity="0.8" />
            <line x1="68" y1="76" x2="68" y2="86" stroke="#1e293b" strokeWidth="1.2" opacity="0.8" />
          </g>
          
          {/* Far Front Wheel */}
          <g className="wheel-far-3">
            <circle cx="126" cy="81" r="11" fill="#090d16" opacity="0.8" />
            <circle cx="126" cy="81" r="6" fill="#334155" opacity="0.8" />
            <line x1="121" y1="81" x2="131" y2="81" stroke="#1e293b" strokeWidth="1.2" opacity="0.8" />
            <line x1="126" y1="76" x2="126" y2="86" stroke="#1e293b" strokeWidth="1.2" opacity="0.8" />
          </g>
        </g>

        {/* --- EXHAUST SMOKE (Starts completely transparent to prevent glitch bubble) --- */}
        <g>
          <circle cx="12" cy="83" r="2.5" fill="#cbd5e1" className="smoke-1" />
          <circle cx="10" cy="84" r="3.5" fill="#94a3b8" className="smoke-2" />
          <circle cx="8" cy="85" r="4.5" fill="#64748b" className="smoke-3" />
        </g>

        {/* --- SUSPENSION JIGGLING BODY CONTAINER --- */}
        <g className="animate-body-jiggle">
          {/* Exhaust Pipe */}
          <path d="M 18,78 L 14,80 L 14,84" stroke="#475569" strokeWidth="2" strokeLinecap="round" fill="none" />

          {/* Under-chassis frame bar */}
          <rect x="18" y="78" width="112" height="4" rx="1" fill="#334155" />

          {/* Near mudguards */}
          <rect x="25" y="75" width="50" height="5" rx="1" fill="#0f172a" opacity="0.85" />
          <path d="M 108,76 A 12 12 0 0 1 132,76" fill="#0f172a" opacity="0.85" />

          {/* fuel tank */}
          <rect x="80" y="79" width="16" height="5" rx="1" fill="#475569" stroke="#334155" strokeWidth="0.5" />

          {/* --- 2.5D CARGO CONTAINER --- */}
          {/* Rear bevel face (3D edge thickness) */}
          <path d="M 20,38 L 15,42 L 15,75 L 20,78 Z" fill={details.rightColor} opacity="0.9" />
          {/* Top bevel face (3D roof edge) */}
          <path d="M 20,38 L 26,33 L 96,33 L 90,38 Z" fill={details.topColor} opacity="0.95" />
          {/* Container Main Side face */}
          <rect
            x="20"
            y="38"
            width="70"
            height="40"
            rx="1.5"
            fill={`url(#containerGrad-${category})`}
          />

          {/* Container Ribs / Vertical Ridges */}
          <g opacity="0.12">
            <line x1="28" y1="38" x2="28" y2="78" stroke="#ffffff" strokeWidth="1.5" />
            <line x1="36" y1="38" x2="36" y2="78" stroke="#ffffff" strokeWidth="1.5" />
            <line x1="44" y1="38" x2="44" y2="78" stroke="#ffffff" strokeWidth="1.5" />
            <line x1="52" y1="38" x2="52" y2="78" stroke="#ffffff" strokeWidth="1.5" />
            <line x1="60" y1="38" x2="60" y2="78" stroke="#ffffff" strokeWidth="1.5" />
            <line x1="68" y1="38" x2="68" y2="78" stroke="#ffffff" strokeWidth="1.5" />
            <line x1="76" y1="38" x2="76" y2="78" stroke="#ffffff" strokeWidth="1.5" />
            <line x1="84" y1="38" x2="84" y2="78" stroke="#ffffff" strokeWidth="1.5" />
          </g>

          {/* --- 2.5D CABIN --- */}
          {/* Cabin Main Side face */}
          <path d="M 94,78 L 132,78 L 132,60 L 122,44 L 94,44 Z" fill="url(#cabinGrad)" />
          {/* Cabin Top bevel */}
          <path d="M 94,44 L 98,40 L 122,40 L 122,44 Z" fill="#94a3b8" />
          {/* Cabin Front-grille bevel (turning corner) */}
          <path d="M 132,60 L 136,57 L 136,75 L 132,78 Z" fill="#1e293b" />
          {/* Front Bumper */}
          <path d="M 132,75 L 137,73 L 137,78 L 132,78 Z" fill="#0f172a" />

          {/* Cabin windshields (Wrapping 2.5D look) */}
          {/* Side window */}
          <path d="M 98,47 L 112,47 L 112,58 L 98,58 Z" fill="#0284c7" opacity="0.6" />
          {/* Wrap-around Front window */}
          <path d="M 115,47 L 122,47 L 128,58 L 118,58 Z" fill="#38bdf8" opacity="0.8" />
          <line x1="117" y1="47" x2="125" y2="58" stroke="#ffffff" strokeWidth="0.8" opacity="0.4" strokeLinecap="round" />

          {/* Headlight bulb */}
          <rect x="134" y="63" width="2" height="5" rx="0.5" fill="#fef08a" />

          {/* Headlight Beam */}
          <path
            d="M 135,63 L 160,53 L 160,83 L 135,68 Z"
            fill="url(#headlightBeam)"
            opacity="0.8"
          />

          {/* --- CATEGORY SIGNAL GLOW OVERLAYS --- */}
          {/* Fuel Sensor Issue */}
          {details.iconType === 'fuel' && (
            <g transform="translate(55, 58)">
              <circle cx="0" cy="0" r="11" fill={details.highlightColor} opacity="0.25" className="animate-ping-glow" />
              <circle cx="0" cy="0" r="7.5" fill={details.highlightColor} opacity="0.85" />
              <path d="M 0,-4.5 C 0,-4.5 3,-1.2 3,1 C 3,2.6 1.6,4 0,4 C -1.6,4 -3,2.6 -3,1 C -3,-1.2 0,-4.5 0,-4.5 Z" fill="#ffffff" />
            </g>
          )}

          {/* Engine/Diagnostics Alert */}
          {details.iconType === 'engine' && (
            <g transform="translate(122, 68)">
              <circle cx="0" cy="0" r="9" fill={details.highlightColor} opacity="0.25" className="animate-ping-glow" />
              <circle cx="0" cy="0" r="6.5" fill={details.highlightColor} opacity="0.85" />
              <path d="M -1.8,-2 L 1.8,-2 L 2,-1 L 2,1.8 L -2,1.8 L -2,-1 Z M -2.5,-0.5 L -2,-0.5 M 2,-0.5 L 2.5,-0.5 M 0,-3 L 0,-2" stroke="#ffffff" strokeWidth="0.8" fill="none" />
            </g>
          )}

          {/* Route Optimization */}
          {details.iconType === 'route' && (
            <g>
              <path
                d="M 25,82 Q 75,98 125,82"
                fill="none"
                stroke={details.highlightColor}
                strokeWidth="2.5"
                strokeDasharray="6,4"
                className="animate-route-flow"
              />
              <g transform="translate(55, 58)">
                <circle cx="0" cy="0" r="11" fill={details.highlightColor} opacity="0.25" className="animate-ping-glow" />
                <circle cx="0" cy="0" r="7.5" fill={details.highlightColor} opacity="0.85" />
                <path d="M -2.5,-2 L 0.5,0 L -2.5,2 M 0.5,-2 L 3.5,0 L 0.5,2" fill="none" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
              </g>
            </g>
          )}

          {/* Invoice Delay / Ledger */}
          {details.iconType === 'invoice' && (
            <g transform="translate(55, 58)">
              <circle cx="0" cy="0" r="11" fill={details.highlightColor} opacity="0.25" className="animate-ping-glow" />
              <circle cx="0" cy="0" r="7.5" fill={details.highlightColor} opacity="0.85" />
              <rect x="-2.5" y="-3.5" width="5" height="7" rx="0.5" fill="#ffffff" />
              <line x1="-1.5" y1="-2" x2="1.5" y2="-2" stroke={details.highlightColor} strokeWidth="0.6" />
              <line x1="-1.5" y1="0" x2="1.5" y2="0" stroke={details.highlightColor} strokeWidth="0.6" />
              <line x1="-1.5" y1="2" x2="0.5" y2="2" stroke={details.highlightColor} strokeWidth="0.6" />
            </g>
          )}
        </g>

        {/* --- SPINNING NEAR-SIDE WHEELS --- */}
        <g>
          {/* Near Back Wheel 1 */}
          <g className="wheel-near-1">
            <circle cx="38" cy="85" r="11" fill="#1e293b" />
            <circle cx="38" cy="85" r="6" fill="#cbd5e1" />
            <circle cx="38" cy="85" r="2.5" fill="#475569" />
            <line x1="33" y1="85" x2="43" y2="85" stroke="#475569" strokeWidth="1.2" />
            <line x1="38" y1="80" x2="38" y2="90" stroke="#475569" strokeWidth="1.2" />
          </g>
          
          {/* Near Back Wheel 2 */}
          <g className="wheel-near-2">
            <circle cx="62" cy="85" r="11" fill="#1e293b" />
            <circle cx="62" cy="85" r="6" fill="#cbd5e1" />
            <circle cx="62" cy="85" r="2.5" fill="#475569" />
            <line x1="57" y1="85" x2="67" y2="85" stroke="#475569" strokeWidth="1.2" />
            <line x1="62" y1="80" x2="62" y2="90" stroke="#475569" strokeWidth="1.2" />
          </g>
          
          {/* Near Front Wheel */}
          <g className="wheel-near-3">
            <circle cx="120" cy="85" r="11" fill="#1e293b" />
            <circle cx="120" cy="85" r="6" fill="#cbd5e1" />
            <circle cx="120" cy="85" r="2.5" fill="#475569" />
            <line x1="115" y1="85" x2="125" y2="85" stroke="#475569" strokeWidth="1.2" />
            <line x1="120" y1="80" x2="120" y2="90" stroke="#475569" strokeWidth="1.2" />
          </g>
        </g>
      </svg>

      {/* Micro-tooltip on hover */}
      <span className="absolute bottom-[-16px] scale-0 group-hover:scale-100 transition-transform duration-200 text-[9px] bg-slate-950 text-white px-2 py-0.5 rounded-md whitespace-nowrap z-20 font-medium">
        {details.tooltip}
      </span>

      {/* Keyframe Styles */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .wheel-near-1 { animation: spin 0.6s linear infinite; transform-origin: 38px 85px; }
        .wheel-near-2 { animation: spin 0.6s linear infinite; transform-origin: 62px 85px; }
        .wheel-near-3 { animation: spin 0.6s linear infinite; transform-origin: 120px 85px; }
        
        .wheel-far-1 { animation: spin 0.6s linear infinite; transform-origin: 44px 81px; }
        .wheel-far-2 { animation: spin 0.6s linear infinite; transform-origin: 68px 81px; }
        .wheel-far-3 { animation: spin 0.6s linear infinite; transform-origin: 126px 81px; }

        @keyframes bodyJiggle {
          0%, 100% { transform: translate3d(0, 0, 0); }
          50% { transform: translate3d(0, -1.2px, 0); }
        }
        .animate-body-jiggle {
          animation: bodyJiggle 0.6s ease-in-out infinite;
          will-change: transform;
        }

        @keyframes roadFlow {
          from { stroke-dashoffset: 0; }
          to { stroke-dashoffset: 18; }
        }
        .animate-road-flow {
          animation: roadFlow 0.5s linear infinite;
        }

        @keyframes smoke-1 {
          0% { transform: translate3d(0, 0, 0) scale(0.6); opacity: 0; }
          10% { opacity: 0.7; }
          100% { transform: translate3d(-12px, -2px, 0) scale(1.3); opacity: 0; }
        }
        @keyframes smoke-2 {
          0% { transform: translate3d(0, 0, 0) scale(0.6); opacity: 0; }
          10% { opacity: 0.7; }
          100% { transform: translate3d(-20px, -4px, 0) scale(1.7); opacity: 0; }
        }
        @keyframes smoke-3 {
          0% { transform: translate3d(0, 0, 0) scale(0.6); opacity: 0; }
          10% { opacity: 0.7; }
          100% { transform: translate3d(-28px, -6px, 0) scale(2.1); opacity: 0; }
        }
        .smoke-1 {
          animation: smoke-1 1.2s linear infinite;
          transform-origin: 14px 82px;
        }
        .smoke-2 {
          animation: smoke-2 1.2s linear infinite;
          animation-delay: 0.4s;
          transform-origin: 14px 82px;
        }
        .smoke-3 {
          animation: smoke-3 1.2s linear infinite;
          animation-delay: 0.8s;
          transform-origin: 14px 82px;
        }

        @keyframes pingGlow {
          0% { transform: scale(0.85); opacity: 0.5; }
          100% { transform: scale(1.7); opacity: 0; }
        }
        .animate-ping-glow {
          animation: pingGlow 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
          transform-origin: center;
        }
      `}</style>
    </div>
  );
}

export default TruckPreview;
