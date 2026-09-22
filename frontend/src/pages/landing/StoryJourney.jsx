import React, { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { Map, AlertCircle, CheckCircle2, Navigation2 } from 'lucide-react';

const JOURNEY_STEPS = [
  {
    id: 1,
    title: 'The Raw Event',
    desc: 'A vehicle stops for 45 minutes on the highway.',
    detail: 'Most systems just show a red dot on a map. Data without meaning.',
    icon: Map,
    color: 'text-slate-400',
    glow: 'shadow-[0_0_30px_rgba(148,163,184,0.15)]',
    border: 'border-slate-800'
  },
  {
    id: 2,
    title: 'The Context',
    desc: 'The vaahan connects this stop to the active trip.',
    detail: 'Driver Ravi is carrying time-sensitive cargo on Route 4. The stop is unplanned.',
    icon: Navigation2,
    color: 'text-blue-400',
    glow: 'shadow-[0_0_30px_rgba(96,165,250,0.2)]',
    border: 'border-blue-900/50'
  },
  {
    id: 3,
    title: 'The Intelligence',
    desc: 'Anomaly detected: High-risk delay.',
    detail: 'The system flags this instantly based on historical route data and current ETA impact.',
    icon: AlertCircle,
    color: 'text-red-400',
    glow: 'shadow-[0_0_30px_rgba(248,113,113,0.25)]',
    border: 'border-red-900/50'
  },
  {
    id: 4,
    title: 'The Action',
    desc: 'Immediate resolution.',
    detail: 'Automated alert to the fleet manager. Driver contacted. Issue resolved before it impacts the delivery schedule.',
    icon: CheckCircle2,
    color: 'text-emerald-400',
    glow: 'shadow-[0_0_30px_rgba(52,211,153,0.25)]',
    border: 'border-emerald-900/50'
  }
];

export function StoryJourney() {
  const containerRef = useRef(null);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  const lineHeight = useTransform(smoothProgress, [0, 1], ["0%", "100%"]);

  return (
    <section ref={containerRef} className="relative w-full bg-[#020617] text-white">
      {/* Sticky Header */}
      <div className="sticky top-0 w-full h-screen flex flex-col items-center justify-center pointer-events-none overflow-hidden">
        {/* Background Gradients */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900/40 via-[#020617] to-[#020617] z-0 pointer-events-none"></div>
        
        <div className="relative z-10 text-center max-w-2xl px-6 -mt-40 mb-20 opacity-30">
          <div className="text-fg-green font-bold tracking-widest text-xs uppercase mb-4">
            The Vaahan Intelligence
          </div>
          <h2 className="text-4xl md:text-5xl lg:text-[56px] font-medium tracking-tight mb-6">
            Every event in context.
          </h2>
        </div>
      </div>

      {/* Scrolling Content */}
      <div className="relative z-20 w-full max-w-5xl mx-auto px-6 pb-32 -mt-[80vh]">
        <div className="relative">
          {/* Central Line */}
          <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-[2px] bg-slate-800/50 -translate-x-1/2 rounded-full overflow-hidden">
            <motion.div 
              className="absolute top-0 left-0 right-0 bg-gradient-to-b from-fg-green via-emerald-400 to-transparent rounded-full"
              style={{ height: lineHeight }}
            />
          </div>

          {/* Steps */}
          <div className="flex flex-col gap-32 md:gap-64 py-32">
            {JOURNEY_STEPS.map((step, index) => {
              const isEven = index % 2 === 0;
              return (
                <StepItem 
                  key={step.id} 
                  step={step} 
                  isEven={isEven} 
                  index={index} 
                  total={JOURNEY_STEPS.length} 
                />
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

function StepItem({ step, isEven, index, total }) {
  const itemRef = useRef(null);
  
  const { scrollYProgress } = useScroll({
    target: itemRef,
    offset: ["start 80%", "center center"]
  });

  const opacity = useTransform(scrollYProgress, [0, 1], [0.2, 1]);
  const y = useTransform(scrollYProgress, [0, 1], [40, 0]);
  const scale = useTransform(scrollYProgress, [0, 1], [0.95, 1]);
  const iconScale = useTransform(scrollYProgress, [0.5, 1], [0.5, 1]);

  return (
    <div ref={itemRef} className={`relative flex items-center w-full ${isEven ? 'md:flex-row' : 'md:flex-row-reverse'} gap-8 md:gap-16`}>
      
      {/* Connector Dot */}
      <div className="absolute left-8 md:left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
        <motion.div 
          className={`w-5 h-5 rounded-full bg-[#020617] border-[4px] border-slate-700`}
          style={{ 
            borderColor: useTransform(scrollYProgress, [0.8, 1], ['#334155', '#10b981'])
          }}
        />
      </div>

      {/* Desktop Blank Side for alignment */}
      <div className="hidden md:block md:w-1/2"></div>

      {/* Content Card */}
      <motion.div 
        className="w-full pl-20 md:pl-0 md:w-1/2 flex flex-col"
        style={{ opacity, y, scale }}
      >
        <div className={`bg-slate-900/40 backdrop-blur-xl border ${step.border} p-8 rounded-3xl ${step.glow} transition-all duration-700`}>
          <motion.div 
            className={`w-12 h-12 rounded-2xl bg-slate-800/50 flex items-center justify-center mb-6 border border-white/5`}
            style={{ scale: iconScale }}
          >
            <step.icon className={`w-6 h-6 ${step.color}`} />
          </motion.div>
          
          <div className="text-[10px] font-bold tracking-widest uppercase text-slate-400 mb-3">
            Step 0{step.id}
          </div>
          <h3 className="text-2xl font-medium text-white mb-3 tracking-tight">
            {step.title}
          </h3>
          <p className="text-lg text-slate-300 font-light leading-relaxed mb-4">
            {step.desc}
          </p>
          <div className="pt-4 border-t border-white/5">
            <p className="text-sm text-slate-400 leading-relaxed">
              {step.detail}
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
