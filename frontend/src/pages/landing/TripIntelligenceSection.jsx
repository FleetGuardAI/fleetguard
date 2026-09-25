import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { 
  ArrowRight, 
  CheckCircle2, 
  Navigation2
} from 'lucide-react';

// ============================================================================
// ANIMATION VARIANTS
// ============================================================================
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.2 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" }
  }
};

const routeLineVariants = {
  hidden: { scaleX: 0 },
  visible: { 
    scaleX: 1, 
    transition: { duration: 1, ease: "easeInOut", delay: 0.4 } 
  }
};

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

function TripHeader() {
  return (
    <motion.div variants={itemVariants} className="flex items-center justify-between pb-4 border-b border-border/60">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center shadow-sm">
          <Navigation2 className="w-4 h-4 text-content-secondary" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-content tracking-tight leading-none mb-1">Trip #0402</h3>
          <p className="text-[10px] text-content-muted font-bold tracking-widest uppercase">DEL-JAI-9901</p>
        </div>
      </div>
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-fg-green/10 border border-fg-green/20">
        <CheckCircle2 className="w-3.5 h-3.5 text-fg-green-deep" />
        <span className="text-[10px] font-bold uppercase tracking-wider text-fg-green-deep">Completed</span>
      </div>
    </motion.div>
  );
}

function RouteVisual() {
  const reducedMotion = useReducedMotion();
  
  return (
    <motion.div variants={itemVariants} className="py-5 flex flex-col gap-4">
      {/* Route Nodes */}
      <div className="flex items-center justify-between relative px-2">
        {/* Connection Line */}
        <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 h-[2px] bg-slate-100 overflow-hidden">
          <motion.div 
            className="w-full h-full bg-slate-300 origin-left"
            variants={routeLineVariants}
          />
        </div>

        <div className="flex flex-col items-start gap-2 relative z-10 bg-white pr-4">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-800 border-2 border-white ring-1 ring-border shadow-sm"></div>
            <span className="text-[13px] font-bold text-content">Delhi</span>
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-2 relative z-10 bg-white pl-4">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-bold text-content">Jaipur</span>
            <div className="w-2.5 h-2.5 rounded-full bg-fg-green border-2 border-white ring-1 ring-border shadow-sm"></div>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="flex items-center justify-between bg-surface-secondary border border-border/50 rounded-lg p-3">
        <div className="flex flex-col gap-0.5">
           <span className="text-[9px] text-content-muted uppercase tracking-widest font-bold">Distance</span>
           <span className="text-xs font-semibold text-content">524 km</span>
        </div>
        <div className="w-px h-6 bg-border/60"></div>
        <div className="flex flex-col gap-0.5">
           <span className="text-[9px] text-content-muted uppercase tracking-widest font-bold">Planned Time</span>
           <span className="text-xs font-semibold text-content">8h 20m</span>
        </div>
        <div className="w-px h-6 bg-border/60"></div>
        <div className="flex flex-col items-end gap-0.5">
           <span className="text-[9px] text-amber-600 uppercase tracking-widest font-bold">Actual Time</span>
           <span className="text-xs font-bold text-amber-700">10h 20m</span>
        </div>
      </div>
    </motion.div>
  );
}

function EconomicsSummary() {
  return (
    <motion.div variants={itemVariants} className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-5 border-y border-border/60">
      <div className="flex flex-col gap-1">
        <span className="text-[9px] text-content-muted uppercase tracking-widest font-bold">Revenue</span>
        <span className="text-[17px] font-semibold text-content tracking-tight">₹18,500</span>
      </div>
      <div className="flex flex-col gap-1 sm:border-l sm:border-border/60 sm:pl-4">
        <span className="text-[9px] text-content-muted uppercase tracking-widest font-bold">Total Cost</span>
        <span className="text-[17px] font-semibold text-content tracking-tight">₹13,680</span>
      </div>
      <div className="flex flex-col gap-1 sm:border-l sm:border-border/60 sm:pl-4">
        <span className="text-[9px] text-fg-green-deep uppercase tracking-widest font-bold">Net Profit</span>
        <span className="text-[17px] font-bold text-fg-green-deep tracking-tight">₹4,820</span>
      </div>
      <div className="flex flex-col gap-1 sm:border-l sm:border-border/60 sm:pl-4">
        <span className="text-[9px] text-content-muted uppercase tracking-widest font-bold">Margin</span>
        <span className="text-[17px] font-bold text-content tracking-tight">26%</span>
      </div>
    </motion.div>
  );
}

function CostBreakdown() {
  const reducedMotion = useReducedMotion();
  // Cost data: Total 13680
  const fuel = (8200 / 13680) * 100; // ~60%
  const driver = (2000 / 13680) * 100; // ~15%
  const tolls = (2100 / 13680) * 100; // ~15%
  const other = (1380 / 13680) * 100; // ~10%

  return (
    <motion.div variants={itemVariants} className="pt-5 flex flex-col gap-3">
      <div className="flex justify-between items-end mb-1">
        <h4 className="text-[10px] font-bold text-content uppercase tracking-widest">Cost Breakdown</h4>
        <span className="text-[11px] font-semibold text-content-secondary">₹13,680</span>
      </div>

      {/* Stacked Bar */}
      <div className="h-4 w-full rounded-md overflow-hidden flex bg-surface">
        <motion.div 
          className="h-full bg-amber-400 border-r border-white/20"
          initial={reducedMotion ? { width: `${fuel}%` } : { width: 0 }}
          whileInView={{ width: `${fuel}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 0.8 }}
        />
        <motion.div 
          className="h-full bg-slate-400 border-r border-white/20"
          initial={reducedMotion ? { width: `${driver}%` } : { width: 0 }}
          whileInView={{ width: `${driver}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 0.9 }}
        />
        <motion.div 
          className="h-full bg-slate-300 border-r border-white/20"
          initial={reducedMotion ? { width: `${tolls}%` } : { width: 0 }}
          whileInView={{ width: `${tolls}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 1.0 }}
        />
        <motion.div 
          className="h-full bg-slate-200"
          initial={reducedMotion ? { width: `${other}%` } : { width: 0 }}
          whileInView={{ width: `${other}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 1.1 }}
        />
      </div>

      {/* Legend */}
      <div className="grid grid-cols-4 gap-2 mt-1">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-sm bg-amber-400"></div>
            <span className="text-[9px] text-content-secondary uppercase font-bold tracking-widest">Fuel</span>
          </div>
          <span className="text-[11px] font-semibold text-content">₹8,200</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-sm bg-slate-400"></div>
            <span className="text-[9px] text-content-secondary uppercase font-bold tracking-widest">Driver</span>
          </div>
          <span className="text-[11px] font-semibold text-content">₹2,000</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-sm bg-slate-300"></div>
            <span className="text-[9px] text-content-secondary uppercase font-bold tracking-widest">Tolls</span>
          </div>
          <span className="text-[11px] font-semibold text-content">₹2,100</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-sm bg-slate-200"></div>
            <span className="text-[9px] text-content-secondary uppercase font-bold tracking-widest">Other</span>
          </div>
          <span className="text-[11px] font-semibold text-content">₹1,380</span>
        </div>
      </div>
    </motion.div>
  );
}

// ============================================================================
// MAIN EXPORT
// ============================================================================

export function TripIntelligenceSection() {
  return (
    <section className="py-20 lg:py-24 bg-[#fdfcfb] overflow-hidden">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex flex-col lg:flex-row gap-12 lg:gap-16 items-center">
          
          {/* Left Column: Editorial (45%) */}
          <div className="w-full lg:w-[45%] space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-6 h-[1px] bg-fg-green"></div>
              <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green">Trip Intelligence</span>
            </div>
            
            <h2 className="text-3xl md:text-4xl font-medium tracking-tight leading-[1.1] text-content max-w-md">
              Every trip has an <span className="text-fg-green">economics story.</span>
            </h2>
            
            <p className="text-[15px] text-content-secondary font-light leading-relaxed max-w-[400px]">
              Go beyond tracking. Understand trip profitability, efficiency, and cost drivers before, during, and after the trip.
            </p>

            <button className="flex items-center text-[12px] font-semibold text-fg-green hover:text-fg-green-deep transition-colors group pt-2">
              See Trip Intelligence
              <ArrowRight className="w-3.5 h-3.5 ml-1.5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* Right Column: Trip Economics Console (55%) */}
          <div className="w-full lg:w-[55%] relative">
            {/* Subtle background glow */}
            <div className="absolute inset-0 bg-fg-green/5 blur-[60px] -z-10 rounded-[30px] translate-x-8 translate-y-8"></div>
            
            <motion.div 
              variants={containerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="bg-white border border-border shadow-[0_12px_24px_-12px_rgba(0,0,0,0.06)] rounded-2xl p-6 w-full max-w-[500px] mx-auto lg:ml-auto lg:mr-0 overflow-hidden"
            >
              <TripHeader />
              <RouteVisual />
              <EconomicsSummary />
              <CostBreakdown />
            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
