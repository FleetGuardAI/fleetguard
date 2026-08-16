import { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';

const LANGUAGES = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'hi', label: 'हिन्दी', flag: '🇮🇳' },
  { code: 'ta', label: 'தமிழ்', flag: '🇮🇳' },
  { code: 'te', label: 'తెలుగు', flag: '🇮🇳' },
  { code: 'kn', label: 'ಕನ್ನಡ', flag: '🇮🇳' },
  { code: 'mr', label: 'मराठी', flag: '🇮🇳' },
  { code: 'gu', label: 'ગુજરાતી', flag: '🇮🇳' },
  { code: 'bn', label: 'বাংলা', flag: '🇮🇳' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
  { code: 'es', label: 'Español', flag: '🇪🇸' },
  { code: 'ar', label: 'العربية', flag: '🇸🇦' },
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
];

/**
 * Language selector dropdown.
 * @param {'light'|'dark'|'adaptive'} variant
 *   - 'light'  → white text (for dark backgrounds)
 *   - 'dark'   → slate text (for white backgrounds like landing-page navbar)
 *   - 'adaptive' → uses CSS-variable-based theming (dashboard)
 */
export function LanguageSelector({ variant = 'dark', className }) {
  const [open, setOpen] = useState(false);
  const { lang, setLang, t } = useLanguage();
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (code) => {
    setLang(code);
    setOpen(false);
  };

  const current = LANGUAGES.find((l) => l.code === lang) || LANGUAGES[0];

  const triggerColors = {
    light: 'text-white/80 hover:text-white hover:bg-white/10',
    dark: 'text-slate-600 hover:text-slate-900 hover:bg-slate-100',
    adaptive: 'text-content-secondary hover:text-content hover:bg-surface-tertiary',
    'glass-transparent': 'text-white/90 hover:text-white bg-white/10 hover:bg-white/15 border border-white/15 rounded-full shadow-sm backdrop-blur-md',
    'glass-scrolled': 'text-slate-700 hover:text-slate-900 bg-slate-100/80 hover:bg-slate-200/50 border border-slate-200/80 rounded-full shadow-sm backdrop-blur-md',
  };

  return (
    <div ref={ref} className={cn('relative', className)}>
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-[11px] font-bold transition-all duration-200',
          triggerColors[variant] || triggerColors['glass-transparent']
        )}
        aria-label="Select language"
      >
        <Globe className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">{current.flag} {current.label}</span>
        <span className="sm:hidden">{current.flag}</span>
        <ChevronDown className={cn('w-3 h-3 transition-transform duration-200', open && 'rotate-180')} />
      </button>

      {open && (
        <div
          className={cn(
            'absolute top-full right-0 mt-2 z-50 w-52 py-1.5 rounded-xl shadow-xl border animate-fade-in',
            'bg-white border-slate-200 overflow-hidden',
            variant === 'adaptive' && 'bg-white border-border',
            variant.startsWith('glass') && 'bg-white/95 backdrop-blur-lg border-slate-200/80 shadow-2xl'
          )}
        >
          <div className={cn(
            'px-3 py-2 border-b',
            variant === 'adaptive' ? 'border-border' : 'border-slate-100'
          )}>
            <p className={cn(
              'text-[10px] font-bold uppercase tracking-widest',
              variant === 'adaptive' ? 'text-content-muted' : 'text-slate-400'
            )}>
              {t('dash.selectLanguage')}
            </p>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {LANGUAGES.map((langItem) => (
              <button
                key={langItem.code}
                onClick={() => handleSelect(langItem.code)}
                className={cn(
                  'w-full flex items-center gap-2.5 px-3 py-2 text-sm transition-colors text-left',
                  lang === langItem.code
                    ? 'bg-brand-50 text-brand-700 font-semibold'
                    : variant === 'adaptive'
                      ? 'text-content hover:bg-surface-tertiary'
                      : 'text-slate-700 hover:bg-slate-50'
                )}
              >
                <span className="text-base">{langItem.flag}</span>
                <span className="flex-1">{langItem.label}</span>
                {lang === langItem.code && <Check className="w-3.5 h-3.5 text-brand-500" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
