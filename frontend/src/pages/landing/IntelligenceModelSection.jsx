import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { 
  ArrowRight, 
  Map, Truck, Droplets, Users, Receipt, FileText, Wrench,
  ShieldCheck, Settings, Sparkles, Navigation2, AlertTriangle, IndianRupee, TrendingDown
} from 'lucide-react';

// ============================================================================
// DATA CONFIGURATION (PHASE 4B: COLUMNAR COMPOSITION)
// ============================================================================

const STAGES = [
  { num: '1', title: 'RAW DATA', desc: 'Multiple sources', pos: 10 },
  { num: '2', title: 'CONTEXT', desc: 'Connects the dots', pos: 40 },
  { num: '3', title: 'INTELLIGENCE', desc: 'Finds what matters', pos: 60 },
  { num: '4', title: 'BUSINESS IMPACT', desc: 'Shows consequences', pos: 75 },
  { num: '5', title: 'ACTION', desc: 'Helps you decide', pos: 95 }
];

// COLUMN A: DATA SOURCES (Clustered)
const DATA_SOURCES = [
  { id: 'trips', label: 'Trips', icon: Map, color: 'text-slate-400', pos: { x: 5, y: 35 }, delay: 0.1 },
  { id: 'vehicles', label: 'Vehicles', icon: Truck, color: 'text-slate-400', pos: { x: 15, y: 35 }, delay: 0.2 },
  { id: 'drivers', label: 'Drivers', icon: Users, color: 'text-slate-400', pos: { x: 5, y: 48 }, delay: 0.3 },
  { id: 'expenses', label: 'Expenses', icon: Receipt, color: 'text-slate-400', pos: { x: 15, y: 48 }, delay: 0.4 },
  { id: 'documents', label: 'Documents', icon: FileText, color: 'text-slate-400', pos: { x: 5, y: 61 }, delay: 0.5 },
  { id: 'maintenance', label: 'Maintenance', icon: Wrench, color: 'text-slate-400', pos: { x: 15, y: 61 }, delay: 0.6 },
  { id: 'fuel', label: 'Fuel Cards', icon: Droplets, color: 'text-amber-500', pos: { x: 20, y: 75 }, delay: 0.7, isAnomaly: true }
];

// COLUMN B: CONTEXT (Anchor)
const TRUCK_POS = { x: 40, y: 45 };
const ANOMALY_POS = { x: 40, y: 75 };

const CONTEXT_FRAGMENTS = [
  { id: 'c-driver', label: 'Driver: Ravi Kumar', pos: { x: 30, y: 32 }, delay: 0.8 },
  { id: 'c-history', label: 'History: Pattern deviation', pos: { x: 30, y: 38 }, delay: 1.0 },
];

// COLUMN C: INTELLIGENCE
const INTELLIGENCE_MODULES = [
  { id: 'i-trip', label: 'Trip Intelligence', sub: 'route economics', icon: Navigation2, pos: { x: 62, y: 32 }, delay: 1.6 },
  { id: 'i-verify', label: 'Verification', sub: 'expense consistency', icon: ShieldCheck, pos: { x: 62, y: 46 }, delay: 1.7 },
  { id: 'i-ops', label: 'Operations Engine', sub: 'translates anomaly', icon: Settings, pos: { x: 62, y: 60 }, delay: 1.9 },
  { id: 'i-copilot', label: 'AI Copilot', sub: 'explains & recommends', icon: Sparkles, pos: { x: 62, y: 74 }, delay: 1.8 }
];

// COLUMN D: IMPACT & DASHBOARD
const IMPACT_POS = { x: 72, y: 60 };
const DASHBOARD_POS = { x: 100, y: 50 };

// ============================================================================
// COMPONENTS
// ============================================================================

function ProcessBar() {
  return (
    <div className="absolute top-6 left-0 right-0 z-40 pointer-events-none">
      {STAGES.map((stage, i) => (
        <div key={i} className="absolute flex flex-col" style={{ left: `${stage.pos}%`, transform: stage.pos === 100 ? 'translateX(-100%)' : 'translateX(-50%)' }}>
          <div className="text-[9px] font-bold tracking-widest uppercase text-content mb-0.5 whitespace-nowrap">
            <span className="text-content-muted mr-1">{stage.num}.</span> {stage.title}
          </div>
          <div className="text-[8px] text-content-muted">{stage.desc}</div>
        </div>
      ))}
    </div>
  );
}

function SourceLabel({ data }) {
  const reducedMotion = useReducedMotion();
  return (
    <motion.div
      className="absolute flex items-center gap-1.5 z-30"
      style={{ top: `${data.pos.y}%`, left: `${data.pos.x}%`, transform: 'translateY(-50%)' }}
      initial={reducedMotion ? { opacity: 1 } : { opacity: 0, x: -10 }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: data.delay, ease: "easeOut" }}
      viewport={{ once: true, margin: "-50px" }}
    >
      <data.icon className={`w-3.5 h-3.5 ${data.color}`} strokeWidth={2} />
      <span className={`text-[10px] font-medium leading-none ${data.isAnomaly ? 'text-amber-600 font-bold' : 'text-content-muted'}`}>{data.label}</span>
      <div className={`absolute -right-3 top-1/2 -translate-y-1/2 w-1 h-1 rounded-full ${data.isAnomaly ? 'bg-amber-500' : 'bg-slate-300'}`}></div>
    </motion.div>
  );
}

function ContextFragment({ data }) {
  const reducedMotion = useReducedMotion();
  return (
    <motion.div
      className="absolute bg-white/80 backdrop-blur-sm border border-border/40 rounded px-1.5 py-1 shadow-sm z-30"
      style={{ top: `${data.pos.y}%`, left: `${data.pos.x}%`, transform: 'translate(-50%, -50%)' }}
      initial={reducedMotion ? { opacity: 1 } : { opacity: 0, scale: 0.95 }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, delay: data.delay, ease: "easeOut" }}
      viewport={{ once: true, margin: "-50px" }}
    >
      <span className="text-[8px] text-content-secondary font-medium tracking-wide uppercase">{data.label}</span>
    </motion.div>
  );
}

function ActiveTripAnchor() {
  const reducedMotion = useReducedMotion();
  return (
    <div className="absolute inset-0 pointer-events-none z-40">
       <motion.div 
         className="absolute flex flex-col bg-[#0f172a] rounded-xl p-3 shadow-xl border border-border/20 z-40 w-[140px]"
         style={{ top: `${TRUCK_POS.y}%`, left: `${TRUCK_POS.x}%`, transform: 'translate(-50%, -50%)' }}
         initial={reducedMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
         whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
         transition={{ duration: 0.6, delay: 0.8 }}
         viewport={{ once: true }}
       >
         {/* Header */}
         <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
           <div className="flex items-center gap-1.5">
             <div className="relative w-5 h-5 bg-fg-green/10 rounded flex items-center justify-center border border-fg-green/20">
               <Truck className="w-3 h-3 text-fg-green" />
               <div className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-fg-green animate-pulse"></div>
             </div>
             <span className="text-[10px] font-bold text-white tracking-wide">MH-04-1234</span>
           </div>
           <span className="text-[8px] text-emerald-400 font-bold uppercase tracking-wider">Active</span>
         </div>
         {/* Route */}
         <div className="flex flex-col gap-1">
           <div className="flex items-center justify-between">
             <span className="text-[9px] font-medium text-white/90">Delhi</span>
             <ArrowRight className="w-3 h-3 text-white/40" />
             <span className="text-[9px] font-medium text-white/90">Jaipur</span>
           </div>
           <div className="flex items-center justify-between mt-1">
             <span className="text-[8px] text-white/50 uppercase tracking-widest">Status</span>
             <span className="text-[8px] text-white/80 font-medium">On Time</span>
           </div>
         </div>
       </motion.div>
    </div>
  );
}

function AnomalyEvent() {
  const reducedMotion = useReducedMotion();
  return (
    <motion.div 
       className="absolute flex items-start gap-2 bg-[#fffbeb] border border-amber-200 rounded-lg p-2 shadow-sm z-40 w-[130px]"
       style={{ top: `${ANOMALY_POS.y}%`, left: `${ANOMALY_POS.x}%`, transform: 'translate(-50%, -50%)' }}
       initial={reducedMotion ? { opacity: 1 } : { opacity: 0, scale: 0.9 }}
       whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
       transition={{ duration: 0.5, delay: 1.3, type: 'spring' }}
       viewport={{ once: true }}
    >
      <div className="w-5 h-5 rounded bg-amber-100 flex items-center justify-center shrink-0">
        <AlertTriangle className="w-3 h-3 text-amber-600" />
      </div>
      <div className="flex flex-col">
        <span className="text-[9px] font-bold text-amber-900 leading-tight">Fuel variance</span>
        <span className="text-[8px] text-amber-700/80 leading-tight mt-0.5">45L unexpected drop</span>
      </div>
    </motion.div>
  );
}

function IntelligenceLayer({ data }) {
  const reducedMotion = useReducedMotion();
  return (
    <motion.div
      className="absolute flex items-center gap-2 bg-white border border-border/60 rounded-lg p-1.5 pr-2.5 shadow-sm z-40"
      style={{ top: `${data.pos.y}%`, left: `${data.pos.x}%`, transform: 'translate(-50%, -50%)' }}
      initial={reducedMotion ? { opacity: 1 } : { opacity: 0, x: -10 }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: data.delay, ease: "easeOut" }}
      viewport={{ once: true, margin: "-50px" }}
    >
      <div className="w-6 h-6 rounded bg-[#fafaf9] border border-border/40 flex items-center justify-center text-slate-600">
        <data.icon className="w-3 h-3" strokeWidth={1.5} />
      </div>
      <div className="flex flex-col">
        <span className="text-[9px] font-bold text-content leading-none mb-0.5">{data.label}</span>
        <span className="text-[7px] text-content-muted leading-none uppercase tracking-wider">{data.sub}</span>
      </div>
    </motion.div>
  );
}

function BusinessImpactTag() {
  const reducedMotion = useReducedMotion();
  return (
    <motion.div 
      className="absolute flex flex-col gap-1 bg-white border border-red-100 rounded-lg p-2 shadow-md z-40 w-[110px]"
      style={{ top: `${IMPACT_POS.y}%`, left: `${IMPACT_POS.x}%`, transform: 'translate(-50%, -50%)' }}
      initial={reducedMotion ? { opacity: 1 } : { opacity: 0, scale: 0.9 }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 2.2, type: 'spring' }}
      viewport={{ once: true }}
    >
       <span className="text-[8px] font-bold uppercase tracking-widest text-red-800 border-b border-red-50 pb-1 mb-0.5">Impact</span>
       <div className="flex items-center justify-between">
         <span className="text-[9px] text-content-secondary">Fuel Cost</span>
         <span className="text-[10px] font-bold text-red-600">+₹4,500</span>
       </div>
       <div className="flex items-center justify-between">
         <span className="text-[9px] text-content-secondary">Margin</span>
         <div className="flex items-center gap-0.5">
           <TrendingDown className="w-2.5 h-2.5 text-red-500" />
           <span className="text-[10px] font-bold text-red-600">5%</span>
         </div>
       </div>
    </motion.div>
  );
}

function OperationalDashboard() {
  const reducedMotion = useReducedMotion();
  return (
    <motion.div 
      className="absolute right-0 z-50 flex flex-col bg-[#0b1120] border border-[#1e293b] rounded-xl shadow-[0_20px_40px_-10px_rgba(0,0,0,0.5)] overflow-hidden w-[260px]"
      style={{ top: `${DASHBOARD_POS.y}%`, transform: 'translateY(-50%)' }}
      initial={reducedMotion ? { opacity: 1, x: 0 } : { opacity: 0, x: 20 }}
      whileInView={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 2.5, ease: "easeOut" }}
      viewport={{ once: true, margin: "-50px" }}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-[#1e293b] flex items-center justify-between bg-[#020617]/90 backdrop-blur">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-[3px] bg-fg-green flex items-center justify-center">
            <span className="text-[7px] font-bold text-[#0b1120] leading-none">V</span>
          </div>
          <span className="text-[10px] font-semibold text-white/90 tracking-tight">the vaahan</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-fg-green/90 animate-pulse"></div>
          <span className="text-[7px] text-white/80 font-medium uppercase tracking-wider">Signals</span>
        </div>
      </div>
      
      <div className="p-3 bg-[#0b1120] flex flex-col gap-3">
        {/* Top Metrics */}
        <div className="grid grid-cols-3 gap-2">
          <div className="flex flex-col gap-0.5">
            <span className="text-[7px] text-white/50 uppercase font-bold tracking-wider">Active</span>
            <span className="text-[12px] font-semibold text-white">248</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[7px] text-white/50 uppercase font-bold tracking-wider">On Time</span>
            <span className="text-[12px] font-semibold text-white">98%</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[7px] text-white/50 uppercase font-bold tracking-wider">Alerts</span>
            <span className="text-[12px] font-semibold text-fg-red">4</span>
          </div>
        </div>

        {/* Highlighted Alert Box */}
        <div className="bg-red-950/30 border border-red-900/40 rounded p-2 flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-3 h-3 text-red-500" />
            <span className="text-[9px] font-semibold text-red-400">Variance • MH-04-1234</span>
          </div>
          <div className="flex justify-between items-center">
             <span className="text-[8px] text-white/60">45L unexpected drop</span>
             <span className="text-[8px] font-bold text-red-400">₹4,500 RISK</span>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="flex flex-col gap-1 pt-1 border-t border-white/5">
          <span className="text-[7px] text-white/40 uppercase font-bold mb-0.5">Activity</span>
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 bg-fg-green rounded-full"></div>
            <span className="text-[8px] text-white/70">Vehicle UP-16-9900 crossed border</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function ContinuousConnectionGraph() {
  const reducedMotion = useReducedMotion();
  // Using viewBox 0 0 100 100 allows SVG coordinates to perfectly match HTML % left/top
  const tx = TRUCK_POS.x; 
  const ty = TRUCK_POS.y;
  const ax = ANOMALY_POS.x;
  const ay = ANOMALY_POS.y;
  const ix = IMPACT_POS.x;
  const iy = IMPACT_POS.y;
  const dx = 83; // left edge of dashboard
  
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full pointer-events-none z-10">
      <defs>
        <linearGradient id="lineFade" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#cbd5e1" stopOpacity="0" />
          <stop offset="20%" stopColor="#cbd5e1" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#cbd5e1" stopOpacity="0.1" />
        </linearGradient>
      </defs>

      {/* 1. Spine connecting Source Inputs to Active Trip */}
      <motion.path 
        d={`M 15,${ty} L ${tx - 5},${ty}`}
        fill="none" stroke="#cbd5e1" strokeWidth="0.15"
        initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1, delay: 0.5 }}
      />

      {/* 2. Context Sources feeding the Spine */}
      {DATA_SOURCES.filter(s => !s.isAnomaly).map((source, i) => {
        const sx = source.pos.x + 5; 
        const sy = source.pos.y;
        
        // Orthogonal/Curved routing to spine
        const path = `M ${sx},${sy} C ${sx + 5},${sy} 15,${ty} 20,${ty}`;
        
        return (
          <g key={i}>
            <motion.path 
              d={path}
              fill="none" stroke="url(#lineFade)" strokeWidth="0.1"
              initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1, delay: source.delay }}
            />
          </g>
        )
      })}

      {/* 3. Fuel Source feeding the Anomaly Event */}
      {(() => {
        const fuel = DATA_SOURCES.find(s => s.isAnomaly);
        const sx = fuel.pos.x + 5;
        const sy = fuel.pos.y;
        const path = `M ${sx},${sy} L ${ax - 5},${ay}`;
        return (
          <motion.path 
              d={path}
              fill="none" stroke="#F59E0B" strokeWidth="0.15" strokeDasharray="0.5 0.5" opacity="0.6"
              initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: fuel.delay }}
            />
        )
      })()}
      
      {/* 4. Truck feeding Intelligence Modules (Spine out) */}
      <motion.path 
        d={`M ${tx + 5},${ty} L 55,${ty}`}
        fill="none" stroke="#cbd5e1" strokeWidth="0.15"
        initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 1.2 }}
      />

      {/* 5. Branching from Spine to Intelligence Modules */}
      {INTELLIGENCE_MODULES.map((mod, i) => {
        const mx = mod.pos.x - 5;
        const my = mod.pos.y;
        
        // Curve from central spine (or anomaly) to engines
        const startX = (mod.id === 'i-ops' || mod.id === 'i-copilot') ? ax + 5 : 55;
        const startY = (mod.id === 'i-ops' || mod.id === 'i-copilot') ? ay : ty;
        
        const path = `M ${startX},${startY} C ${startX + 5},${startY} ${mx - 2},${my} ${mx},${my}`;
        
        return (
           <motion.path key={i}
              d={path}
              fill="none" stroke="#cbd5e1" strokeWidth="0.15"
              initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 1.5 }}
            />
        )
      })}

      {/* 6. Intelligence to Business Impact */}
      <motion.path 
         d={`M 68,${ay} C 73,${ay} ${ix - 5},${iy} ${ix},${iy}`}
         fill="none" stroke="#ef4444" strokeWidth="0.15" strokeOpacity="0.3"
         initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
         whileInView={{ pathLength: 1 }}
         viewport={{ once: true }}
         transition={{ duration: 0.6, delay: 2.1 }}
       />

      {/* 7. Business Impact to Dashboard Output */}
      <motion.path 
         d={`M ${ix + 5},${iy} L ${dx},${iy}`}
         fill="none" stroke="#ef4444" strokeWidth="0.2" strokeOpacity="0.5"
         initial={reducedMotion ? { pathLength: 1 } : { pathLength: 0 }}
         whileInView={{ pathLength: 1 }}
         viewport={{ once: true }}
         transition={{ duration: 0.5, delay: 2.4 }}
       />
       
       {/* Pulse on the final output line */}
       {!reducedMotion && (
          <motion.path 
            d={`M ${ix + 5},${iy} L ${dx},${iy}`}
            fill="none" stroke="#ef4444" strokeWidth="0.3" strokeLinecap="round" opacity="0.8"
            initial={{ pathLength: 0.05, pathOffset: 0, opacity: 0 }}
            whileInView={{ opacity: 0.8 }}
            animate={{ pathOffset: 1 }}
            transition={{ 
              pathOffset: { duration: 1.5, repeat: Infinity, ease: "linear", delay: 2.8 },
              opacity: { duration: 0.5, delay: 2.8 }
            }}
          />
       )}
    </svg>
  );
}

// ============================================================================
// MAIN EXPORT
// ============================================================================

export function IntelligenceModelSection() {
  return (
    <section id="how-vaahan-works" className="py-24 bg-[#fdfcfb] overflow-hidden relative scroll-mt-24">
      <div className="container mx-auto px-6 max-w-[1440px] relative z-10">
        <div className="flex flex-col xl:flex-row gap-8">
          
          {/* Left Column: Editorial */}
          <div className="w-full xl:w-[25%] flex flex-col justify-between pt-16 relative z-50">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-6 h-[1px] bg-fg-green/60"></div>
                <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green">How the vaahan works</span>
              </div>
              
              <h2 className="text-4xl md:text-5xl lg:text-[50px] font-medium tracking-tight leading-[1.05] mb-6 text-content">
                From data to<br/>
                <span className="text-fg-green">decisions.</span>
              </h2>
              
              <p className="text-[15px] text-content-secondary font-light leading-relaxed mb-8">
                Your vaahan doesn't just collect data. It connects every piece of information, adds context, finds what matters, and helps you take action.
              </p>

              <button className="flex items-center text-[12px] font-semibold text-fg-green hover:text-fg-green-deep transition-colors group">
                See how the platform works
                <ArrowRight className="w-4 h-4 ml-1.5 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>

          {/* Right Column: Spatial Canvas (Desktop) */}
          <div className="hidden xl:block relative w-full xl:w-[75%] aspect-[16/9] max-h-[750px]">
            <ProcessBar />
            <ContinuousConnectionGraph />
            
            {/* Input Cluster (Col A) */}
            {DATA_SOURCES.map((source) => (
              <SourceLabel key={source.id} data={source} />
            ))}
            
            {/* Active Trip Anchor & Context (Col B) */}
            <ActiveTripAnchor />
            
            {CONTEXT_FRAGMENTS.map((frag) => (
              <ContextFragment key={frag.id} data={frag} />
            ))}
            
            <AnomalyEvent />

            {/* Intelligence Layers (Col C) */}
            {INTELLIGENCE_MODULES.map((mod) => (
              <IntelligenceLayer key={mod.id} data={mod} />
            ))}

            {/* Output (Col D) */}
            <BusinessImpactTag />
            <OperationalDashboard />
          </div>

          {/* Mobile Fallback */}
          <div className="block xl:hidden w-full mt-12 flex flex-col gap-12">
            <div className="flex flex-col gap-6">
               {STAGES.map((s, i) => (
                 <div key={i} className="flex flex-col p-4 bg-surface rounded-xl border border-border">
                   <span className="text-[10px] font-bold text-content uppercase tracking-wider">{s.num}. {s.title}</span>
                   <span className="text-[12px] text-content-muted mt-1">{s.desc}</span>
                 </div>
               ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
