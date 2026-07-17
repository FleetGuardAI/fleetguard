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

  // Global DOM-based Auto-Translator
  useEffect(() => {
    const translateTextNode = (node) => {
      const text = node.textContent;
      if (!text) return;
      if (!/[a-zA-Z]/.test(text)) return;
      
      if (node._origText === undefined) {
        node._origText = text;
      }
      
      const trimmed = node._origText.trim();
      const translated = t(trimmed);
      if (translated !== trimmed) {
        const leading = node._origText.match(/^\s*/)[0];
        const trailing = node._origText.match(/\s*$/)[0];
        node.textContent = leading + translated + trailing;
      }
    };

    const translateInput = (input) => {
      if (input.placeholder) {
        if (input._origPlaceholder === undefined) {
          input._origPlaceholder = input.placeholder;
        }
        const trimmed = input._origPlaceholder.trim();
        const translated = t(trimmed);
        if (translated !== trimmed) {
          input.placeholder = translated;
        }
      }
    };

    const traverseAndTranslate = (root) => {
      if (!root) return;
      
      const walker = document.createTreeWalker(
        root,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: (node) => {
            const parent = node.parentElement;
            if (parent) {
              const tag = parent.tagName;
              if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'TEXTAREA' || parent.closest('.no-translate') || parent.getAttribute('translate') === 'no') {
                return NodeFilter.FILTER_REJECT;
              }
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );
      
      let node;
      while ((node = walker.nextNode())) {
        translateTextNode(node);
      }
      
      const inputs = root.getElementsByTagName('INPUT');
      for (let i = 0; i < inputs.length; i++) {
        translateInput(inputs[i]);
      }
    };

    // Translate initial DOM state
    traverseAndTranslate(document.body);

    // Watch for dynamic React mounts/updates
    const observer = new MutationObserver((mutations) => {
      observer.disconnect();
      try {
        for (const mutation of mutations) {
          if (mutation.type === 'childList') {
            for (let i = 0; i < mutation.addedNodes.length; i++) {
              const node = mutation.addedNodes[i];
              if (node.nodeType === Node.TEXT_NODE) {
                translateTextNode(node);
              } else if (node.nodeType === Node.ELEMENT_NODE) {
                traverseAndTranslate(node);
              }
            }
          } else if (mutation.type === 'characterData') {
            translateTextNode(mutation.target);
          }
        }
      } finally {
        observer.observe(document.body, {
          childList: true,
          subtree: true,
          characterData: true
        });
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true
    });

    return () => observer.disconnect();
  }, [lang, t]);

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
