import React, { useState, useEffect } from 'react';
import { LandingNav } from './landing/LandingNav';
import { HeroSection } from './landing/HeroSection';
import { ChallengeSection } from './landing/ChallengeSection';
import { CostCalculatorSection } from './landing/CostCalculatorSection';
import { IntelligenceModelSection } from './landing/IntelligenceModelSection';
import { TripIntelligenceSection } from './landing/TripIntelligenceSection';
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
    <div className="min-h-screen bg-fg-dark font-sans text-white relative selection:bg-fg-green/20 selection:text-fg-green overflow-x-hidden">
      {/* Navigation Layer */}
      <LandingNav isScrolled={isScrolled} />
      
      {/* Page Sections */}
      <main>
        <HeroSection />
        <ChallengeSection />
        <CostCalculatorSection />
        <IntelligenceModelSection />
        <TripIntelligenceSection />
        <EnginesSection />
        <StoryJourney />
        <AppsSection />
        <ProductAndOutcomesSection />
      </main>

      {/* Final CTA & Footer */}
      <FooterSection />
    </div>
  );
}
