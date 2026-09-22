import React, { forwardRef, useImperativeHandle, useRef } from 'react';
import { motion } from 'framer-motion'; 
import { cn } from '@/utils/cn';

/**
 * FleetMap renders the ambient physical reality of the fleet: routes and vehicles.
 * It exposes refs so the master GSAP timeline can animate its properties.
 */
export const FleetMap = forwardRef((props, ref) => {
  const containerRef = useRef(null);
  const targetVehicleRef = useRef(null);
  const otherVehiclesRef = useRef(null);
  const routesRef = useRef(null);
  
  useImperativeHandle(ref, () => ({
    get container() { return containerRef.current; },
    get targetVehicle() { return targetVehicleRef.current; },
    get otherVehicles() { return otherVehiclesRef.current; },
    get routes() { return routesRef.current; },
    setIntelligenceMode: (active) => {
      // Find all vehicles and assign random semantic colors if active
      if (!otherVehiclesRef.current) return;
      const vehicles = otherVehiclesRef.current.children;
      const colors = ['#1F5C42', '#1F5C42', '#1F5C42', '#E8A33D', '#1F5C42', '#C4483A'];
      
      Array.from(vehicles).forEach((v, i) => {
        if (active) {
          v.style.backgroundColor = colors[i % colors.length];
          if (colors[i % colors.length] !== '#1F5C42') {
            v.style.boxShadow = `0 0 15px ${colors[i % colors.length]}`;
          }
        } else {
          v.style.backgroundColor = 'rgba(255,255,255,0.2)';
          v.style.boxShadow = 'none';
        }
      });
    }
  }));

  // We define a 2000x2000 coordinate system. The camera will move around this.
  return (
    <div 
      ref={containerRef}
      className="absolute top-1/2 left-1/2 w-[2000px] h-[2000px] pointer-events-none z-0"
    >
      {/* Background Grid */}
      <div className="absolute inset-0 bg-grid opacity-10" />

      {/* Routes (SVG) */}
      <svg ref={routesRef} className="absolute inset-0 w-full h-full" viewBox="0 0 2000 2000">
        <defs>
          <linearGradient id="routeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgba(34, 197, 94, 0.1)" />
            <stop offset="100%" stopColor="rgba(34, 197, 94, 0.4)" />
          </linearGradient>
        </defs>
        
        {/* Ambient Routes */}
        <path d="M 200,400 Q 500,200 800,600 T 1500,800" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="4" />
        <path d="M 400,1800 Q 600,1200 1000,1000 T 1800,600" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="4" />
        <path d="M 100,1000 C 300,1000 400,1400 800,1600" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="4" />
        
        {/* The Target Route */}
        <path 
          id="targetRoute"
          d="M 500,1500 Q 800,1100 1000,1000 T 1500,500" 
          fill="none" 
          stroke="url(#routeGrad)" 
          strokeWidth="6" 
          strokeLinecap="round"
          className="opacity-50"
        />
      </svg>

      {/* Ambient Vehicles */}
      <div ref={otherVehiclesRef}>
        <Vehicle x={800} y={600} active={false} />
        <Vehicle x={1500} y={800} active={false} />
        <Vehicle x={600} y={1300} active={false} />
        <Vehicle x={200} y={400} active={false} />
        <Vehicle x={1800} y={600} active={false} />
        <Vehicle x={400} y={1800} active={false} />
        <Vehicle x={800} y={1600} active={false} />
      </div>

      {/* The Target Vehicle (MH-04-1234) */}
      <div 
        ref={targetVehicleRef}
        className="absolute w-8 h-8 -ml-4 -mt-4 flex items-center justify-center z-10"
        style={{ left: '1000px', top: '1000px' }} // Positioned exactly at the center of the 2000x2000 map
      >
        {/* Pulse ring */}
        <div className="absolute inset-0 rounded-full border border-fg-green/40 animate-ping" />
        {/* Core node */}
        <div className="relative w-3 h-3 rounded-full bg-fg-green shadow-[0_0_15px_rgba(34,197,94,0.8)]" />
        
        {/* Vehicle Label (Fades in during Trip Phase) */}
        <div className="target-vehicle-label absolute top-full mt-2 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-surface border border-border whitespace-nowrap opacity-0 shadow-lg transition-colors">
          <span className="text-[10px] font-bold text-content tracking-widest uppercase">MH-04-1234</span>
        </div>
      </div>

    </div>
  );
});

function Vehicle({ x, y, active }) {
  return (
    <div 
      className="absolute w-2 h-2 -ml-1 -mt-1 rounded-full z-0 transition-all duration-1000"
      style={{ 
        left: `${x}px`, 
        top: `${y}px`,
        backgroundColor: active ? '#22C55E' : 'rgba(255,255,255,0.2)'
      }}
    />
  );
}
