import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronUp,
  ChevronRight,
  XCircle,
  Truck,
  User,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import { ConfidenceRing } from './ConfidenceRing';
import { SavingsIndicator } from './SavingsIndicator';
import { SignalTimeline } from './SignalTimeline';
import { SEVERITY_CONFIG } from '@/data/aiOpportunityData';

function getBusinessImpact(category) {
  switch (category) {
    case 'fuel_waste':
    case 'idle_time':
    case 'duplicate_fuel':
      return 'Financial Risk';
    case 'route_optimization':
      return 'Operational Optimization';
    case 'high_maintenance':
    case 'unexpected_expense':
      return 'Asset Depreciation Risk';
    case 'insurance_renewal':
    case 'permit_expiry':
      return 'Regulatory & Liability Threat';
    default:
      return 'General Fleet Compliance';
  }
}

function getConversationalNarrative(o) {
  const savingFormatted = `₹${(o.potentialSaving || 0).toLocaleString('en-IN')}`;

  switch (o.category) {
    case 'fuel_waste':
      return `Fuel efficiency dropped significantly on truck ${o.truck?.plate || ''}. Average fuel economy fell from 4.8 km/L to 3.9 km/L over the last 26 days. This drop is costing you roughly ${savingFormatted} per month.`;
    case 'unused_truck':
      return `Truck ${o.truck?.plate || ''} has been sitting idle at the yard for 6 consecutive days. Leaving this vehicle unassigned is causing fixed depreciation and insurance leakage of about ${savingFormatted} this month.`;
    case 'driver_behaviour':
      return `We detected 3 harsh braking events today from driver ${o.driver?.name || ''} while operating ${o.truck?.plate || ''} on NH-48. This aggressive driving style is accelerating brake pad wear and increasing risk.`;
    default:
      return `${o.title}. We recommend executing the suggested operational adjustments immediately to prevent further waste.`;
  }
}

export function SignalPanel({ opportunity, onAssign, onSchedule, onDismiss, onInvestigate, index = 0 }) {
  const { t } = useLanguage();
  const [expanded, setExpanded] = useState(false);

  if (!opportunity) return null;

  const o = opportunity;
  const sev = (o.severity && SEVERITY_CONFIG[o.severity]) ? SEVERITY_CONFIG[o.severity] : SEVERITY_CONFIG.low;
  const evidence = o.evidence || [];

  const activeBorder = o.severity === 'critical'
    ? 'border-red-500/20'
    : o.severity === 'high'
      ? 'border-orange-500/20'
      : 'border-fg-border';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ type: 'spring', stiffness: 100, damping: 20, delay: index * 0.08 }}
      className="w-full"
    >
      <div
        className={cn(
          'relative fg-card-static p-6 md:p-7',
          'hover:bg-fg-card-hover hover:border-fg-green/10 hover:shadow-fg-card',
          'transition-all duration-400 select-none overflow-hidden',
          activeBorder
        )}
      >
        {/* Layout */}
        <div className="space-y-5">
          
          {/* Top row: Label, Time, Severity */}
          <div className="flex items-center gap-3 text-[11px] text-fg-text-sec">
            <span className="font-semibold text-fg-green tracking-wider uppercase">
              {t("Predictive Signal")}
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span className={cn('font-semibold uppercase tracking-wider', 
              o.severity === 'critical' ? 'text-red-400' : 
              o.severity === 'high' ? 'text-orange-400' : 
              o.severity === 'medium' ? 'text-amber-400' : 'text-fg-green'
            )}>
              {t(o.severity || 'medium')} {t("Priority")}
            </span>
            <span className="flex items-center gap-1 ml-auto">
              <Clock className="w-3.5 h-3.5" />
              {o.createdAt ? new Date(o.createdAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''}
            </span>
          </div>

          {/* Title */}
          <h3 className="text-lg md:text-xl font-light text-fg-text tracking-tight leading-snug">
            {o.title}
          </h3>

          {/* Conversational Text */}
          <p className="text-sm text-fg-text-sec leading-relaxed font-light">
            {getConversationalNarrative(o)}
          </p>

          {/* Savings & Impact summary rail */}
          <div className="flex items-center gap-8 flex-wrap pt-1">
            <div>
              <span className="text-[10px] text-fg-text-sec/70 uppercase tracking-widest block mb-1">{t("Monthly Savings")}</span>
              <SavingsIndicator value={o.potentialSaving} />
            </div>
            
            <div>
              <span className="text-[10px] text-fg-text-sec/70 uppercase tracking-widest block mb-1">{t("Confidence")}</span>
              <ConfidenceRing percentage={o.confidence} size={42} strokeWidth={2.5} />
            </div>

            <div>
              <span className="text-[10px] text-fg-text-sec/70 uppercase tracking-widest block mb-1">{t("Business Impact")}</span>
              <span className="text-xs font-semibold text-fg-text block pt-1 bg-white/[0.03] px-2.5 py-1 rounded-lg border border-fg-border">
                {t(getBusinessImpact(o.category))}
              </span>
            </div>
          </div>

          {/* Expanded detail panel */}
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ type: 'spring', stiffness: 180, damping: 20 }}
                className="overflow-hidden space-y-6 pt-5 mt-3 border-t border-fg-border"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Why this matters & Root cause */}
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-[10px] font-semibold text-fg-text-sec/70 uppercase tracking-widest mb-1.5">
                        {t("Why this matters")}
                      </h4>
                      <p className="text-xs text-fg-text-sec leading-relaxed">
                        {t(o.rootCause || 'Unresolved telemetry variance leading to operational friction and capital burn.')}
                      </p>
                    </div>
                    <div>
                      <h4 className="text-[10px] font-semibold text-fg-text-sec/70 uppercase tracking-widest mb-1.5">
                        {t("Suggested Action Plan")}
                      </h4>
                      <div className="p-3 bg-white/[0.02] border border-fg-border rounded-xl text-xs text-fg-text-sec leading-relaxed">
                        {t(o.recommendation)}
                      </div>
                    </div>
                  </div>

                  {/* Detected changes & Timeline */}
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-[10px] font-semibold text-fg-text-sec/70 uppercase tracking-widest mb-2">
                        {t("Detected Changes")}
                      </h4>
                      <ul className="space-y-1.5">
                        {evidence.map((ev, idx) => (
                          <li key={idx} className="text-xs text-fg-text-sec flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-fg-green mt-1.5 flex-shrink-0" />
                            <span>{t(ev)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div>
                      <h4 className="text-[10px] font-semibold text-fg-text-sec/70 uppercase tracking-widest mb-2">
                        {t("Signal History")}
                      </h4>
                      <SignalTimeline events={[
                        { id: 1, message: t('Signal generated by anomalies monitor'), timestamp: o.createdAt, user: t('Diagnostics Engine') }
                      ]} />
                    </div>
                  </div>
                </div>

                {/* Operational Tags */}
                <div className="flex gap-2 flex-wrap">
                  {o.truck && (
                    <span className="text-[10px] text-fg-text-sec bg-white/[0.03] border border-fg-border px-2.5 py-1 rounded-lg flex items-center gap-1">
                      <Truck className="w-3.5 h-3.5 text-fg-text-sec/60" />
                      {t("Vehicle:")} <strong className="text-fg-text font-semibold">{o.truck.plate}</strong>
                    </span>
                  )}
                  {o.driver && (
                    <span className="text-[10px] text-fg-text-sec bg-white/[0.03] border border-fg-border px-2.5 py-1 rounded-lg flex items-center gap-1">
                      <User className="w-3.5 h-3.5 text-fg-text-sec/60" />
                      {t("Driver:")} <strong className="text-fg-text font-semibold">{o.driver.name}</strong>
                    </span>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Bottom Row Actions */}
          <div className="pt-4 border-t border-fg-border flex items-center justify-between flex-wrap gap-4">
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs font-medium text-fg-text-sec hover:text-fg-text transition-colors flex items-center gap-1.5"
            >
              {expanded ? (
                <>{t("Hide detailed diagnosis")} <ChevronUp className="w-3.5 h-3.5" /></>
              ) : (
                <>{t("View telemetry log & root cause")} <ArrowRight className="w-3.5 h-3.5" /></>
              )}
            </button>

            <div className="flex items-center gap-3 flex-shrink-0">
              <motion.button
                whileTap={{ scale: 0.96 }}
                onClick={() => onDismiss?.(o.id)}
                className="p-2 rounded-xl text-fg-text-sec hover:text-red-400 hover:bg-red-500/10 transition-colors flex-shrink-0"
                title={t("Archive Signal")}
              >
                <XCircle className="w-4 h-4" />
              </motion.button>

              <motion.button
                whileTap={{ scale: 0.96 }}
                onClick={() => onAssign?.(o.id)}
                className="bg-brand-500 text-white font-semibold text-xs px-5 py-2.5 rounded-xl transition-all duration-200 hover:bg-brand-600 shadow-green flex items-center gap-1.5 cursor-pointer flex-shrink-0 active:scale-[0.98]"
              >
                <span>{t("Resolve Signal")}</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </motion.button>
            </div>
          </div>

        </div>
      </div>
    </motion.div>
  );
}
