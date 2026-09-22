import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { 
  MapPin, Navigation2, Receipt, FileText, 
  Users, LayoutDashboard, BarChart3, Zap
} from 'lucide-react';

// ============================================================================
// COMPARISON DATA
// ============================================================================

const COMPARISON_ROWS = [
  {
    category: 'Tracking',
    icon: MapPin,
    left: 'Where is the vehicle?',
    right: 'Where is it, how is the trip performing, and what is changing?',
  },
  {
    category: 'Trips',
    icon: Navigation2,
    left: 'Trip status and route tracking',
    right: 'Trip economics, planned vs actual performance and profitability',
  },
  {
    category: 'Expenses',
    icon: Receipt,
    left: 'Record expenses',
    right: 'Capture, verify, approve and understand expense impact',
  },
  {
    category: 'Documents',
    icon: FileText,
    left: 'Store documents',
    right: 'Track documents, verification, expiry and operational relevance',
  },
  {
    category: 'Drivers',
    icon: Users,
    left: 'Driver records and communication',
    right: 'Driver workflows through the Driver App',
  },
  {
    category: 'Fleet operations',
    icon: LayoutDashboard,
    left: 'Multiple dashboards and spreadsheets',
    right: 'One operational view across vehicles, drivers, trips, expenses and documents',
  },
  {
    category: 'Intelligence',
    icon: BarChart3,
    left: 'Reports and dashboards',
    right: 'Operational insights, anomalies and AI-assisted recommendations',
  },
  {
    category: 'Action',
    icon: Zap,
    left: 'Data for review',
    right: 'Information connected to the action that needs to happen',
  },
];

// ============================================================================
// DESKTOP COMPARISON TABLE
// ============================================================================

function DesktopComparison() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="hidden md:grid grid-cols-2 gap-6 mt-14">
      {/* LEFT PANEL — Most fleet tools */}
      <motion.div
        className="bg-[#F5F5F3] rounded-[20px] p-8 border border-border/40"
        initial={reducedMotion ? { opacity: 1 } : { opacity: 0, x: -20 }}
        whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, x: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        viewport={{ once: true, margin: '-80px' }}
      >
        <div className="mb-8">
          <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted">Most fleet tools</span>
        </div>
        <div className="flex flex-col">
          {COMPARISON_ROWS.map((row, i) => {
            const Icon = row.icon;
            return (
              <motion.div
                key={row.category}
                className={`flex items-start gap-4 py-5 ${i !== COMPARISON_ROWS.length - 1 ? 'border-b border-border/30' : ''}`}
                initial={reducedMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
                whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.05, ease: 'easeOut' }}
                viewport={{ once: true, margin: '-40px' }}
              >
                <div className="w-8 h-8 rounded-lg bg-white border border-border/40 flex items-center justify-center shrink-0 mt-0.5">
                  <Icon className="w-4 h-4 text-content-muted" strokeWidth={1.5} />
                </div>
                <div>
                  <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted block mb-1.5">{row.category}</span>
                  <p className="text-[14px] text-content-secondary font-light leading-relaxed">{row.left}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* RIGHT PANEL — With Vahan */}
      <motion.div
        className="bg-gradient-to-br from-[#EAF5F0] to-[#E2F0E8] rounded-[20px] p-8 border border-fg-green/15 shadow-[0_8px_32px_rgba(31,92,66,0.06)] relative overflow-hidden"
        initial={reducedMotion ? { opacity: 1 } : { opacity: 0, x: 20 }}
        whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: 'easeOut' }}
        viewport={{ once: true, margin: '-80px' }}
      >
        {/* Subtle glow */}
        <div className="absolute -top-20 -right-20 w-60 h-60 bg-fg-green/5 rounded-full blur-3xl pointer-events-none"></div>

        <div className="mb-8 relative z-10">
          <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green">With Vahan</span>
        </div>
        <div className="flex flex-col relative z-10">
          {COMPARISON_ROWS.map((row, i) => {
            const Icon = row.icon;
            return (
              <motion.div
                key={row.category}
                className={`flex items-start gap-4 py-5 ${i !== COMPARISON_ROWS.length - 1 ? 'border-b border-fg-green/10' : ''}`}
                initial={reducedMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
                whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 + i * 0.05, ease: 'easeOut' }}
                viewport={{ once: true, margin: '-40px' }}
              >
                <div className="w-8 h-8 rounded-lg bg-white/80 border border-fg-green/15 flex items-center justify-center shrink-0 mt-0.5">
                  <Icon className="w-4 h-4 text-fg-green" strokeWidth={1.5} />
                </div>
                <div>
                  <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green/70 block mb-1.5">{row.category}</span>
                  <p className="text-[14px] text-content font-medium leading-relaxed">{row.right}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}

// ============================================================================
// MOBILE COMPARISON (STACKED)
// ============================================================================

function MobileComparison() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="block md:hidden mt-10 space-y-4">
      {COMPARISON_ROWS.map((row, i) => {
        const Icon = row.icon;
        return (
          <motion.div
            key={row.category}
            className="rounded-2xl overflow-hidden border border-border/40"
            initial={reducedMotion ? { opacity: 1 } : { opacity: 0, y: 12 }}
            whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.04, ease: 'easeOut' }}
            viewport={{ once: true, margin: '-30px' }}
          >
            {/* Category header */}
            <div className="flex items-center gap-2.5 px-5 py-3 bg-[#F5F5F3] border-b border-border/30">
              <Icon className="w-4 h-4 text-content-muted" strokeWidth={1.5} />
              <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted">{row.category}</span>
            </div>
            {/* Most fleet tools */}
            <div className="px-5 py-4 bg-[#F9F9F8]">
              <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted/60 block mb-1">Most fleet tools</span>
              <p className="text-[13px] text-content-secondary font-light leading-relaxed">{row.left}</p>
            </div>
            {/* With Vahan */}
            <div className="px-5 py-4 bg-[#EDF7F1] border-t border-fg-green/10">
              <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green/70 block mb-1">With Vahan</span>
              <p className="text-[13px] text-content font-medium leading-relaxed">{row.right}</p>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

// ============================================================================
// MAIN EXPORT
// ============================================================================

export function DifferentiationSection() {
  const reducedMotion = useReducedMotion();

  return (
    <section className="py-24 md:py-32 bg-[#fdfcfb] overflow-hidden relative">
      <div className="container mx-auto px-6 max-w-6xl">

        {/* Section Header */}
        <motion.div
          className="max-w-3xl mx-auto text-center mb-4"
          initial={reducedMotion ? { opacity: 1 } : { opacity: 0, y: 16 }}
          whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          viewport={{ once: true, margin: '-80px' }}
        >
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-6 h-[1px] bg-fg-green/60"></div>
            <span className="text-[10px] font-bold tracking-widest uppercase text-fg-green">What makes Vahan different</span>
            <div className="w-6 h-[1px] bg-fg-green/60"></div>
          </div>

          <h2 className="text-3xl md:text-4xl lg:text-[42px] font-medium tracking-tight leading-[1.15] mb-5 text-content">
            Most fleet software shows you what happened.{' '}
            <span className="text-fg-green">Vahan helps you understand what to do next.</span>
          </h2>
          
          <p className="text-[16px] md:text-[17px] text-content-secondary font-light leading-relaxed max-w-2xl mx-auto">
            Traditional tools often stop at tracking, records and reports. Vahan connects operational data across the fleet and turns it into decisions.
          </p>
        </motion.div>

        {/* Desktop comparison */}
        <DesktopComparison />

        {/* Mobile comparison */}
        <MobileComparison />

      </div>
    </section>
  );
}
