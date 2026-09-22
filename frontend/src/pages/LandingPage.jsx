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
      <LandingNav isScrolled={isScrolled} />
      
      {/* Page Sections */}
      <main>
        <div data-nav-theme="dark"><HeroSection /></div>
        <div data-nav-theme="light"><ChallengeSection /></div>
        <div data-nav-theme="light"><CostCalculatorSection /></div>
        <div data-nav-theme="light"><IntelligenceModelSection /></div>
        <div data-nav-theme="light"><DifferentiationSection /></div>
        <div data-nav-theme="light"><TripIntelligenceSection /></div>
        <div data-nav-theme="light"><EnginesSection /></div>
        <div data-nav-theme="dark"><StoryJourney /></div>
        <div data-nav-theme="light"><AppsSection /></div>
        <div data-nav-theme="light"><ProductAndOutcomesSection /></div>
      </main>

      {/* Final CTA & Footer */}
      <div data-nav-theme="dark">
        <FooterSection />
      </div>
    </div>
  );
}
