import React, { useState, useEffect } from 'react';
import { LandingNav } from './landing/LandingNav';
import { HeroSection } from './landing/HeroSection';
import { ChallengeSection } from './landing/ChallengeSection';
import { CostCalculatorSection } from './landing/CostCalculatorSection';
import { IntelligenceModelSection } from './landing/IntelligenceModelSection';
import { TripIntelligenceSection } from './landing/TripIntelligenceSection';
import { DifferentiationSection } from './landing/DifferentiationSection';
import { EnginesSection } from './landing/EnginesSection';
import { StoryJourney } from './landing/StoryJourney';
import { AppsSection } from './landing/AppsSection';
import { ProductAndOutcomesSection } from './landing/ProductAndOutcomesSection';
import FooterSection from './landing/FooterSection';

export default function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [demoOpen, setDemoOpen] = useState(false);
  const [demoPrepared, setDemoPrepared] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // init
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-fg-dark font-sans text-white relative selection:bg-fg-green/20 selection:text-fg-green overflow-x-clip">
      {/* Navigation Layer */}
      <LandingNav isScrolled={isScrolled} onDemo={() => { setDemoPrepared(false); setDemoOpen(true); }} />
      
      {/* Page Sections */}
      <main>
        <div data-nav-theme="dark"><HeroSection onDemo={() => { setDemoPrepared(false); setDemoOpen(true); }} /></div>
        <div id="product" data-nav-theme="light"><ChallengeSection /></div>
        <div data-nav-theme="light"><CostCalculatorSection /></div>
        <div id="intelligence" data-nav-theme="light"><IntelligenceModelSection /></div>
        <div data-nav-theme="light"><DifferentiationSection /></div>
        <div id="operations" data-nav-theme="light"><TripIntelligenceSection /></div>
        <div id="copilot" data-nav-theme="light"><EnginesSection /></div>
        <div data-nav-theme="dark"><StoryJourney /></div>
        <div id="platform" data-nav-theme="light"><AppsSection /></div>
        <div id="vision" data-nav-theme="light"><ProductAndOutcomesSection /></div>
      </main>

      {/* Final CTA & Footer */}
      <div data-nav-theme="dark">
        <FooterSection onDemo={() => { setDemoPrepared(false); setDemoOpen(true); }} />
      </div>
      {demoOpen && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="demo-request-title" onKeyDown={(event) => { if (event.key === 'Escape') setDemoOpen(false); }} tabIndex={-1} onClick={(event) => { if (event.target === event.currentTarget) setDemoOpen(false); }}>
          <form className="w-full max-w-md rounded-2xl border border-white/10 bg-[#101a14] p-6 text-white shadow-2xl" onSubmit={(event) => { event.preventDefault(); setDemoPrepared(true); }}>
            <div className="flex items-start justify-between"><div><p className="text-[10px] uppercase tracking-[0.2em] text-emerald-300">the vahan</p><h2 id="demo-request-title" className="mt-2 text-2xl">Request a demo</h2></div><button type="button" aria-label="Close demo request" onClick={() => setDemoOpen(false)} className="text-xl text-white/50">×</button></div>
            <div className="mt-6 space-y-3">{['Name', 'Company', 'Email'].map((label) => <label key={label} className="block text-xs text-white/60">{label}<input required type={label === 'Email' ? 'email' : 'text'} className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none" /></label>)}</div>
            <p className="mt-4 text-xs leading-5 text-white/45">This prepares your details locally. No request is sent until a submission service is connected.</p>
            {demoPrepared && <p role="status" className="mt-4 rounded-lg border border-emerald-300/20 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-200">Demo request prepared.</p>}
            <button type="submit" className="mt-5 w-full rounded-lg bg-emerald-400 py-3 text-sm font-semibold text-[#07110c]">Prepare demo request</button>
          </form>
        </div>
      )}
    </div>
  );
}
