import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import translations from '@/i18n/translations';

const LanguageContext = createContext(null);

const STORAGE_KEY = 'fleetguard_lang';

/**
 * LanguageProvider — wraps the app and provides:
 *  - `lang`       – current language code (e.g. 'en', 'hi')
 *  - `setLang`    – function to change the language
 *  - `t(key)`     – returns the translated string for the current lang
 */
export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) || 'en'; } catch { return 'en'; }
  });

  const setLang = useCallback((code) => {
    setLangState(code);
    try { localStorage.setItem(STORAGE_KEY, code); } catch {}
  }, []);

  // Also update the html lang attribute for accessibility / SEO
  useEffect(() => {
    document.documentElement.lang = lang;
    // Set dir for RTL languages
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  }, [lang]);

  const t = useCallback((key) => {
    const dict = translations[lang] || translations.en;
    return dict[key] || translations.en[key] || key;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

/**
 * Hook to access the language context.
 * Returns { lang, setLang, t }
 */
export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return ctx;
}
