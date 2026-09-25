import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ChevronRight } from 'lucide-react';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';

export function LandingNav({ onDemo }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [navTheme, setNavTheme] = useState('dark');
  const [isAtTop, setIsAtTop] = useState(true);
  
  const navThemeRef = useRef('dark');
  const isAtTopRef = useRef(true);

  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => { document.body.style.overflow = 'auto'; };
  }, [mobileMenuOpen]);

  useEffect(() => {
    const handleScroll = () => {
      // Check if at the very top
      const currentlyAtTop = window.scrollY < 20;
      if (currentlyAtTop !== isAtTopRef.current) {
        isAtTopRef.current = currentlyAtTop;
        setIsAtTop(currentlyAtTop);
      }

      // Detect background section via robust midpoint sampling
      // Y=80 is safely inside the navbar height
      const elements = document.elementsFromPoint(window.innerWidth / 2, 80);
      for (const el of elements) {
        const wrapper = el.closest('[data-nav-theme]');
        if (wrapper) {
          const theme = wrapper.getAttribute('data-nav-theme');
          if (theme !== navThemeRef.current) {
            navThemeRef.current = theme;
            setNavTheme(theme);
          }
          break; // Stop after finding the first valid theme wrapper
        }
      }
    };

    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    // Initialize immediately
    handleScroll();
    
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const navLinks = [
    { label: 'Product', href: '#product' },
    { label: 'Intelligence', href: '#intelligence' },
    { label: 'Operations', href: '#operations' },
    { label: 'AI Copilot', href: '#copilot' },
    { label: 'Platform', href: '#platform' },
    { label: 'Vision', href: '#vision' },
  ];

  const handleNavClick = (e, href) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const isDark = navTheme === 'dark';

  // Compute transitioning styles
  const navClasses = cn(
    "max-w-6xl mx-auto rounded-full py-3 px-6 pointer-events-auto flex items-center justify-between transition-all duration-400 ease-in-out",
    isAtTop && isDark
      ? "bg-transparent border border-transparent shadow-none" 
      : isDark 
        ? "bg-[#05080c]/70 backdrop-blur-lg shadow-[0_8px_30px_rgb(0,0,0,0.4)] border border-white/10"
        : "bg-white/85 backdrop-blur-lg shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-[#14281e]/10"
  );

  const textClasses = cn(
    "text-[13px] font-semibold transition-colors duration-400 ease-in-out",
    isDark ? "text-white/90 hover:text-fg-green" : "text-slate-900 hover:text-fg-green"
  );

  const dashClasses = cn(
    "text-[13px] font-bold transition-colors duration-400 ease-in-out",
    isDark ? "text-white/90 hover:text-fg-green" : "text-slate-900 hover:text-fg-green"
  );

  const btnClasses = cn(
    "px-5 py-2.5 text-[13px] font-bold rounded-full transition-all duration-400 ease-in-out shadow-sm",
    isDark 
      ? "bg-fg-green hover:bg-fg-green-deep text-white shadow-fg-green/20" 
      : "bg-[#0f172a] hover:bg-[#1e293b] text-white shadow-slate-900/10"
  );

  return (
    <>
      <div className="fixed top-0 inset-x-0 z-[100] pt-4 px-4 pointer-events-none">
        <nav className={navClasses}>
          
          {/* Logo with optical color adjustment for light mode */}
          <a href="/" className="flex items-center z-50 pointer-events-auto">
            <img 
              src="/assets/the_vahan_logo.png" 
              alt="the vaahan" 
              className="h-8 object-contain transition-all duration-400 ease-in-out" 
              style={{ filter: !isDark ? 'invert(1) hue-rotate(180deg) brightness(0.6) contrast(1.2)' : 'none' }}
            />
          </a>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8 pointer-events-auto">
            <div className="flex items-center gap-8">
              {navLinks.map((link, i) => (
                <a
                  key={i}
                  href={link.href}
                  onClick={(e) => handleNavClick(e, link.href)}
                  className={textClasses}
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          <div className="hidden md:flex items-center gap-6 pointer-events-auto">
            <a 
              href="/dashboard"
              className={dashClasses}
            >
              Dashboard
            </a>
            <button
              type="button"
              onClick={onDemo}
              className={btnClasses}
            >
              Book a Demo
            </button>
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            className="md:hidden p-2 z-50 relative pointer-events-auto"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className={cn("w-6 h-6 transition-colors duration-400", isDark ? "text-white" : "text-slate-900")} />
            ) : (
              <Menu className={cn("w-6 h-6 transition-colors duration-400", isDark ? "text-white" : "text-slate-900")} />
            )}
          </button>
        </nav>
      </div>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, backdropFilter: 'blur(0px)' }}
            animate={{ opacity: 1, backdropFilter: 'blur(16px)' }}
            exit={{ opacity: 0, backdropFilter: 'blur(0px)' }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-40 bg-[#020617]/95 md:hidden pointer-events-auto"
          >
            <div className="flex flex-col h-full pt-28 pb-8 px-6">
              <div className="flex flex-col gap-6 text-xl font-medium text-white mb-auto">
                {navLinks.map((link, i) => (
                  <motion.a
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.05 }}
                    key={i}
                    href={link.href}
                    onClick={(e) => handleNavClick(e, link.href)}
                    className="hover:text-fg-green transition-colors font-semibold"
                  >
                    {link.label}
                  </motion.a>
                ))}
              </div>

              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-4 pt-6 border-t border-white/10"
              >
                  <a
                    href="/dashboard"
                  className="block w-full text-center py-3 text-white font-bold hover:text-fg-green transition-colors"
                >
                  Dashboard
                </a>
                
                <button
                  type="button"
                  onClick={() => { setMobileMenuOpen(false); onDemo?.(); }}
                  className="flex items-center justify-center w-full py-3.5 bg-fg-green text-white font-bold rounded-full hover:bg-fg-green-deep transition-colors"
                >
                  Book a Demo
                </button>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
