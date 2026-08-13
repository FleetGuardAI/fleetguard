import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, RefreshCw } from 'lucide-react';
import { SignalPanel } from './SignalPanel';
import { useLanguage } from '@/i18n/LanguageContext';

/**
 * Premium Opportunity Feed wrapper — dark command-center aesthetic.
 * Contains Signal Panels with subtle green atmospheric lighting.
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
    <div className="relative rounded-2xl overflow-hidden">
      
      {/* Premium ambient radial background lights */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-fg-green/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-fg-green-muted/5 blur-[100px] pointer-events-none" />
      
      {/* Subtle telemetry grid texture */}
      <div 
        className="absolute inset-0 opacity-[0.015] pointer-events-none" 
        style={{
          backgroundImage: `radial-gradient(circle, rgba(25,184,106,0.4) 1px, transparent 1.5px)`,
          backgroundSize: '24px 24px',
        }}
      />

      <div className="relative space-y-6">
        {/* Header Block */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-xs font-semibold text-fg-text-sec uppercase tracking-widest flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-fg-green" />
              {t("Operations Engine")}
            </h2>
            <p className="text-[11px] text-fg-text-sec/60">
              {t("Real-time predictive telemetry feed")}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-fg-text-sec bg-white/[0.03] border border-fg-border px-2.5 py-1 rounded-lg">
              {opportunities.length} {t("Active Signals")}
            </span>
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="p-1.5 rounded-lg border border-fg-border hover:bg-white/[0.05] text-fg-text-sec transition-colors"
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
            {Array.from({ length: 2 }).map((_, i) => (
              <div 
                key={i} 
                className="w-full h-44 bg-white/[0.02] border border-fg-border rounded-2xl animate-pulse" 
              />
            ))}
          </div>
        ) : opportunities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center rounded-2xl border border-dashed border-fg-border p-6 bg-white/[0.01]">
            <Sparkles className="w-8 h-8 text-fg-text-sec/50 mb-3" />
            <h3 className="text-sm font-semibold text-fg-text mb-1">{t("Signals Cleared")}</h3>
            <p className="text-xs text-fg-text-sec">{t("Your fleet telemetry is currently fully optimized.")}</p>
          </div>
        ) : (
          <div className="space-y-5">
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
