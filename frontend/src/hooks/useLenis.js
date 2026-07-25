import { useEffect, useRef } from 'react';
import Lenis from 'lenis';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

/**
 * Initializes Lenis smooth scrolling and syncs it with GSAP ScrollTrigger.
 * 
 * - lerp: 0.075 gives a buttery, slightly slow momentum feel
 * - duration: 1.2 controls the deceleration curve
 * - Lenis RAF is linked to GSAP's ticker for perfect sync with ScrollTrigger
 * 
 * Returns the Lenis instance for external use (e.g., scrollTo).
 */
export default function useLenis() {
  const lenisRef = useRef(null);

  useEffect(() => {
    const lenis = new Lenis({
      lerp: 0.075,
      duration: 1.2,
      smoothWheel: true,
      wheelMultiplier: 0.8,
      touchMultiplier: 1.5,
      infinite: false,
    });

    lenisRef.current = lenis;

    // Sync Lenis scroll position with GSAP ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update);

    // Use GSAP's ticker as the animation loop driver for Lenis
    const tickerCallback = (time) => {
      lenis.raf(time * 1000); // GSAP ticker time is in seconds, Lenis expects ms
    };
    gsap.ticker.add(tickerCallback);

    // Disable GSAP's default lag smoothing so it doesn't fight Lenis
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(tickerCallback);
      lenis.destroy();
      lenisRef.current = null;
    };
  }, []);

  return lenisRef;
}
