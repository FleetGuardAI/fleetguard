import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

/**
 * Animation presets matching the reference video:
 * - Slow ease-in-out timing
 * - Vertical translation (20–60px)
 * - Subtle scale (0.95–1.0)
 * - Opacity 0→1
 * - Staggered reveals
 */
const ANIMATION_DEFAULTS = {
  duration: 1,
  ease: 'power2.out',
};

const TRIGGER_DEFAULTS = {
  start: 'top 85%',
  end: 'bottom 20%',
  toggleActions: 'play none none none', // animate once on enter
};

/**
 * Central hook that registers all GSAP ScrollTrigger animations
 * for the FleetGuard landing page.
 * 
 * Uses data-animate attributes to target elements:
 * - data-animate="fade-up"
 * - data-animate="fade-in"
 * - data-animate="slide-left"
 * - data-animate="slide-right"
 * - data-animate="scale-in"
 * - data-animate="stagger-children"
 * 
 * Uses data-animate-delay for custom delays (e.g., "0.2")
 */
export default function useScrollAnimations(containerRef) {
  const animationsRef = useRef([]);

  useEffect(() => {
    if (!containerRef?.current) return;

    const ctx = gsap.context(() => {
      const container = containerRef.current;

      // ——— HERO PARALLAX FADE-OUT ———
      const heroSection = container.querySelector('#hero');
      const heroContent = container.querySelector('[data-hero-content]');
      const heroBg = container.querySelector('[data-hero-bg]');

      if (heroSection && heroContent) {
        gsap.to(heroContent, {
          y: -60,
          opacity: 0,
          ease: 'none',
          scrollTrigger: {
            trigger: heroSection,
            start: 'top top',
            end: 'bottom top',
            scrub: 0.5, // smooth scroll-linked
          },
        });
      }

      if (heroSection && heroBg) {
        gsap.to(heroBg, {
          y: -40,
          scale: 1.05,
          ease: 'none',
          scrollTrigger: {
            trigger: heroSection,
            start: 'top top',
            end: 'bottom top',
            scrub: 0.8, // slightly slower than content for parallax depth
          },
        });
      }

      // ——— FADE-UP REVEALS ———
      const fadeUpElements = container.querySelectorAll('[data-animate="fade-up"]');
      fadeUpElements.forEach((el) => {
        const delay = parseFloat(el.dataset.animateDelay) || 0;
        gsap.fromTo(
          el,
          { y: 45, opacity: 0, scale: 0.98 },
          {
            y: 0,
            opacity: 1,
            scale: 1,
            delay,
            ...ANIMATION_DEFAULTS,
            scrollTrigger: {
              trigger: el,
              ...TRIGGER_DEFAULTS,
            },
          }
        );
      });

      // ——— SIMPLE FADE-IN ———
      const fadeInElements = container.querySelectorAll('[data-animate="fade-in"]');
      fadeInElements.forEach((el) => {
        const delay = parseFloat(el.dataset.animateDelay) || 0;
        gsap.fromTo(
          el,
          { opacity: 0 },
          {
            opacity: 1,
            delay,
            duration: 0.8,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: el,
              ...TRIGGER_DEFAULTS,
            },
          }
        );
      });

      // ——— SLIDE FROM LEFT ———
      const slideLeftElements = container.querySelectorAll('[data-animate="slide-left"]');
      slideLeftElements.forEach((el) => {
        const delay = parseFloat(el.dataset.animateDelay) || 0;
        gsap.fromTo(
          el,
          { x: -60, opacity: 0 },
          {
            x: 0,
            opacity: 1,
            delay,
            ...ANIMATION_DEFAULTS,
            scrollTrigger: {
              trigger: el,
              ...TRIGGER_DEFAULTS,
            },
          }
        );
      });

      // ——— SLIDE FROM RIGHT ———
      const slideRightElements = container.querySelectorAll('[data-animate="slide-right"]');
      slideRightElements.forEach((el) => {
        const delay = parseFloat(el.dataset.animateDelay) || 0;
        gsap.fromTo(
          el,
          { x: 60, opacity: 0 },
          {
            x: 0,
            opacity: 1,
            delay,
            ...ANIMATION_DEFAULTS,
            scrollTrigger: {
              trigger: el,
              ...TRIGGER_DEFAULTS,
            },
          }
        );
      });

      // ——— SCALE-IN (for dashboard/product showcases) ———
      const scaleInElements = container.querySelectorAll('[data-animate="scale-in"]');
      scaleInElements.forEach((el) => {
        const delay = parseFloat(el.dataset.animateDelay) || 0;
        gsap.fromTo(
          el,
          { y: 50, opacity: 0, scale: 0.95 },
          {
            y: 0,
            opacity: 1,
            scale: 1,
            delay,
            duration: 1.1,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: el,
              ...TRIGGER_DEFAULTS,
            },
          }
        );
      });

      // ——— STAGGER CHILDREN (card grids) ———
      const staggerContainers = container.querySelectorAll('[data-animate="stagger-children"]');
      staggerContainers.forEach((containerEl) => {
        const staggerDelay = parseFloat(containerEl.dataset.staggerDelay) || 0.15;
        const children = containerEl.children;

        if (children.length === 0) return;

        gsap.fromTo(
          children,
          { y: 40, opacity: 0, scale: 0.98 },
          {
            y: 0,
            opacity: 1,
            scale: 1,
            ...ANIMATION_DEFAULTS,
            stagger: staggerDelay,
            scrollTrigger: {
              trigger: containerEl,
              ...TRIGGER_DEFAULTS,
            },
          }
        );
      });

      // ——— STICKY PINNED "HOW IT WORKS" SECTION ———
      const pinnedSection = container.querySelector('[data-animate="pin-section"]');
      const pinnedSteps = container.querySelectorAll('[data-pin-step]');
      const laserLine = container.querySelector('[data-animate-laser]');

      if (pinnedSection && pinnedSteps.length > 0) {
        // Pin the section
        const pinTrigger = ScrollTrigger.create({
          trigger: pinnedSection,
          start: 'top 15%',
          end: `+=${window.innerHeight * 1.2}`,
          pin: true,
          pinSpacing: true,
          anticipatePin: 1,
        });

        // Stagger the steps within the pinned section
        const pinTimeline = gsap.timeline({
          scrollTrigger: {
            trigger: pinnedSection,
            start: 'top 15%',
            end: `+=${window.innerHeight * 1.2}`,
            scrub: 0.8,
          },
        });

        // Hide all steps initially
        gsap.set(pinnedSteps, { y: 30, opacity: 0, scale: 0.96 });

        // Animate laser line growing
        if (laserLine) {
          gsap.set(laserLine, { scaleX: 0, transformOrigin: 'left center' });
        }

        pinnedSteps.forEach((step, i) => {
          const startPos = i / pinnedSteps.length;
          pinTimeline.to(
            step,
            {
              y: 0,
              opacity: 1,
              scale: 1,
              duration: 0.3,
              ease: 'power2.out',
            },
            startPos
          );

          // Grow laser line alongside steps
          if (laserLine && i < pinnedSteps.length - 1) {
            pinTimeline.to(
              laserLine,
              {
                scaleX: (i + 1) / (pinnedSteps.length - 1),
                duration: 0.2,
                ease: 'none',
              },
              startPos + 0.15
            );
          }
        });

        animationsRef.current.push(pinTrigger);
      }

      // ——— HERO STATS STAGGER ———
      const heroStats = container.querySelector('[data-animate="hero-stats"]');
      if (heroStats) {
        const statItems = heroStats.children;
        gsap.fromTo(
          statItems,
          { y: 25, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.8,
            ease: 'power2.out',
            stagger: 0.1,
            scrollTrigger: {
              trigger: heroStats,
              start: 'top 90%',
              toggleActions: 'play none none none',
            },
          }
        );
      }

      // ——— INTEGRATIONS LOGO STAGGER ———
      const logosContainer = container.querySelector('[data-animate="logos-stagger"]');
      if (logosContainer) {
        const logos = logosContainer.children;
        gsap.fromTo(
          logos,
          { opacity: 0, y: 10 },
          {
            opacity: 0.4, // they were at 40% opacity by design
            y: 0,
            duration: 0.6,
            ease: 'power2.out',
            stagger: 0.1,
            scrollTrigger: {
              trigger: logosContainer,
              start: 'top 90%',
              toggleActions: 'play none none none',
            },
          }
        );
      }

      // ——— CTA SECTION SEQUENTIAL REVEAL ———
      const ctaCard = container.querySelector('[data-animate="cta-reveal"]');
      if (ctaCard) {
        const ctaChildren = ctaCard.querySelectorAll('[data-cta-child]');
        gsap.fromTo(
          ctaCard,
          { y: 40, opacity: 0, scale: 0.96 },
          {
            y: 0,
            opacity: 1,
            scale: 1,
            duration: 1,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: ctaCard,
              start: 'top 85%',
              toggleActions: 'play none none none',
            },
          }
        );

        if (ctaChildren.length > 0) {
          gsap.fromTo(
            ctaChildren,
            { y: 20, opacity: 0 },
            {
              y: 0,
              opacity: 1,
              duration: 0.8,
              ease: 'power2.out',
              stagger: 0.12,
              scrollTrigger: {
                trigger: ctaCard,
                start: 'top 80%',
                toggleActions: 'play none none none',
              },
            }
          );
        }
      }

      // ——— FOOTER COLUMNS STAGGER ———
      const footerGrid = container.querySelector('[data-animate="footer-stagger"]');
      if (footerGrid) {
        const footerCols = footerGrid.children;
        gsap.fromTo(
          footerCols,
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.8,
            ease: 'power2.out',
            stagger: 0.1,
            scrollTrigger: {
              trigger: footerGrid,
              start: 'top 90%',
              toggleActions: 'play none none none',
            },
          }
        );
      }

    }, containerRef);

    return () => {
      ctx.revert(); // Clean up all GSAP animations and ScrollTriggers
      animationsRef.current.forEach((st) => st.kill?.());
      animationsRef.current = [];
    };
  }, [containerRef]);
}
