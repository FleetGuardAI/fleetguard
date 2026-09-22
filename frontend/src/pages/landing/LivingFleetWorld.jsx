import React, { useRef, useLayoutEffect, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useLanguage } from '@/i18n/LanguageContext';
import { FleetMap } from './FleetMap';
import { useTimeline } from './TimelineContext';
import { Truck, AlertTriangle, TrendingUp, Sparkles, MessageSquare, ArrowRight, Zap, Route } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

export function LivingFleetWorld() {
  const { t } = useLanguage();
  const { scrollContainerRef } = useTimeline();
  
  // Refs for the World and UI
  const worldRef = useRef(null);
  const mapRef = useRef(null); // Ref to the FleetMap component instance
  
  // UI Layer Refs
  const heroTextRef = useRef(null);
  const tripPanelRef = useRef(null);
  const varianceSectionRef = useRef(null);
  const opsEngineRef = useRef(null);
  const copilotRef = useRef(null);
  const finalRevealRef = useRef(null);

  useLayoutEffect(() => {
    let ctx = gsap.context(() => {
      
      const mapEls = mapRef.current;
      if (!mapEls) return;

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: scrollContainerRef.current,
          start: 'top top',
          end: 'bottom bottom',
          scrub: 1,
        }
      });

      // INITIAL STATE (Phase 1: Ambient Fleet)
      gsap.set(mapEls.container, { xPercent: -50, yPercent: -50, scale: 0.4, x: 0, y: 0, opacity: 0.6 });
      gsap.set(mapEls.targetVehicle, { scale: 1 });
      gsap.set('.target-vehicle-label', { opacity: 0 });
      
      // Setup UI Centering using GSAP to avoid Tailwind transform conflicts
      gsap.set(heroTextRef.current, { yPercent: -50 });
      gsap.set(copilotRef.current, { xPercent: -50, opacity: 0, pointerEvents: 'none' });
      gsap.set(finalRevealRef.current, { yPercent: -50, opacity: 0, pointerEvents: 'none' });
      gsap.set([tripPanelRef.current, opsEngineRef.current], { opacity: 0, pointerEvents: 'none' });
      gsap.set(varianceSectionRef.current, { height: 0, opacity: 0, marginTop: 0 });

      // PHASE 2: Selection (10% - 25%)
      // Zoom into MH-04-1234
      tl.to(heroTextRef.current, { opacity: 0, y: -50, duration: 0.1 }, 0.05)
        .to(mapEls.container, { 
          scale: 1.2, // Zoom in
          opacity: 1,
          duration: 0.15,
          ease: 'power2.inOut'
        }, 0.1)
        .to(mapEls.otherVehicles, { opacity: 0.1, duration: 0.1 }, 0.1)
        .to('.target-vehicle-label', { opacity: 1, duration: 0.05 }, 0.2)
        // Show Trip Context Panel
        .fromTo(tripPanelRef.current, 
          { opacity: 0, x: -20, pointerEvents: 'none' },
          { opacity: 1, x: 0, pointerEvents: 'auto', duration: 0.1 }, 
          0.2
        );

      // PHASE 3: The Event (30% - 45%)
      // Fuel Variance occurs. UI transforms.
      tl.to(mapEls.targetVehicle.querySelector('.bg-fg-green'), { backgroundColor: '#F59E0B', boxShadow: '0 0 20px rgba(245,158,11,0.8)', duration: 0.05 }, 0.3)
        .to(mapEls.targetVehicle.querySelector('.border-fg-green\\/40'), { borderColor: 'rgba(245,158,11,0.5)', duration: 0.05 }, 0.3)
        .to('.target-vehicle-label', { borderColor: 'rgba(245,158,11,0.5)', color: '#F59E0B', duration: 0.05 }, 0.3)
        // Expand the Trip Panel to show the Intelligence (Expected vs Actual)
        .to(varianceSectionRef.current, { 
          height: 'auto', 
          opacity: 1, 
          marginTop: '16px',
          duration: 0.1,
          ease: 'back.out(1.2)'
        }, 0.35);

      // PHASE 4: Business Consequence (50% - 65%)
      // Camera pans right slightly to make room for Ops Engine
      tl.to(mapEls.container, { xPercent: -65, duration: 0.15, ease: 'power1.inOut' }, 0.5)
        .to(tripPanelRef.current, { x: '-20vw', duration: 0.15 }, 0.5)
        // Ops Engine panel emerges
        .fromTo(opsEngineRef.current,
          { opacity: 0, y: 30, scale: 0.95, pointerEvents: 'none' },
          { opacity: 1, y: 0, scale: 1, pointerEvents: 'auto', duration: 0.1 },
          0.55
        );

      // PHASE 5: Copilot Decision (70% - 85%)
      // Copilot emerges with the context
      tl.to([tripPanelRef.current, opsEngineRef.current], { opacity: 0.4, scale: 0.95, duration: 0.1 }, 0.7)
        .fromTo(copilotRef.current,
          { opacity: 0, y: 50, pointerEvents: 'none' },
          { opacity: 1, y: 0, pointerEvents: 'auto', duration: 0.15, ease: 'power2.out' },
          0.75
        );

      // PHASE 6: Return to Fleet (90% - 100%)
      // Pull back to the macro view, but now fleet is analyzed
      tl.to([tripPanelRef.current, opsEngineRef.current, copilotRef.current], { opacity: 0, pointerEvents: 'none', duration: 0.1 }, 0.9)
        .to('.target-vehicle-label', { opacity: 0, duration: 0.05 }, 0.9)
        .to(mapEls.container, { 
          scale: 0.4, 
          xPercent: -50, 
          yPercent: -50,
          duration: 0.15,
          ease: 'power2.inOut'
        }, 0.9)
        .to(mapEls.otherVehicles, { opacity: 0.8, duration: 0.1 }, 0.9)
        // Show Final Typography
        .fromTo(finalRevealRef.current,
          { opacity: 0, scale: 0.9, pointerEvents: 'none' },
          { opacity: 1, scale: 1, pointerEvents: 'auto', duration: 0.1 },
          0.95
        );

    }, scrollContainerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div 
      ref={scrollContainerRef} 
      className="relative w-full bg-surface-inverted text-white"
      style={{ height: '600vh' }} // The scroll track length
    >
      {/* The Sticky "Camera" Window */}
      <div className="sticky top-0 w-full h-screen overflow-hidden flex items-center justify-center">
        
        {/* The Spatial World Layer */}
        <div ref={worldRef} className="absolute inset-0 w-full h-full flex items-center justify-center">
          <FleetMap ref={mapRef} />
        </div>

        {/* UI Overlay Layer */}
        <div className="absolute inset-0 w-full max-w-7xl mx-auto px-6 pointer-events-none">
          
          {/* Phase 1: Ambient Fleet Text */}
          <div ref={heroTextRef} className="absolute inset-x-6 top-1/3 text-center">
            <h1 className="text-5xl md:text-7xl font-display font-medium tracking-tight mb-6">
              The fleet is <span className="text-fg-green">alive.</span>
            </h1>
            <p className="text-xl md:text-2xl text-white/60 font-light max-w-2xl mx-auto">
              FleetGuard continuously translates raw movement into operational understanding.
            </p>
          </div>

          {/* Phase 2 & 3: Trip & Event Context Panel */}
          <div 
            ref={tripPanelRef} 
            className="absolute top-1/3 left-6 md:left-24 w-80 bg-surface-inverted/90 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-2xl pointer-events-auto"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
                <Route className="w-5 h-5 text-white/80" />
              </div>
              <div>
                <p className="text-white font-medium text-sm">Trip #8402</p>
                <p className="text-xs text-white/50">Mumbai → Pune</p>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-white/60">Driver</span>
                <span className="text-white font-medium">Ravi Kumar</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-white/60">Status</span>
                <span className="text-fg-green font-medium">In Transit</span>
              </div>
            </div>

            {/* This section expands during Phase 3 */}
            <div ref={varianceSectionRef} className="overflow-hidden">
              <div className="pt-4 border-t border-white/10 space-y-4">
                <div className="inline-flex px-2 py-1 bg-amber-500/20 text-amber-500 text-[10px] font-bold uppercase tracking-widest rounded border border-amber-500/30">
                  Anomaly Detected
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/5 rounded-lg p-3">
                    <p className="text-[10px] text-white/40 uppercase mb-1">Expected Burn</p>
                    <p className="text-lg font-medium">82L</p>
                  </div>
                  <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                    <p className="text-[10px] text-amber-500/60 uppercase mb-1">Actual Burn</p>
                    <p className="text-lg font-medium text-amber-500">127L</p>
                  </div>
                </div>
                <p className="text-xs text-white/50 leading-relaxed">
                  Sudden drop detected while stationary. Diverges 45L from historical route profile.
                </p>
              </div>
            </div>
          </div>

          {/* Phase 4: Operations Engine Panel */}
          <div 
            ref={opsEngineRef} 
            className="absolute top-1/4 right-6 md:right-24 w-80 bg-white rounded-2xl p-5 shadow-2xl pointer-events-auto"
          >
            <div className="flex items-center gap-2 mb-6 border-b border-border pb-4">
              <Zap className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-semibold text-content uppercase tracking-widest">Operations Engine</span>
            </div>
            
            <div className="mb-6">
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-widest text-red-600 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Financial Exposure
                </span>
                <span className="text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded text-red-700 bg-red-50">
                  Critical
                </span>
              </div>
              <div className="flex items-end gap-2">
                <h4 className="text-3xl font-bold text-content tracking-tight">₹4,500</h4>
                <span className="text-xs text-red-500 font-medium pb-1 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-0.5" /> +₹4,500
                </span>
              </div>
            </div>

            <p className="text-xs text-content-secondary leading-relaxed p-3 bg-surface-secondary rounded-lg border border-border">
              Exposure increased directly due to MH-04-1234 variance. Margin impact estimated at -0.8% for current period.
            </p>
          </div>

          {/* Phase 5: AI Copilot Panel */}
          <div 
            ref={copilotRef}
            className="absolute bottom-12 left-1/2 w-full max-w-2xl bg-surface border border-border rounded-2xl shadow-2xl pointer-events-auto flex flex-col overflow-hidden"
          >
            <div className="flex items-center justify-between px-4 py-3 bg-surface-base border-b border-border">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-brand-50 flex items-center justify-center border border-brand-100">
                  <Sparkles className="w-3 h-3 text-fg-green" />
                </div>
                <span className="text-sm font-semibold text-content">FleetGuard Copilot</span>
              </div>
              <span className="text-[10px] text-fg-green font-medium uppercase tracking-widest bg-brand-50 px-2 py-1 rounded">Context Linked</span>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-sm text-content-secondary leading-relaxed">
                I've linked the <span className="font-medium text-content">45L fuel variance</span> on MH-04-1234 to the <span className="font-medium text-content">₹4,500 exposure</span>. 
                The drop occurred 20 mins after a logged purchase at Reliance Pump. This profile matches theft.
              </p>
              <div className="grid grid-cols-2 gap-3 pt-2">
                <button className="flex items-center justify-center gap-2 w-full p-2.5 rounded-lg bg-surface-secondary border border-border hover:border-fg-green transition-colors text-sm font-medium text-content">
                  <MessageSquare className="w-4 h-4 text-content-muted" />
                  Message Driver
                </button>
                <button className="flex items-center justify-center gap-2 w-full p-2.5 rounded-lg bg-fg-green text-white transition-colors text-sm font-medium shadow-md">
                  <ArrowRight className="w-4 h-4" />
                  Flag for Investigation
                </button>
              </div>
            </div>
          </div>

          {/* Phase 6: Final Macro Reveal */}
          <div ref={finalRevealRef} className="absolute inset-x-6 top-1/2 text-center pointer-events-none">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-white/80 text-xs font-semibold uppercase tracking-widest mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-fg-green animate-pulse" />
              System Active
            </div>
            <h2 className="text-5xl md:text-7xl font-display font-medium tracking-tight mb-6">
              FleetGuard <span className="text-fg-green">understands.</span>
            </h2>
            <p className="text-xl md:text-2xl text-white/60 font-light max-w-2xl mx-auto mb-10">
              Continuously processing trips, events, and expenses across your entire ecosystem.
            </p>
            <a 
              href="/dashboard"
              className="inline-flex px-8 py-4 bg-fg-green text-surface-inverted font-semibold rounded-xl hover:bg-fg-green-bright transition-colors shadow-[0_0_20px_rgba(34,197,94,0.3)] pointer-events-auto"
            >
              Open Dashboard
            </a>
          </div>

        </div>
      </div>
    </div>
  );
}
