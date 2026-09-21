import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ChevronRight } from 'lucide-react';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';

export function LandingNav({ isScrolled = false }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { t } = useLanguage();

  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => { document.body.style.overflow = 'auto'; };
  }, [mobileMenuOpen]);

  const navLinks = [
    { label: t('Platform'), href: '#' }, 
    { label: t('Intelligence'), href: '#' },
    { label: t('Apps'), href: '#' },
    { label: t('Company'), href: '#' },
  ];

  const handleNavClick = (e, href) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    // Add real smooth scroll to sections if needed later
  };

  const themeClass = isScrolled
    ? 'text-content hover:text-fg-green'
    : 'text-white hover:text-fg-green';

  return (
    <>
      <nav
        className={cn(
          'fixed top-0 inset-x-0 z-[100] transition-all duration-300',
          isScrolled
            ? 'bg-white/90 backdrop-blur-md border-b border-border shadow-sm py-3'
            : 'bg-transparent py-5'
        )}
      >
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          
          {/* Logo */}
          <a href="/" className="flex items-center gap-2.5 z-50 relative group">
            <div className="w-8 h-8 rounded bg-fg-green flex items-center justify-center relative overflow-hidden transition-all group-hover:scale-105">
              <span className="text-white font-bold text-sm">V</span>
            </div>
            <span className={cn(
              "font-sans font-bold text-xl tracking-tight transition-colors duration-300",
              isScrolled ? "text-content" : "text-white"
            )}>
              the vaahan
            </span>
          </a>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            <div className="flex items-center gap-6">
              {navLinks.map((link, i) => (
                <a
                  key={i}
                  href={link.href}
                  onClick={(e) => handleNavClick(e, link.href)}
                  className={cn("text-sm font-medium transition-colors", themeClass)}
                >
                  {link.label}
                </a>
              ))}
            </div>

            <div className={cn("flex items-center gap-4 pl-6 border-l", isScrolled ? "border-border" : "border-white/20")}>
              <LanguageSelector variant={isScrolled ? 'dark' : 'light'} />
              <a 
                href="/login"
                className={cn("text-sm font-medium transition-colors", themeClass)}
              >
                {t('Login')}
              </a>
              <a
                href="/dashboard"
                className="group relative px-5 py-2.5 bg-fg-green text-white text-sm font-semibold rounded-full overflow-hidden transition-transform hover:-translate-y-0.5"
              >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
                <span className="relative z-10 flex items-center gap-1.5">
                  {t('Open Dashboard')}
                  <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </span>
              </a>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className="md:hidden p-2 z-50 relative"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className={cn("w-6 h-6", isScrolled ? "text-content" : "text-white")} />
            ) : (
              <Menu className={cn("w-6 h-6", isScrolled ? "text-content" : "text-white")} />
            )}
          </button>
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, backdropFilter: 'blur(0px)' }}
            animate={{ opacity: 1, backdropFilter: 'blur(16px)' }}
            exit={{ opacity: 0, backdropFilter: 'blur(0px)' }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-40 bg-surface-inverted/95 md:hidden"
          >
            <div className="flex flex-col h-full pt-24 pb-8 px-6">
              <div className="flex flex-col gap-6 text-xl font-medium text-white mb-auto">
                {navLinks.map((link, i) => (
                  <motion.a
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.05 }}
                    key={i}
                    href={link.href}
                    onClick={(e) => handleNavClick(e, link.href)}
                    className="hover:text-fg-green transition-colors"
                  >
                    {link.label}
                  </motion.a>
                ))}
              </div>

              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-6 pt-6 border-t border-white/10"
              >
                <div className="flex items-center justify-between">
                  <span className="text-white/60 text-sm">{t('Language')}</span>
                  <LanguageSelector variant="light" />
                </div>
                
                <a
                  href="/login"
                  className="block w-full text-center py-3 text-white font-medium hover:text-fg-green transition-colors"
                >
                  {t('Login')}
                </a>
                
                <a
                  href="/dashboard"
                  className="flex items-center justify-center gap-2 w-full py-3.5 bg-fg-green text-white font-semibold rounded-full"
                >
                  {t('Open Dashboard')}
                  <ChevronRight className="w-4 h-4" />
                </a>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
