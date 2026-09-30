import React from 'react';
import { ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

export function HeroSection({ onDemo }) {
  // Respect user motion preferences
  const reducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  return (
    <section className="relative flex h-screen min-h-[800px] w-full flex-col justify-center overflow-hidden bg-[#020405]">
      
      {/* 
        CINEMATIC LOGISTICS BACKGROUND 
        High-quality image background representing a premium physical logistics network
      */}
      <motion.div 
        className="absolute inset-0 z-0 h-[110%] w-[110%] -left-[5%] -top-[5%] bg-cover bg-center origin-center"
        style={{ backgroundImage: `url('/assets/hero-truck-bg.jpg')` }}
        animate={reducedMotion ? {} : {
          scale: [1, 1.03],
          x: ['0%', '-1.5%'],
          y: ['0%', '-1%']
        }}
        transition={{
          duration: 45,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "linear"
        }}
      />

      {/* Subtle Atmospheric Overlay (Fog/Depth) */}
      <motion.div
        className="absolute inset-0 z-[1] pointer-events-none mix-blend-screen"
        style={{
          background: 'radial-gradient(circle at 75% 65%, rgba(16, 185, 129, 0.08) 0%, transparent 50%)'
        }}
        animate={reducedMotion ? {} : {
          opacity: [0.5, 0.8, 0.5],
          scale: [1, 1.1, 1]
        }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Subtle Data Integration / Trajectory Line Overlay */}
      <div className="absolute inset-0 z-[1] pointer-events-none overflow-hidden">
        <svg className="absolute h-full w-full opacity-40 mix-blend-screen" preserveAspectRatio="none">
          {/* Subtle curved highway trajectory line */}
          <motion.path 
            d="M 100% 90% Q 70% 60% 50% 40% T 30% 30%" 
            fill="none" 
            stroke="url(#green-gradient)" 
            strokeWidth="1.5"
            strokeDasharray="4 8"
            animate={reducedMotion ? {} : { strokeDashoffset: [0, -100] }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          />
          <defs>
            <linearGradient id="green-gradient" x1="100%" y1="100%" x2="30%" y2="30%">
              <stop offset="0%" stopColor="#34d399" stopOpacity="0" />
              <stop offset="30%" stopColor="#34d399" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#34d399" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>

        {/* Pulsing Location Signal (Positioned approximately over highway area) */}
        <div className="absolute right-[28%] bottom-[35%] flex items-center justify-center">
          <motion.div 
            className="absolute h-16 w-16 rounded-full border border-[#34d399]/20"
            animate={reducedMotion ? {} : { scale: [0.5, 2], opacity: [0.8, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeOut" }}
          />
          <div className="h-1.5 w-1.5 rounded-full bg-[#34d399] shadow-[0_0_8px_rgba(52,211,153,1)]" />
        </div>
      </div>

      {/* 
        FOREGROUND PROTECTION GRADIENTS
        Aggressive black gradients on the left 45% to guarantee text legibility 
      */}
      <div className="absolute inset-0 z-[2] bg-gradient-to-r from-[#020405] via-[#020405]/95 to-transparent w-[90%] md:w-[60%]" />
      <div className="absolute inset-0 z-[2] bg-[radial-gradient(ellipse_at_0%_50%,_rgba(2,4,5,1)_0%,_rgba(2,4,5,0)_60%)] opacity-95" />
      <div className="absolute inset-0 z-[2] bg-gradient-to-b from-[#020405]/80 via-transparent to-[#020405]/95" />

      {/* Foreground Content - EXACTLY PRESERVED */}
      <div className="container relative z-10 mx-auto flex h-full max-w-7xl flex-col justify-between px-6 pt-24 pointer-events-none">
        <div className="flex flex-1 flex-col justify-center pointer-events-auto">
          <div className="max-w-2xl">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
              <div className="mb-6 text-[10px] font-bold uppercase tracking-widest text-white/50">
                FLEET INTELLIGENCE FOR A MORE EFFICIENT TOMORROW
              </div>
              <h1 className="mb-6 text-5xl font-medium leading-[1.05] tracking-tight text-white sm:text-6xl md:text-7xl lg:text-[80px]">
                Every mile <br />has a story.<br />
                <span className="font-normal text-[#15803d]">We help you understand it.</span>
              </h1>
              <p className="mb-10 max-w-xl text-lg font-light leading-relaxed text-white/60 sm:text-xl">
                The vaahan connects your vehicles, drivers, trips, expenses and more— turning fleet activity into operational and financial intelligence.
              </p>
              <div className="flex flex-col gap-4 sm:flex-row">
                <a href="#platform" className="inline-flex items-center justify-center rounded bg-[#15803d] px-8 py-3.5 text-sm font-medium text-white transition-colors hover:bg-[#166534]">
                  Explore the Platform <ArrowRight className="ml-2 h-4 w-4" />
                </a>
                <button type="button" onClick={onDemo} className="inline-flex items-center justify-center rounded border border-white/20 bg-transparent px-8 py-3.5 text-sm font-medium text-white transition-colors hover:bg-white/5">
                  Book a Demo
                </button>
              </div>
            </motion.div>
          </div>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }} className="flex items-center gap-12 pb-12 pointer-events-auto">
          {['DATA', 'CONTEXT', 'INTELLIGENCE', 'ACTION'].map((label) => (
            <div key={label}>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-white/80">{label}</div>
              <div className="mt-1 text-[10px] text-white/40">Connected fleet signal</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
