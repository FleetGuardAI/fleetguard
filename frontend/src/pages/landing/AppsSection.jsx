import React from 'react';
import { Smartphone, CheckCircle2, ArrowRight, Camera, AlertTriangle, Droplets, Receipt, ShieldAlert, Sparkles, Navigation } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';

// ============================================================================
// ANIMATION VARIANTS
// ============================================================================

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.3, delayChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" }
  }
};

const signalVariants = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: { 
    pathLength: 1, 
    opacity: 1,
    transition: { duration: 1.5, ease: "easeInOut", delay: 1.2 } 
  }
};

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

function DriverApp() {
  return (
    <motion.div variants={itemVariants} className="w-full max-w-[300px] mx-auto relative group">
      {/* Editorial Label */}
      <div className="absolute -top-10 left-0 right-0 flex justify-center">
        <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted">Field</span>
      </div>

      {/* Device Frame */}
      <div className="bg-[#1e293b] rounded-[36px] p-[10px] shadow-[0_25px_50px_-12px_rgba(0,0,0,0.15)] ring-1 ring-slate-900/5 relative">
        {/* Notch */}
        <div className="absolute top-[10px] left-1/2 -translate-x-1/2 w-24 h-5 bg-[#1e293b] rounded-b-xl z-20"></div>

        {/* Screen */}
        <div className="bg-[#f8fafc] rounded-[28px] overflow-hidden flex flex-col h-[520px] relative">
          
          {/* Status Bar */}
          <div className="h-10 bg-fg-green w-full shrink-0 flex justify-between items-end px-6 pb-1">
            <span className="text-[10px] font-bold text-white/90">9:41</span>
            <div className="flex gap-1.5 items-center pb-0.5">
              <div className="w-3.5 h-2.5 rounded-sm bg-white/90"></div>
              <div className="w-3.5 h-2.5 rounded-sm bg-white/90"></div>
            </div>
          </div>

          {/* App Header */}
          <div className="bg-fg-green px-5 pt-3 pb-6 shrink-0 relative overflow-hidden">
            <div className="absolute right-0 top-0 opacity-10">
              <Smartphone className="w-32 h-32 -mr-8 -mt-8" />
            </div>
            
            <div className="flex justify-between items-center mb-6 relative z-10">
              <span className="text-[11px] font-bold text-white tracking-wide">Driver Portal</span>
              <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center">
                 <span className="text-[10px] font-bold text-white">RK</span>
              </div>
            </div>
            
            <div className="relative z-10">
              <span className="text-[10px] font-bold text-emerald-200 uppercase tracking-widest mb-1 block">Active</span>
              <h3 className="text-2xl font-medium text-white tracking-tight leading-none mb-1.5">Trip #0402</h3>
              <p className="text-[13px] text-emerald-100 flex items-center gap-1.5">
                Delhi <ArrowRight className="w-3 h-3" /> Jaipur
              </p>
            </div>
          </div>

          {/* Body */}
          <div className="flex-1 px-4 py-5 flex flex-col gap-3 bg-slate-50 relative z-10 -mt-3 rounded-t-2xl">
            
            <span className="text-[10px] font-bold text-content-muted uppercase tracking-widest ml-1 mb-1 block">Required Actions</span>

            {/* Active Highlighted Action (The Sync Event) */}
            <div className="bg-white rounded-xl p-4 shadow-sm border-2 border-emerald-500/30 flex flex-col gap-3 relative overflow-hidden group">
              <div className="absolute inset-0 bg-emerald-50/50"></div>
              <div className="relative z-10 flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                    <Droplets className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[13px] font-bold text-content">Log Fuel</span>
                    <span className="text-[11px] text-content-secondary mt-0.5">Required for this trip</span>
                  </div>
                </div>
              </div>
              
              <div className="relative z-10 bg-white border border-border/60 rounded-lg p-2.5 flex items-center justify-between">
                <span className="text-[11px] font-semibold text-content-secondary">Amount</span>
                <span className="text-[13px] font-bold text-content">₹8,200</span>
              </div>
              
              <button className="relative z-10 w-full py-2.5 bg-emerald-600 text-white rounded-lg text-[12px] font-semibold flex items-center justify-center gap-1.5 shadow-sm">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Submitted
              </button>
            </div>

            {/* Other Actions */}
            <div className="bg-white rounded-xl p-3.5 shadow-sm border border-border/60 flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-surface-secondary flex items-center justify-center shrink-0">
                <Receipt className="w-4 h-4 text-content-secondary" />
              </div>
              <div className="flex flex-col">
                <span className="text-[13px] font-semibold text-content">Upload Receipt</span>
                <span className="text-[10px] text-content-muted">Tolls or expenses</span>
              </div>
            </div>

            <div className="bg-white rounded-xl p-3.5 shadow-sm border border-border/60 flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center shrink-0">
                <ShieldAlert className="w-4 h-4 text-red-500" />
              </div>
              <div className="flex flex-col">
                <span className="text-[13px] font-semibold text-red-700">Report Issue</span>
                <span className="text-[10px] text-red-500/70">Breakdown or delay</span>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Supporting Copy */}
      <div className="mt-8 text-center max-w-[260px] mx-auto">
        <h4 className="text-[14px] font-bold text-content mb-1.5">Driver App</h4>
        <p className="text-[13px] text-content-secondary leading-relaxed">Simple tools for the road. Log fuel, upload receipts, update trips and report issues.</p>
      </div>
    </motion.div>
  );
}

function SharedContextConnector() {
  const reducedMotion = useReducedMotion();
  
  return (
    <motion.div variants={itemVariants} className="w-full lg:w-[15%] h-24 lg:h-auto flex flex-col lg:flex-row items-center justify-center relative my-12 lg:my-0 shrink-0">
      
      {/* SVG Connecting Line */}
      <div className="absolute inset-0 pointer-events-none hidden lg:block z-0">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
          {/* Background line */}
          <path d="M 0,50 L 100,50" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 4" fill="none" />
          {/* Animated signal line */}
          <motion.path 
            d="M 0,50 L 100,50" 
            stroke="#10b981" 
            strokeWidth="2" 
            fill="none" 
            variants={signalVariants}
          />
          {/* Signal dot */}
          {!reducedMotion && (
            <motion.circle 
              r="3" 
              fill="#10b981" 
              initial={{ cx: 0, cy: 50, opacity: 0 }}
              whileInView={{ opacity: [0, 1, 1, 0] }}
              animate={{ cx: 100 }}
              transition={{ 
                cx: { duration: 2, ease: "easeInOut", repeat: Infinity, delay: 2 },
                opacity: { duration: 2, repeat: Infinity, delay: 2 }
              }}
            />
          )}
        </svg>
      </div>

      {/* Vertical line for mobile */}
      <div className="absolute inset-0 pointer-events-none block lg:hidden z-0">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
          <path d="M 50,0 L 50,100" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 4" fill="none" />
        </svg>
      </div>

      {/* Connector Label */}
      <div className="bg-[#fdfcfb] px-3 py-2 z-10 flex flex-col items-center">
        <div className="w-7 h-7 rounded bg-white border border-border shadow-sm flex items-center justify-center mb-2">
          <span className="text-[12px] font-bold text-fg-green leading-none">V</span>
        </div>
        <span className="text-[9px] font-bold text-content uppercase tracking-widest text-center">Same fleet<br/><span className="text-content-muted font-medium">Same truth</span></span>
      </div>

    </motion.div>
  );
}

function OwnerApp() {
  return (
    <motion.div variants={itemVariants} className="w-full lg:max-w-[550px] relative group mx-auto lg:ml-0">
      {/* Editorial Label */}
      <div className="absolute -top-10 left-0 right-0 flex justify-center lg:justify-start lg:pl-10">
        <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted">Command Center</span>
      </div>

      {/* Desktop Dashboard Frame */}
      <div className="bg-white rounded-xl shadow-[0_25px_50px_-12px_rgba(0,0,0,0.1)] border border-border/80 overflow-hidden flex flex-col">
        
        {/* Browser Chrome */}
        <div className="h-10 bg-[#fafaf9] border-b border-border/50 flex items-center px-4 gap-4 shrink-0">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ef4444]/80"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]/80"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-[#10b981]/80"></div>
          </div>
          <div className="flex-1 bg-white border border-border/50 h-6 rounded-md flex items-center justify-center text-[10px] text-content-muted">
            app.thevaahan.com
          </div>
          <div className="w-10"></div> {/* Spacer for symmetry */}
        </div>

        {/* Dashboard Layout */}
        <div className="flex h-[360px]">
          
          {/* Sidebar */}
          <div className="w-[120px] bg-[#0b1120] p-3 flex flex-col gap-1 shrink-0">
             <div className="text-white text-[10px] font-bold mb-4 flex items-center gap-1.5 px-1">
               <div className="w-3 h-3 bg-fg-green rounded-[2px] flex items-center justify-center"><span className="text-[7px] text-[#0b1120]">V</span></div>
               the vaahan
             </div>
             <div className="h-6 rounded bg-white/10 px-2 flex items-center">
               <span className="text-[9px] text-white/90 font-medium">Overview</span>
             </div>
             <div className="h-6 rounded hover:bg-white/5 px-2 flex items-center">
               <span className="text-[9px] text-white/50">Trips</span>
             </div>
             <div className="h-6 rounded hover:bg-white/5 px-2 flex items-center">
               <span className="text-[9px] text-white/50">Vehicles</span>
             </div>
             <div className="h-6 rounded hover:bg-white/5 px-2 flex items-center">
               <span className="text-[9px] text-white/50">Financials</span>
             </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 bg-[#f8fafc] p-6 overflow-hidden flex flex-col">
             <div className="flex justify-between items-end mb-5">
               <div>
                 <h2 className="text-lg font-bold text-content leading-none mb-1">Fleet Overview</h2>
                 <span className="text-[11px] text-content-muted">Live operational status</span>
               </div>
               <div className="px-2 py-1 bg-white border border-border/60 rounded text-[10px] font-semibold text-content-secondary shadow-sm">
                 Last 24 Hours
               </div>
             </div>

             {/* Metric Cards */}
             <div className="grid grid-cols-3 gap-3 mb-5 shrink-0">
                <div className="bg-white rounded-lg p-3 border border-border/60 shadow-sm flex flex-col gap-1">
                  <span className="text-[9px] font-bold text-content-muted uppercase tracking-widest">Active Vehicles</span>
                  <span className="text-xl font-bold text-content">248</span>
                </div>
                <div className="bg-white rounded-lg p-3 border border-border/60 shadow-sm flex flex-col gap-1">
                  <span className="text-[9px] font-bold text-red-500 uppercase tracking-widest">Alerts</span>
                  <span className="text-xl font-bold text-red-600">12</span>
                </div>
                <div className="bg-white rounded-lg p-3 border border-border/60 shadow-sm flex flex-col gap-1">
                  <span className="text-[9px] font-bold text-content-muted uppercase tracking-widest">On Time</span>
                  <span className="text-xl font-bold text-content">98%</span>
                </div>
             </div>

             {/* Recent Signals / Activity */}
             <div className="bg-white rounded-lg border border-border/60 shadow-sm flex-1 flex flex-col overflow-hidden">
                <div className="px-4 py-3 border-b border-border/60 bg-[#fafaf9]">
                  <span className="text-[11px] font-bold text-content uppercase tracking-widest">Recent Signals</span>
                </div>
                
                <div className="p-2 flex flex-col gap-1.5">
                  {/* The Synced Event */}
                  <motion.div 
                    className="p-3 rounded-md bg-emerald-50/80 border border-emerald-100 flex items-start gap-3 relative overflow-hidden"
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 2.2 }} // Wait for signal to travel
                  >
                     <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500"></div>
                     <div className="w-6 h-6 rounded-full bg-emerald-100 border border-emerald-200 flex items-center justify-center shrink-0">
                       <Droplets className="w-3 h-3 text-emerald-600" />
                     </div>
                     <div className="flex flex-col flex-1">
                       <div className="flex justify-between items-start">
                         <span className="text-[12px] font-bold text-content">Fuel transaction</span>
                         <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-100 px-1.5 rounded">Just now</span>
                       </div>
                       <span className="text-[11px] text-content-secondary mt-0.5">Trip #0402 • Delhi → Jaipur</span>
                       <span className="text-[13px] font-bold text-content mt-1.5">₹8,200 <span className="font-normal text-[11px] text-content-muted ml-1">Verified via Driver App</span></span>
                     </div>
                  </motion.div>

                  {/* Other History */}
                  <div className="p-3 rounded-md hover:bg-[#fafaf9] border border-transparent flex items-start gap-3 transition-colors">
                     <div className="w-6 h-6 rounded-full bg-surface-secondary border border-border flex items-center justify-center shrink-0">
                       <Navigation className="w-3 h-3 text-content-muted" />
                     </div>
                     <div className="flex flex-col flex-1">
                       <div className="flex justify-between items-start">
                         <span className="text-[12px] font-semibold text-content">Route update</span>
                         <span className="text-[10px] text-content-muted font-medium">12m ago</span>
                       </div>
                       <span className="text-[11px] text-content-secondary mt-0.5">Vehicle UP-16-9900 crossed border</span>
                     </div>
                  </div>
                </div>
             </div>
          </div>
        </div>
      </div>

      {/* Supporting Copy */}
      <div className="mt-8 text-center lg:text-left max-w-[320px] mx-auto lg:ml-0 lg:pl-4">
        <h4 className="text-[14px] font-bold text-content mb-1.5">Owner App</h4>
        <p className="text-[13px] text-content-secondary leading-relaxed">Full visibility and control. Monitor the fleet, investigate signals, understand performance and make informed decisions.</p>
      </div>
    </motion.div>
  );
}

// ============================================================================
// MAIN EXPORT
// ============================================================================

export function AppsSection() {
  return (
    <section className="py-32 bg-[#fdfcfb] overflow-hidden relative">
      <div className="container mx-auto px-6 max-w-7xl">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-24 relative z-10">
          <div className="inline-flex items-center gap-3 mb-6">
            <div className="w-6 h-[1px] bg-fg-green"></div>
            <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green">Built for everyone</span>
            <div className="w-6 h-[1px] bg-fg-green"></div>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-medium tracking-tight leading-[1.1] mb-5 text-content">
            One fleet. Two operating surfaces.
          </h2>
          
          <p className="text-[17px] text-content-secondary font-light leading-relaxed">
            The same data. The same context. A better way for everyone to work.
          </p>
        </div>

        {/* Visual Composition */}
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="flex flex-col lg:flex-row items-center lg:items-start justify-between relative"
        >
          <DriverApp />
          <SharedContextConnector />
          <OwnerApp />
        </motion.div>

      </div>
    </section>
  );
}
