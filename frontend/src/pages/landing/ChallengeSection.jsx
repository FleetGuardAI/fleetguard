import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Map, Droplets, Receipt, FileText,
  Truck, Users, Wrench, CreditCard,
  ArrowRight, Play, Activity, ShieldAlert, ArrowDown
} from 'lucide-react';

// ============================================================================
// DATA & COORDINATES
// ============================================================================

// Desktop exact coordinates mapped to a 1000x750 viewBox logic
const SPATIAL_SOURCES = [
  { id: 'trips', label: 'TRIPS', sub: 'TMS / Dispatch', icon: Map, color: 'text-blue-500', pos: { x: 25, y: 15 }, scale: 1.05, delay: 0.1 },
  { id: 'vehicles', label: 'VEHICLES', sub: 'Telematics', icon: Truck, color: 'text-cyan-500', pos: { x: 15, y: 25 }, scale: 1.1, delay: 0.6 },
  { id: 'fuel', label: 'FUEL', sub: 'Fuel cards', icon: Droplets, color: 'text-amber-500', pos: { x: 10, y: 40 }, scale: 0.95, delay: 0.2 },
  { id: 'drivers', label: 'DRIVERS', sub: 'Field updates', icon: Users, color: 'text-slate-500', pos: { x: 8, y: 55 }, scale: 0.98, delay: 0.3 },
  { id: 'expenses', label: 'EXPENSES', sub: 'Spreadsheets', icon: Receipt, color: 'text-blue-500', pos: { x: 12, y: 70 }, scale: 1.0, delay: 0.4 },
  { id: 'maintenance', label: 'MAINTENANCE', sub: 'Service logs', icon: Wrench, color: 'text-red-500', pos: { x: 20, y: 85 }, scale: 0.95, delay: 0.7 },
  { id: 'documents', label: 'DOCUMENTS', sub: 'WhatsApp / Email', icon: FileText, color: 'text-purple-500', pos: { x: 32, y: 90 }, scale: 0.9, delay: 0.5 },
  { id: 'payments', label: 'PAYMENTS', sub: 'Bank / ERP', icon: CreditCard, color: 'text-fg-green', pos: { x: 28, y: 50 }, scale: 0.9, delay: 0.8 }
];

const NODE_POS = { x: 50, y: 50 };

const METRICS = [
  { value: '6+', label: 'Data Sources', sub: 'Typically used' },
  { value: '15+', label: 'Systems Connected', sub: 'Across operations' },
  { value: '30%', label: 'Manual Follow-ups', sub: 'Time lost' },
  { value: 'High', label: 'Exception Risk', sub: 'Due to silos' },
];

// ============================================================================
// COMPONENTS - LEFT COLUMN
// ============================================================================

function ChallengeCopy() {
  return (
    <div className="flex flex-col space-y-6 md:space-y-8">
      {/* Label */}
      <div className="flex items-center gap-3">
        <div className="w-6 h-[1px] bg-fg-green/40"></div>
        <span className="text-[11px] font-semibold tracking-[0.2em] uppercase text-fg-green">
          01 The Challenge
        </span>
      </div>

      {/* Headline */}
      <h2 className="text-4xl md:text-[40px] lg:text-[44px] font-medium tracking-tight leading-[1.15] text-content">
        Your fleet generates<br className="hidden md:block"/> information everywhere.<br/>
        <span className="text-fg-green">The hard part is<br className="hidden md:block"/> knowing what matters.</span>
      </h2>

      {/* Supporting Copy */}
      <p className="text-[17px] text-content-secondary font-light leading-relaxed max-w-[420px]">
        Trips, fuel, expenses, documents, driver updates, maintenance, payments — information lives in different systems, teams and formats, making it hard to get a clear, real-time picture.
      </p>

      {/* CTAs */}
      <div className="flex flex-wrap items-center gap-5 pt-2">
        <a href="#demo" className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-fg-green text-white font-medium hover:bg-fg-green-deep transition-colors shadow-sm shadow-fg-green/10 group text-[13px]">
          See How Vaahan Solves This
          <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
        </a>
        <button className="inline-flex items-center justify-center py-3 text-content-secondary hover:text-content transition-colors group font-medium text-[13px]">
          <span className="flex items-center justify-center w-7 h-7 rounded-full border border-border/80 group-hover:border-content-muted mr-2.5 transition-colors bg-white">
            <Play className="w-3 h-3 ml-0.5 fill-current opacity-70" />
          </span>
          Watch 2 min video
        </button>
      </div>
    </div>
  );
}

function ChallengeMetrics() {
  return (
    <div className="flex flex-wrap md:flex-nowrap gap-x-8 gap-y-8 pt-8 mt-12 border-t border-border/50 max-w-xl">
      {METRICS.map((metric, i) => (
        <div key={i} className="flex-1 min-w-[100px] relative">
          {i !== 0 && (
            <div className="hidden md:block absolute left-[-16px] top-2 bottom-2 w-[1px] bg-border/40"></div>
          )}
          <div className="text-[28px] font-medium text-content mb-1 leading-none">{metric.value}</div>
          <div className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest mb-0.5 leading-tight">{metric.label}</div>
          <div className="text-[11px] text-content-muted leading-tight">{metric.sub}</div>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// COMPONENTS - RIGHT COLUMN VISUALIZATION (DESKTOP)
// ============================================================================

function SignalModule({ data }) {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      className="absolute flex items-center gap-2.5 z-20 group cursor-default"
      style={{
        top: `${data.pos.y}%`,
        left: `${data.pos.x}%`,
        scale: data.scale,
        transform: 'translate(-50%, -50%)' // Ensure anchor is center
      }}
      initial={reducedMotion ? { opacity: 1 } : { opacity: 0, filter: 'blur(4px)' }}
      animate={{ y: [0, -6, 0] }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, filter: 'blur(0px)' }}
      transition={{
        opacity: { duration: 0.8, delay: data.delay, ease: "easeOut" },
        filter: { duration: 0.8, delay: data.delay, ease: "easeOut" },
        y: { duration: 4, repeat: Infinity, ease: "easeInOut", delay: data.delay }
      }}
      viewport={{ once: true, margin: "-50px" }}
    >
      <div className="shrink-0 w-8 h-8 rounded-full bg-white border border-border/60 flex items-center justify-center shadow-sm relative transition-colors group-hover:border-border">
        {/* Subtle activity dot */}
        <div className={`absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full ${data.color} opacity-40`}></div>
        <data.icon className={`w-3.5 h-3.5 ${data.color} opacity-80`} strokeWidth={2} />
      </div>
      <div className="flex flex-col">
        <div className="text-[10px] font-bold text-content tracking-widest uppercase leading-none">{data.label}</div>
        <div className="text-[9px] text-content-muted leading-tight mt-0.5 tracking-wide">{data.sub}</div>
      </div>
    </motion.div>
  );
}

function FleetContextGraph({ className, style }) {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      className={`z-20 flex flex-col items-center justify-center ${className || ''}`}
      style={style}
      initial={reducedMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
      whileInView={reducedMotion ? { opacity: 1, scale: 1 } : { opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, delay: 0.8, ease: "easeOut" }}
      viewport={{ once: true, margin: "-50px" }}
    >
      <div className="relative w-[260px] h-[260px] flex items-center justify-center">
        {/* Abstract core glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(34,197,94,0.08),_transparent_60%)] rounded-full pointer-events-none"></div>

        {/* Abstract map/route geometry */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 260 260">
           {/* Connecting route arcs */}
           <path d="M 40,200 C 90,80 180,60 230,160" fill="none" stroke="#4ADE80" strokeWidth="1.5" strokeDasharray="4 6" strokeOpacity="0.4" />
           <path d="M 60,80 C 140,140 200,140 230,80" fill="none" stroke="#cbd5e1" strokeWidth="1" strokeDasharray="2 4" strokeOpacity="0.5" />

           {/* Boundary rings representing "unified context" */}
           <circle cx="130" cy="130" r="75" fill="none" stroke="#cbd5e1" strokeWidth="0.5" strokeOpacity="0.3" />
           <circle cx="130" cy="130" r="110" fill="none" stroke="#cbd5e1" strokeWidth="0.5" strokeOpacity="0.15" />
        </svg>

        {/* Minimal vehicle markers */}
        <div className="absolute top-[72px] left-[195px] w-1.5 h-1.5 rounded-full bg-slate-400"></div>
        <div className="absolute top-[178px] left-[105px] w-1.5 h-1.5 rounded-full bg-slate-400"></div>

        {/* Highlighted active vehicle tracking */}
        <div className="absolute top-[105px] left-[85px] flex flex-col items-center">
           <div className="relative flex items-center justify-center">
              <div className="absolute inset-0 w-7 h-7 -ml-[10px] -mt-[10px] bg-fg-green/20 rounded-full animate-ping-slow"></div>
              <div className="w-3.5 h-3.5 bg-[#0f172a] border border-fg-green rounded-full flex items-center justify-center relative z-10 shadow-[0_0_8px_rgba(34,197,94,0.4)]">
                 <div className="w-1.5 h-1.5 bg-fg-green rounded-full"></div>
              </div>
           </div>

           {/* Overlapping Signals arriving at the vehicle */}
           <div className="absolute top-4 left-4 flex flex-col gap-1 z-30">
              <div className="px-1.5 py-0.5 bg-white/90 backdrop-blur-sm border border-border/40 text-[7px] font-bold text-slate-700 rounded-sm shadow-sm whitespace-nowrap">TRIP 4092</div>
              <div className="px-1.5 py-0.5 bg-white/90 backdrop-blur-sm border border-border/40 text-[7px] font-bold text-amber-600 rounded-sm shadow-sm whitespace-nowrap">LOW FUEL</div>
           </div>
        </div>

        {/* The Core Intelligence Label */}
        <div className="absolute bottom-6 text-center">
           <div className="text-[9px] font-bold text-content-secondary uppercase tracking-[0.2em] mb-1 opacity-80">
              The Vaahan
           </div>
           <div className="text-[12px] font-bold text-content leading-tight tracking-wider animate-pulse">
              CONTEXTUAL<br/>INTELLIGENCE
           </div>
        </div>
      </div>
    </motion.div>
  );
}

function OperationalDashboard({ className, style }) {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      className={`z-30 flex flex-col bg-[#0b1120] border border-[#1e293b] rounded-2xl shadow-[0_20px_50px_-10px_rgba(0,0,0,0.4)] overflow-hidden w-[240px] lg:w-[260px] ${className || ''}`}
      style={style}
      initial={reducedMotion ? { opacity: 1, x: 0 } : { opacity: 0, x: 20 }}
      whileInView={reducedMotion ? { opacity: 1, x: 0 } : { opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 1.2, ease: "easeOut" }}
      viewport={{ once: true, margin: "-50px" }}
    >
      <div className="px-4 py-3 border-b border-[#1e293b] flex items-center justify-between bg-[#020617]/80 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-[4px] bg-fg-green flex items-center justify-center">
            <span className="text-[9px] font-bold text-[#0b1120] leading-none">V</span>
          </div>
          <span className="text-[13px] font-semibold text-white/90 tracking-tight">the vaahan</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-fg-green/80 animate-pulse"></div>
          <span className="text-[9px] text-fg-green font-bold uppercase tracking-widest opacity-80">Live</span>
        </div>
      </div>

      <div className="p-3.5 grid grid-cols-2 gap-2.5 relative bg-[#0b1120]">
        {/* Subtle internal grid depth */}
        <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(circle_at_center,_white_1px,_transparent_1px)] bg-[length:12px_12px] pointer-events-none"></div>

        {/* Main Metric */}
        <div className="col-span-2 bg-white/[0.03] border border-white/5 rounded-xl p-3 relative z-10 hover:bg-white/[0.04] transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] text-white/50 font-bold tracking-widest uppercase">Active Fleet</span>
            <Activity className="w-3.5 h-3.5 text-fg-green opacity-80" />
          </div>
          <div className="flex items-end gap-3">
             <div className="text-3xl font-light text-white tracking-tight leading-none">248</div>
             <div className="text-[10px] text-fg-green font-semibold mb-1">+12 today</div>
          </div>
        </div>

        {/* Sub Metrics */}
        <div className="bg-white/[0.03] border border-white/5 rounded-xl p-3 relative z-10">
          <div className="text-[8px] text-white/50 font-bold uppercase tracking-widest mb-1.5">Trips On Time</div>
          <div className="text-base font-semibold text-white/95">98.4%</div>
        </div>

        <div className="bg-white/[0.03] border border-white/5 rounded-xl p-3 relative z-10">
          <div className="text-[8px] text-white/50 font-bold uppercase tracking-widest mb-1.5">Active Alerts</div>
          <div className="flex items-center gap-2">
            <span className="text-base font-semibold text-fg-red">3</span>
            <ShieldAlert className="w-3.5 h-3.5 text-fg-red opacity-80" />
          </div>
        </div>

        {/* Live Signals Row */}
        <div className="col-span-2 bg-white/[0.03] border border-white/5 rounded-xl p-3 mt-1 relative z-10">
          <div className="flex items-center justify-between mb-3">
            <div className="text-[9px] text-white/50 font-bold uppercase tracking-widest">Live Operations</div>
            <div className="text-[8px] text-white/40 uppercase tracking-wider font-semibold">Past 1h</div>
          </div>
          <div className="flex flex-col gap-2.5">
            <div className="flex items-center justify-between gap-3">
              <span className="text-[9px] text-white/70 w-12 font-medium tracking-wide">Fueling</span>
              <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div className="h-full bg-amber-500 rounded-full" initial={{ width: 0 }} whileInView={{ width: '65%' }} transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}></motion.div>
              </div>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-[9px] text-white/70 w-12 font-medium tracking-wide">Dispatch</span>
              <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div className="h-full bg-blue-500 rounded-full" initial={{ width: 0 }} whileInView={{ width: '85%' }} transition={{ duration: 1, delay: 0.7, ease: "easeOut" }}></motion.div>
              </div>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-[9px] text-white/70 w-12 font-medium tracking-wide">Maint.</span>
              <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div className="h-full bg-fg-red rounded-full" initial={{ width: 0 }} whileInView={{ width: '20%' }} transition={{ duration: 1, delay: 0.9, ease: "easeOut" }}></motion.div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function ContinuousConnectionGraph() {
  const reducedMotion = useReducedMotion();
  const nodeX = 420; // 42% of 1000
  const nodeY = 300; // 50% of 600

  return (
    <svg viewBox="0 0 1000 600" preserveAspectRatio="none" className="absolute inset-0 w-full h-full pointer-events-none z-10">
       <defs>
         <linearGradient id="fadeLine" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#cbd5e1" stopOpacity="0" />
            <stop offset="40%" stopColor="#cbd5e1" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#cbd5e1" stopOpacity="0.1" />
         </linearGradient>
       </defs>

       {/* Source to Node flows */}
       {SPATIAL_SOURCES.map((s, i) => {
         const x1 = s.pos.x * 10;
         const y1 = s.pos.y * 6;

         // Smooth converging routing
         const cp1x = x1 + (nodeX - x1) * 0.4;
         const cp1y = y1;
         const cp2x = nodeX - (nodeX - x1) * 0.2;
         const cp2y = nodeY;

         const pathData = `M ${x1},${y1} C ${cp1x},${cp1y} ${cp2x},${cp2y} ${nodeX},${nodeY}`;

         return (
           <g key={i}>
             {/* Base ambient track */}
             <motion.path
               d={pathData}
               fill="none"
               stroke="url(#fadeLine)"
               strokeWidth="1.5"
               initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
               whileInView={{ pathLength: 1 }}
               viewport={{ once: true, margin: "-50px" }}
               transition={{ duration: 1.5, delay: s.delay, ease: "easeInOut" }}
             />
             {/* Continuous subtle data pulses */}
             {!reducedMotion && (
               <motion.path
                 d={pathData}
                 fill="none"
                 stroke="#4ADE80"
                 strokeWidth="2"
                 strokeLinecap="round"
                 opacity="0.5"
                 initial={{ pathLength: 0.015, pathOffset: 0, opacity: 0 }}
                 whileInView={{ opacity: 0.5 }}
                 animate={{ pathOffset: 1 }}
                 transition={{
                   pathOffset: { duration: 3.5, repeat: Infinity, ease: "linear", delay: s.delay + 1 },
                   opacity: { duration: 0.5, delay: s.delay + 1 }
                 }}
               />
             )}
           </g>
         )
       })}

       {/* Node to Dashboard resolution path - specifically terminates at 65% (x=650) */}
       <motion.path
          d={`M ${nodeX},${nodeY} L 650,${nodeY}`}
          fill="none"
          stroke="#4ADE80"
          strokeWidth="2"
          strokeDasharray="4 6"
          strokeOpacity="0.4"
          initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
          whileInView={{ pathLength: 1 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 1.2, delay: 1.5, ease: "easeOut" }}
       />

       {/* Central Convergence Intelligence Node */}
       <circle cx={nodeX} cy={nodeY} r="3" fill="#176B4D" className="opacity-90" />
       <circle cx={nodeX} cy={nodeY} r="3" fill="#4ADE80" className="animate-ping" opacity="0.6" style={{ transformOrigin: `${nodeX}px ${nodeY}px` }} />
    </svg>
  );
}

function VisualEcosystemCanvas() {
  return (
    <div className="relative w-full aspect-[4/5] sm:aspect-[4/3] lg:aspect-[16/9] max-h-[600px] flex items-center justify-center">
      {/* Extreme subtle background depth */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_40%_50%,_#e2e8f0_1px,_transparent_1px)] bg-[length:32px_32px] opacity-[0.25] pointer-events-none z-0"></div>

      <ContinuousConnectionGraph />

      {SPATIAL_SOURCES.map((source, idx) => (
        <SignalModule key={source.id} data={source} index={idx} />
      ))}

      <FleetContextGraph
         className="absolute"
         style={{ left: '42%', top: '50%', transform: 'translate(-50%, -50%)' }}
      />
      <OperationalDashboard
         className="absolute"
         style={{ left: '68%', top: '50%', transform: 'translateY(-50%)' }}
      />
    </div>
  );
}

// ============================================================================
// COMPONENTS - MOBILE FALLBACK
// ============================================================================

function MobileSignalModule({ data }) {
  return (
    <div className="flex items-center gap-2.5 p-2 bg-[#fdfdfc] border border-border/40 rounded-xl shadow-[0_2px_4px_rgba(0,0,0,0.01)] w-full">
      <div className={`shrink-0 w-8 h-8 rounded-lg bg-white border border-border/30 shadow-sm flex items-center justify-center ${data.color}`}>
        <data.icon className="w-3.5 h-3.5 opacity-80" strokeWidth={1.5} />
      </div>
      <div className="min-w-0">
        <div className="text-[11px] font-bold text-content tracking-wider uppercase leading-none mb-0.5">{data.label}</div>
        <div className="text-[9px] text-content-muted leading-tight truncate">{data.sub}</div>
      </div>
    </div>
  );
}

function MobileVisualFallback() {
  return (
    <div className="flex flex-col items-center gap-10 py-8 w-full max-w-sm mx-auto">
      <div className="w-full grid grid-cols-2 gap-3">
        {SPATIAL_SOURCES.slice(0, 6).map((source) => (
          <MobileSignalModule key={source.id} data={source} />
        ))}
      </div>

      <div className="flex justify-center -my-6 text-border/60">
         <ArrowDown className="w-5 h-5" strokeWidth={1.5} />
      </div>

      <div className="relative transform scale-90 -my-8 mx-auto w-fit">
        <FleetContextGraph />
      </div>

      <div className="flex justify-center -my-6 text-border/60">
         <ArrowDown className="w-5 h-5" strokeWidth={1.5} />
      </div>

      <div className="w-full relative transform scale-95 origin-top flex justify-center">
        <OperationalDashboard />
      </div>
    </div>
  );
}


// ============================================================================
// MAIN EXPORT
// ============================================================================

export function ChallengeSection() {
  return (
    <section className="py-16 md:py-20 bg-[#fafaf9] overflow-hidden relative">
      <div className="container mx-auto px-6 max-w-[1440px]">
        <div className="flex flex-col xl:flex-row items-center xl:items-start gap-16 xl:gap-8">

          {/* Left: Copy & Metrics */}
          <div className="w-full xl:w-[32%] xl:pt-16 flex flex-col justify-between relative z-40">
            <ChallengeCopy />
            <ChallengeMetrics />
          </div>

          {/* Right: Visualization Canvas (Desktop only) */}
          <div className="hidden md:block w-full xl:w-[68%]">
            <VisualEcosystemCanvas />
          </div>

          {/* Right: Visualization Stack (Mobile only) */}
          <div className="block md:hidden w-full">
            <MobileVisualFallback />
          </div>

        </div>
      </div>
    </section>
  );
}
