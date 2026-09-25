import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { 
  ArrowRight, 
  CheckCircle2, 
  Sparkles, 
  TrendingDown,
  Navigation2,
  Clock,
  Droplets,
  AlertTriangle
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
    <motion.div variants={itemVariants} className="flex items-center justify-between pb-5 border-b border-border/50">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center shadow-sm">
          <Navigation2 className="w-4 h-4 text-content-secondary" />
        </div>
        <div>
          <h3 className="text-[15px] font-bold text-content tracking-tight leading-none mb-1">Trip #0402</h3>
          <p className="text-[11px] text-content-muted font-medium tracking-wide uppercase">ID: DEL-JAI-9901</p>
        </div>
      </div>
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 border border-emerald-100">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">Completed</span>
      </div>
    </motion.div>
  );
}

function RouteVisual() {
  const reducedMotion = useReducedMotion();
  
  return (
    <motion.div variants={itemVariants} className="py-6 flex flex-col gap-4">
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
            <div className="w-3 h-3 rounded-full bg-content border-[2.5px] border-white ring-1 ring-border shadow-sm"></div>
            <span className="text-sm font-bold text-content">Delhi</span>
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-2 relative z-10 bg-white pl-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-content">Jaipur</span>
            <div className="w-3 h-3 rounded-full bg-emerald-500 border-[2.5px] border-white ring-1 ring-border shadow-sm"></div>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="flex items-center justify-center gap-8 mt-1">
        <div className="flex flex-col items-center gap-0.5">
           <span className="text-[10px] text-content-muted uppercase tracking-widest font-bold">Distance</span>
           <span className="text-xs font-semibold text-content">524 km</span>
        </div>
        <div className="w-px h-6 bg-border"></div>
        <div className="flex flex-col items-center gap-0.5">
           <span className="text-[10px] text-content-muted uppercase tracking-widest font-bold">Planned</span>
           <span className="text-xs font-semibold text-content">8h 20m</span>
        </div>
        <div className="w-px h-6 bg-border"></div>
        <div className="flex flex-col items-center gap-0.5">
           <span className="text-[10px] text-amber-600 uppercase tracking-widest font-bold">Actual</span>
           <span className="text-xs font-bold text-amber-700">10h 20m</span>
        </div>
      </div>
    </motion.div>
  );
}

function EconomicsSummary() {
  return (
    <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4 py-6 border-y border-border/50 bg-[#fafaf9] -mx-8 px-8">
      <div className="flex flex-col gap-1">
        <span className="text-[10px] text-content-muted uppercase tracking-widest font-bold">Revenue</span>
        <span className="text-xl font-medium text-content tracking-tight">₹18,500</span>
      </div>
      <div className="flex flex-col gap-1 border-l border-border/60 pl-4">
        <span className="text-[10px] text-content-muted uppercase tracking-widest font-bold">Total Cost</span>
        <span className="text-xl font-medium text-content tracking-tight">₹13,680</span>
      </div>
      <div className="flex flex-col gap-1 border-l border-border/60 pl-4">
        <span className="text-[10px] text-emerald-700 uppercase tracking-widest font-bold flex items-center gap-1.5">Net Profit</span>
        <span className="text-2xl font-bold text-emerald-700 tracking-tight">₹4,820</span>
      </div>
      <div className="flex flex-col gap-1 border-l border-border/60 pl-4">
        <span className="text-[10px] text-content-muted uppercase tracking-widest font-bold">Margin</span>
        <span className="text-2xl font-bold text-content tracking-tight">26%</span>
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
    <motion.div variants={itemVariants} className="py-6 flex flex-col gap-4">
      <div className="flex justify-between items-end mb-1">
        <h4 className="text-[11px] font-bold text-content uppercase tracking-widest">Cost Breakdown</h4>
        <span className="text-xs font-semibold text-content-secondary">₹13,680</span>
      </div>

      {/* Stacked Bar */}
      <div className="h-6 w-full rounded-md overflow-hidden flex bg-surface">
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-[2px] bg-amber-400"></div>
            <span className="text-[10px] text-content-secondary uppercase font-bold tracking-wider">Fuel</span>
          </div>
          <span className="text-[13px] font-semibold text-content">₹8,200</span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-[2px] bg-slate-400"></div>
            <span className="text-[10px] text-content-secondary uppercase font-bold tracking-wider">Driver</span>
          </div>
          <span className="text-[13px] font-semibold text-content">₹2,000</span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-[2px] bg-slate-300"></div>
            <span className="text-[10px] text-content-secondary uppercase font-bold tracking-wider">Tolls</span>
          </div>
          <span className="text-[13px] font-semibold text-content">₹2,100</span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-[2px] bg-slate-200"></div>
            <span className="text-[10px] text-content-secondary uppercase font-bold tracking-wider">Other</span>
          </div>
          <span className="text-[13px] font-semibold text-content">₹1,380</span>
        </div>
      </div>
    </motion.div>
  );
}

function ExpectedVsActual() {
  return (
    <motion.div variants={itemVariants} className="grid grid-cols-2 gap-4 pb-6 border-b border-border/50">
      {/* Expected */}
      <div className="flex flex-col p-4 bg-surface rounded-xl border border-border/60">
        <span className="text-[10px] font-bold text-content-muted uppercase tracking-widest mb-3">Expected</span>
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <span className="text-[11px] text-content-secondary">Fuel Cost</span>
            <span className="text-[11px] font-medium text-content">₹7,100</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[11px] text-content-secondary">Trip Time</span>
            <span className="text-[11px] font-medium text-content">8h 20m</span>
          </div>
          <div className="h-px bg-border my-1"></div>
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-bold text-content">Margin</span>
            <span className="text-[11px] font-bold text-emerald-600">31%</span>
          </div>
        </div>
      </div>

      {/* Actual */}
      <div className="flex flex-col p-4 bg-amber-50/50 rounded-xl border border-amber-200/50">
        <span className="text-[10px] font-bold text-amber-800 uppercase tracking-widest mb-3">Actual</span>
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <span className="text-[11px] text-amber-900/70">Fuel Cost</span>
            <span className="text-[11px] font-bold text-amber-700">₹8,200</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[11px] text-amber-900/70">Trip Time</span>
            <span className="text-[11px] font-bold text-amber-700">10h 20m</span>
          </div>
          <div className="h-px bg-amber-200/50 my-1"></div>
          <div className="flex justify-between items-center">
            <span className="text-[11px] font-bold text-amber-900">Margin</span>
            <span className="text-[11px] font-bold text-red-600">26%</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function InsightPanel() {
  return (
    <motion.div variants={itemVariants} className="py-6">
      <h4 className="text-[11px] font-bold text-content uppercase tracking-widest mb-4">Why Margin Dropped</h4>
      
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface border border-border">
          <div className="flex items-center gap-3">
            <Droplets className="w-4 h-4 text-amber-500 shrink-0" />
            <span className="text-[13px] font-medium text-content">Fuel cost variance</span>
          </div>
          <span className="text-[13px] font-bold text-amber-600">+₹1,100</span>
        </div>

        <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface border border-border">
          <div className="flex items-center gap-3">
            <Clock className="w-4 h-4 text-amber-500 shrink-0" />
            <span className="text-[13px] font-medium text-content">Operational delay</span>
          </div>
          <span className="text-[13px] font-bold text-amber-600">+2h</span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-lg bg-red-50 border border-red-100 mt-2">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-red-500 shrink-0" />
            <span className="text-[13px] font-bold text-red-900">Margin Impact</span>
          </div>
          <span className="text-[15px] font-bold text-red-600">−5%</span>
        </div>
      </div>
    </motion.div>
  );
}

function CopilotLink() {
  return (
    <motion.div variants={itemVariants} className="pt-2">
      <button className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#fafaf9] hover:bg-surface-secondary border border-border transition-colors text-content-secondary group">
        <Sparkles className="w-4 h-4 text-content-muted group-hover:text-amber-500 transition-colors" />
        <span className="text-sm font-medium">Ask Copilot about this trip</span>
        <ArrowRight className="w-3.5 h-3.5 opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
      </button>
    </motion.div>
  );
}

// ============================================================================
// MAIN EXPORT
// ============================================================================

export function TripIntelligenceSection() {
  return (
    <section className="py-32 bg-[#fdfcfb] overflow-hidden">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex flex-col lg:flex-row gap-16 lg:gap-24 items-center">
          
          {/* Left Column: Editorial (40%) */}
          <div className="w-full lg:w-[40%] space-y-8">
            <div className="flex items-center gap-3">
              <div className="w-6 h-[1px] bg-fg-green"></div>
              <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green">Trip Intelligence</span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-medium tracking-tight leading-[1.1] text-content">
              Every trip has an <span className="text-fg-green">economics story.</span>
            </h2>
            
            <p className="text-[17px] text-content-secondary font-light leading-relaxed max-w-[400px]">
              Go beyond tracking. Understand trip profitability, efficiency, and cost drivers before, during, and after the trip.
            </p>

            <button className="flex items-center text-[13px] font-semibold text-fg-green hover:text-fg-green-deep transition-colors group">
              See Trip Intelligence
              <ArrowRight className="w-4 h-4 ml-1.5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* Right Column: Trip Economics Console (60%) */}
          <div className="w-full lg:w-[60%] relative">
            {/* Subtle background glow */}
            <div className="absolute inset-0 bg-fg-green/5 blur-[80px] -z-10 rounded-[40px] translate-x-10 translate-y-10"></div>
            
            <motion.div 
              variants={containerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="bg-white border border-border shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)] rounded-[24px] p-8 w-full max-w-[600px] mx-auto overflow-hidden"
            >
              <TripHeader />
              <RouteVisual />
              <EconomicsSummary />
              <CostBreakdown />
              <ExpectedVsActual />
              <InsightPanel />
              <CopilotLink />
            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
