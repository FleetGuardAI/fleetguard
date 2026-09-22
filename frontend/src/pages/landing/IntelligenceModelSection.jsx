import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { 
  ArrowRight, 
  Navigation2, Receipt, FileText, Smartphone, Eye, Sparkles
} from 'lucide-react';

// ============================================================================
// FEATURE CARDS DATA
// ============================================================================

const FEATURE_CARDS = [
  {
    num: '01',
    title: 'Trip Intelligence',
    description: 'Understand every trip beyond GPS tracking. See planned vs actual time, fuel cost, route performance and trip profitability.',
    icon: Navigation2,
  },
  {
    num: '02',
    title: 'Expense Control',
    description: 'Capture driver expenses, receipts and supporting documents in one place. Review, verify and approve spending before it becomes leakage.',
    icon: Receipt,
  },
  {
    num: '03',
    title: 'Document Control',
    description: 'Keep vehicle, driver and trip documents organized with verification status, expiry tracking and audit history.',
    icon: FileText,
  },
  {
    num: '04',
    title: 'Driver Operations',
    description: 'Connect drivers directly to operations through the Driver App. Handle trips, expenses, documents, emergency requests and updates without endless calls.',
    icon: Smartphone,
  },
  {
    num: '05',
    title: 'Fleet Visibility',
    description: 'See vehicles, drivers, trips, maintenance and operational activity from one system instead of scattered spreadsheets and WhatsApp conversations.',
    icon: Eye,
  },
  {
    num: '06',
    title: 'AI Operations Copilot',
    description: "Turn operational data into useful explanations, alerts and recommendations. Don't just show what happened — explain what needs attention.",
    icon: Sparkles,
  },
];

// ============================================================================
// FEATURE CARD COMPONENT
// ============================================================================

function FeatureCard({ card, index }) {
  const reducedMotion = useReducedMotion();
  const Icon = card.icon;

  // Stagger offset: odd cards shift down slightly on desktop for visual rhythm
  const isOffset = index % 2 === 1;

  return (
    <motion.div
      className={`group relative bg-white/70 backdrop-blur-sm border border-border/60 rounded-[20px] p-7 shadow-sm 
        transition-all duration-300 cursor-default
        hover:shadow-[0_12px_32px_rgba(31,92,66,0.08)] hover:border-fg-green/25 hover:-translate-y-1 hover:scale-[1.01]
        ${isOffset ? 'lg:mt-8' : ''}`}
      initial={reducedMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 24, scale: 0.97 }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.55, delay: index * 0.1, ease: 'easeOut' }}
      viewport={{ once: true, margin: '-60px' }}
    >
      {/* Top accent line */}
      <div className="absolute top-0 left-6 right-6 h-[2px] bg-gradient-to-r from-fg-green/0 via-fg-green/20 to-fg-green/0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

      {/* Card number + Icon row */}
      <div className="flex items-center justify-between mb-5">
        <span className="text-[11px] font-bold tracking-widest text-content-muted uppercase">{card.num}</span>
        <div className="w-10 h-10 rounded-xl bg-[#EAF5F0] border border-fg-green/10 flex items-center justify-center group-hover:bg-fg-green/10 transition-colors duration-300">
          <Icon className="w-5 h-5 text-fg-green" strokeWidth={1.5} />
        </div>
      </div>

      {/* Title */}
      <h3 className="text-[18px] font-semibold text-content tracking-tight mb-3 group-hover:text-fg-green transition-colors duration-300">
        {card.title}
      </h3>

      {/* Description */}
      <p className="text-[14px] text-content-secondary font-light leading-relaxed">
        {card.description}
      </p>
    </motion.div>
  );
}

// ============================================================================
// MOBILE FEATURE CARD
// ============================================================================

function MobileFeatureCard({ card, index }) {
  const reducedMotion = useReducedMotion();
  const Icon = card.icon;

  return (
    <motion.div
      className="bg-white/70 backdrop-blur-sm border border-border/60 rounded-2xl p-6 shadow-sm"
      initial={reducedMotion ? { opacity: 1 } : { opacity: 0, y: 16 }}
      whileInView={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08, ease: 'easeOut' }}
      viewport={{ once: true, margin: '-40px' }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 rounded-lg bg-[#EAF5F0] border border-fg-green/10 flex items-center justify-center shrink-0">
          <Icon className="w-4.5 h-4.5 text-fg-green" strokeWidth={1.5} />
        </div>
        <div>
          <span className="text-[10px] font-bold tracking-widest text-content-muted uppercase block">{card.num}</span>
          <h3 className="text-[16px] font-semibold text-content tracking-tight leading-tight">{card.title}</h3>
        </div>
      </div>
      <p className="text-[13px] text-content-secondary font-light leading-relaxed">
        {card.description}
      </p>
    </motion.div>
  );
}

// ============================================================================
// MAIN EXPORT
// ============================================================================

export function IntelligenceModelSection() {
  return (
    <section id="how-vaahan-works" className="py-24 bg-[#fdfcfb] overflow-hidden relative scroll-mt-24">
      <div className="container mx-auto px-6 max-w-[1440px] relative z-10">
        <div className="flex flex-col xl:flex-row gap-12 xl:gap-16">
          
          {/* Left Column: Editorial (35%) */}
          <div className="w-full xl:w-[33%] flex flex-col justify-start pt-4 xl:pt-16 relative z-50 shrink-0">
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

          {/* Right Column: Feature Cards Grid (Desktop) */}
          <div className="hidden xl:block w-full xl:w-[67%]">
            <div className="grid grid-cols-2 gap-6">
              {FEATURE_CARDS.map((card, index) => (
                <FeatureCard key={card.num} card={card} index={index} />
              ))}
            </div>
          </div>

          {/* Mobile/Tablet Fallback: Vertical Stack */}
          <div className="block xl:hidden w-full">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {FEATURE_CARDS.map((card, index) => (
                <MobileFeatureCard key={card.num} card={card} index={index} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
