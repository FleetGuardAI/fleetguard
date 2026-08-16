import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, ChevronRight, ChevronUp, ArrowRight, ShieldAlert, AlertTriangle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import { ConfidenceRing } from './ConfidenceRing';

export function SignalDeck({ signals, onResolve }) {
  const { t } = useLanguage();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [expanded, setExpanded] = useState(false);

  if (!signals || signals.length === 0) return null;

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + 1) % signals.length);
    setExpanded(false);
  };

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - 1 + signals.length) % signals.length);
    setExpanded(false);
  };

  return (
    <div className="relative w-full h-full min-h-[400px] flex flex-col justify-center">
      {/* Deck Container */}
      <div className="relative w-full flex-1 perspective-1000">
        <AnimatePresence mode="popLayout">
          {signals.map((signal, index) => {
            // Calculate relative position (-1, 0, 1, etc.)
            const relativeIndex = (index - currentIndex + signals.length) % signals.length;
            
            // Only render front card and up to 2 cards behind
            if (relativeIndex > 2 && relativeIndex !== signals.length - 1) return null;

            const isFront = relativeIndex === 0;
            const isBehind1 = relativeIndex === 1;
            const isBehind2 = relativeIndex === 2;

            const zIndex = isFront ? 30 : isBehind1 ? 20 : 10;
            const scale = isFront ? 1 : isBehind1 ? 0.95 : 0.9;
            const yOffset = isFront ? 0 : isBehind1 ? 12 : 24;
            const opacity = isFront ? 1 : isBehind1 ? 0.6 : 0.3;

            return (
              <motion.div
                key={signal.id}
                layout
                initial={{ opacity: 0, y: 50, scale: 0.9 }}
                animate={{ opacity, y: yOffset, scale, zIndex }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ type: 'spring', stiffness: 260, damping: 20 }}
                className={cn(
                  'absolute top-0 left-0 w-full h-full flex flex-col bg-white border border-border shadow-elevated rounded-2xl p-6',
                  !isFront && 'pointer-events-none'
                )}
                style={{ transformOrigin: 'top center' }}
              >
                {/* Signal header */}
                <div className="flex items-center gap-3 text-xs text-content-secondary mb-4">
                  <span className="font-semibold text-brand-500 tracking-wider uppercase flex items-center gap-1.5">
                    <SparklesIcon /> {t("Predictive Signal")}
                  </span>
                  <span className={cn("w-1.5 h-1.5 rounded-full", 
                    signal.severity === 'high' ? 'bg-red-500' : 'bg-amber-500'
                  )} />
                  <span className={cn("font-semibold uppercase tracking-wider",
                    signal.severity === 'high' ? 'text-red-400' : 'text-amber-400'
                  )}>
                    {t(signal.priority || "Medium Priority")}
                  </span>
                  <span className="flex items-center gap-1 ml-auto">
                    <Clock className="w-3.5 h-3.5" />
                    {signal.time || '06:44 am'}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-xl font-light text-content tracking-tight leading-snug mb-3">
                  {signal.title}
                </h3>

                {/* Narrative */}
                <p className="text-sm text-content-secondary leading-relaxed font-light mb-5">
                  {signal.narrative}
                </p>

                {/* Metrics Rail */}
                <div className="flex items-center gap-8 flex-wrap py-4 border-y border-border/50">
                  <div>
                    <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Monthly Savings")}</span>
                    <p className="text-2xl font-bold text-content">
                      ₹{(signal.potentialSaving || signal.savings || 475).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Confidence")}</span>
                    <ConfidenceRing percentage={signal.confidence || 90} size={48} strokeWidth={3} />
                  </div>
                  <div>
                    <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Business Impact")}</span>
                    <span className="text-xs font-medium text-content bg-surface-secondary px-3 py-1.5 rounded-lg border border-border">
                      {signal.impact || 'Financial Risk'}
                    </span>
                  </div>
                </div>

                {/* AI Recommended Actions */}
                <div className="mt-4 flex-1 min-h-0 overflow-y-auto fg-scrollbar pr-2 pb-2">
                  <span className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest block mb-2">{t("AI Recommended Actions")}</span>
                  <ul className="space-y-2.5">
                    {signal.suggestions ? signal.suggestions.map((sug, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-[13px] text-content-secondary font-light leading-snug">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-1.5 flex-shrink-0" />
                        {sug}
                      </li>
                    )) : (
                      <>
                        <li className="flex items-start gap-2.5 text-[13px] text-content-secondary font-light leading-snug">
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-1.5 flex-shrink-0" />
                          {t("Run automated diagnostic check on vehicle telemetry to verify sensor integrity.")}
                        </li>
                        <li className="flex items-start gap-2.5 text-[13px] text-content-secondary font-light leading-snug">
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-1.5 flex-shrink-0" />
                          {t("Dispatch alert to driver's mobile app requesting visual status confirmation.")}
                        </li>
                        <li className="flex items-start gap-2.5 text-[13px] text-content-secondary font-light leading-snug">
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-1.5 flex-shrink-0" />
                          {t("Flag associated route segments for potential terrain-induced anomalies.")}
                        </li>
                      </>
                    )}
                  </ul>
                </div>

                {/* Expanded details */}
                {expanded && isFront && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="space-y-4 pt-5"
                  >
                    <div>
                      <h4 className="text-[10px] font-semibold text-content-muted uppercase tracking-widest mb-2">{t("Root Cause")}</h4>
                      <p className="text-sm text-content-secondary leading-relaxed bg-surface/50 p-3 rounded-lg border border-border/50">
                        {signal.rootCause || 'Potential fuel leak or unauthorized siphoning detected.'}
                      </p>
                    </div>
                  </motion.div>
                )}

                {/* Actions */}
                <div className="pt-5 mt-auto flex items-center justify-between flex-wrap gap-3">
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-sm font-medium text-content-secondary hover:text-content transition-colors flex items-center gap-1.5"
                  >
                    {expanded ? (
                      <>{t("Hide details")} <ChevronUp className="w-4 h-4" /></>
                    ) : (
                      <>{t("View telemetry log & root cause")} <ArrowRight className="w-4 h-4" /></>
                    )}
                  </button>
                  <motion.button
                    whileTap={{ scale: 0.96 }}
                    onClick={() => onResolve(signal.id)}
                    className="bg-brand-500 text-white font-semibold text-sm px-6 py-2.5 rounded-xl transition-all duration-200 hover:bg-brand-600 shadow-green flex items-center gap-1.5 cursor-pointer"
                  >
                    {t("Resolve Signal")}
                    <ChevronRight className="w-4 h-4" />
                  </motion.button>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Pagination Controls */}
      {signals.length > 1 && (
        <div className="flex items-center justify-center gap-4 mt-6 absolute -bottom-10 left-0 right-0">
          <button 
            onClick={handlePrev}
            className="p-1.5 rounded-full bg-surface border border-border text-content-secondary hover:text-content hover:bg-surface-secondary transition-all"
          >
            <ChevronUp className="w-4 h-4 -rotate-90" />
          </button>
          <div className="flex items-center gap-1.5">
            {signals.map((_, i) => (
              <div 
                key={i} 
                className={cn(
                  "w-1.5 h-1.5 rounded-full transition-all duration-300",
                  i === currentIndex ? "bg-brand-500 w-4" : "bg-border"
                )}
              />
            ))}
          </div>
          <button 
            onClick={handleNext}
            className="p-1.5 rounded-full bg-surface border border-border text-content-secondary hover:text-content hover:bg-surface-secondary transition-all"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

function SparklesIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>
    </svg>
  );
}
