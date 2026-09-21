import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Truck } from 'lucide-react';
import { motion } from 'framer-motion';

export default function FooterSection() {
  return (
    <>
      {/* Section 11: Final CTA */}
      <section className="relative w-full h-[500px] flex flex-col justify-center bg-[#0B120F] overflow-hidden">
        
        {/* Abstract Animated Background */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-[url('/assets/hero_bg_1920.jpg')] bg-cover bg-center opacity-30 mix-blend-luminosity"></div>
          <div className="absolute inset-0 bg-gradient-to-r from-[#0B120F] via-[#0B120F]/80 to-transparent"></div>
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B120F] via-transparent to-transparent"></div>
        </div>

        {/* Floating Tracking Tags */}
        <div className="absolute top-[40%] left-[45%] z-10 hidden lg:block">
           <div className="bg-fg-dark/80 backdrop-blur-md border border-white/10 rounded-lg p-2 flex flex-col gap-1 w-32">
              <span className="text-white text-xs font-semibold">MH-04-1234</span>
              <span className="flex items-center gap-1.5 text-[10px] text-fg-green"><div className="w-1.5 h-1.5 rounded-full bg-fg-green"></div>On Time</span>
           </div>
        </div>
        
        <div className="absolute top-[30%] left-[65%] z-10 hidden xl:block">
           <div className="bg-fg-dark/80 backdrop-blur-md border border-white/10 rounded-lg p-2 flex flex-col gap-1 w-32">
              <span className="text-white text-xs font-semibold">GJ-01-7788</span>
              <span className="flex items-center gap-1.5 text-[10px] text-cyan-400"><div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>In Transit</span>
           </div>
        </div>
        
        <div className="absolute top-[60%] left-[75%] z-10 hidden md:block">
           <div className="bg-fg-dark/80 backdrop-blur-md border border-white/10 rounded-lg p-2 flex flex-col gap-1 w-32 border-amber-500/30">
              <span className="text-white text-xs font-semibold">RJ-14-9012</span>
              <span className="flex items-center gap-1.5 text-[10px] text-amber-500"><div className="w-1.5 h-1.5 rounded-full bg-amber-500"></div>Attention</span>
           </div>
        </div>

        <div className="container mx-auto px-6 max-w-7xl relative z-20">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="max-w-2xl"
          >
            <div className="text-[10px] font-bold tracking-widest uppercase text-content-muted mb-4">
              THE ROAD AHEAD
            </div>
            
            <h2 className="text-4xl md:text-5xl font-medium tracking-tight text-white mb-4 leading-[1.1]">
              Run your fleet<br/>
              with context.
            </h2>
            
            <p className="text-lg text-content-muted font-light leading-relaxed mb-8">
              More than tracking. Real understanding.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/dashboard" className="inline-flex items-center justify-center bg-fg-green hover:bg-fg-green/90 text-white font-medium px-6 py-3 h-auto text-sm rounded transition-colors">
                Open Dashboard <ArrowRight className="ml-2 w-4 h-4" />
              </Link>
              <Link to="#contact" className="inline-flex items-center justify-center bg-transparent border border-white/20 hover:bg-white/5 text-white font-medium px-6 py-3 h-auto text-sm rounded transition-colors">
                Talk to Us
              </Link>
            </div>
          </motion.div>
        </div>

        {/* Handwriting Note */}
        <motion.div 
          initial={{ opacity: 0, rotate: 0 }}
          whileInView={{ opacity: 1, rotate: -5 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="absolute bottom-16 right-16 z-20 font-['Nanum_Pen_Script',cursive,sans-serif] text-white/50 text-3xl max-w-[200px] leading-tight hidden md:block"
        >
          Every mile<br/>has a story.
        </motion.div>
      </section>

      {/* Section 12: Footer */}
      <footer className="bg-fg-dark border-t border-white/10 py-12 px-6">
        <div className="max-w-[1400px] mx-auto lg:px-4">
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-10">
            {/* Brand */}
            <div className="lg:col-span-2">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-6 h-6 flex items-center justify-center bg-fg-green rounded-md">
                   <span className="text-white font-bold text-xs">V</span>
                </div>
                <span className="text-xl font-bold tracking-tight text-white">
                  the vaahan
                </span>
              </div>
              <p className="text-sm text-content-muted leading-relaxed max-w-xs">
                Intelligence for Every Mile. Connect your vehicles, drivers, trips, and expenses to run a smarter, more profitable fleet.
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">Platform</h4>
              <ul className="space-y-2.5 text-sm">
                <li><a href="#how" className="text-content-muted hover:text-white transition-colors">How it works</a></li>
                <li><a href="#engines" className="text-content-muted hover:text-white transition-colors">Intelligence Engines</a></li>
                <li><a href="#product" className="text-content-muted hover:text-white transition-colors">Dashboard</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">Apps</h4>
              <ul className="space-y-2.5 text-sm">
                <li><a href="#apps" className="text-content-muted hover:text-white transition-colors">Driver App</a></li>
                <li><a href="#apps" className="text-content-muted hover:text-white transition-colors">Owner App</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">Company</h4>
              <ul className="space-y-2.5 text-sm">
                <li><a href="#about" className="text-content-muted hover:text-white transition-colors">About</a></li>
                <li><a href="mailto:info@thevaahan.com" className="text-content-muted hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-[11px] text-content-muted">© 2026 the vaahan. All rights reserved.</p>
            <div className="flex items-center gap-4 text-xs text-content-muted">
              <a href="#" className="hover:text-white transition-colors">English</a>
              <span>•</span>
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <span>•</span>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}

function ButtonLink({ to, primary, secondary, children }) {
  if (primary) {
    return (
      <Link to={to} className="inline-flex items-center justify-center bg-fg-green hover:bg-fg-green/90 text-white font-medium px-8 py-4 h-auto text-lg rounded-full transition-colors">
        {children}
      </Link>
    );
  }
  return (
    <Link to={to} className="inline-flex items-center justify-center bg-transparent border border-white/20 hover:bg-white/5 text-white font-medium px-8 py-4 h-auto text-lg rounded-full transition-colors">
      {children}
    </Link>
  );
}
