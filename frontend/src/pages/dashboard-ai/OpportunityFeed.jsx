import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, RefreshCw } from 'lucide-react';
import { SignalPanel } from './SignalPanel';
import { useLanguage } from '@/i18n/LanguageContext';

/**
 * Premium Opportunity Feed wrapper containing Signal Panels.
 * Implements very soft layered radial lighting backgrounds, ambient textures,
 * and elegant viewport entry animations.
 */
export function OpportunityFeed({
  opportunities = [],
  loading = false,
  refreshing = false,
  onRefresh,
  onAssign,
  onSchedule,
  onDismiss,
  onInvestigate,
}) {
  const { t } = useLanguage();
  return (
    <div className="relative rounded-[32px] p-1 border border-white/5 overflow-hidden">
      
      {/* Premium ambient radial background lights */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-brand-500/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/5 blur-[100px] pointer-events-none" />
      
      {/* Subtle organic dotted grid texture */}
      <div 
        className="absolute inset-0 opacity-[0.015] pointer-events-none" 
        style={{
          backgroundImage: `radial-gradient(circle, #fff 1px, transparent 1.5px)`,
          backgroundSize: '24px 24px',
        }}
      />

      <div className="relative p-6 md:p-8 space-y-8">
        {/* Header Block */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-xs font-semibold text-content-muted uppercase tracking-widest flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-brand-500" />
              {t("Operations Engine")}
            </h2>
            <p className="text-[11px] text-content-muted">
              {t("Real-time predictive telemetry feed")}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-content-muted bg-white/[0.02] border border-white/5 px-2.5 py-1 rounded-lg">
              {opportunities.length} {t("Active Signals")}
            </span>
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="p-1.5 rounded-lg border border-border/40 hover:bg-surface-secondary text-content-secondary transition-colors"
                title={t("Fetch Signals")}
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
        </div>

        {/* Signals feed list */}
        {loading ? (
          <div className="space-y-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div 
                key={i} 
                className="w-full h-44 bg-white/[0.01] border border-white/5 rounded-[30px] animate-pulse" 
              />
            ))}
          </div>
        ) : opportunities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center rounded-[30px] border border-dashed border-border/40 p-6 bg-white/[0.01]">
            <Sparkles className="w-8 h-8 text-content-muted mb-3" />
            <h3 className="text-sm font-semibold text-content mb-1">{t("Signals Cleared")}</h3>
            <p className="text-xs text-content-muted">{t("Your fleet telemetry is currently fully optimized.")}</p>
          </div>
        ) : (
          <div className="space-y-6">
            {opportunities.map((opp, idx) => (
              <SignalPanel
                key={opp.id}
                opportunity={opp}
                index={idx}
                onAssign={onAssign}
                onSchedule={onSchedule}
                onDismiss={onDismiss}
                onInvestigate={onInvestigate}
              />
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
export default OpportunityFeed;
