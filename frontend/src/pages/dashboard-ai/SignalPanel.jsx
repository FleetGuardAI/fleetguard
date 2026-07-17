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
  Sparkles,
  Zap,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import { ConfidenceRing } from './ConfidenceRing';
import { SavingsIndicator } from './SavingsIndicator';
import { TruckPreview } from './TruckPreview';
import { SignalTimeline } from './SignalTimeline';
import { SEVERITY_CONFIG } from '@/data/aiOpportunityData';

function getBusinessImpact(category) {
  switch (category) {
    case 'fuel_waste':
    case 'idle_time':
    case 'duplicate_fuel':
      return 'Immediate Cash Leakage';
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
  const truckPlate = o.truck ? `**${o.truck.plate}**` : '';
  const driverName = o.driver ? `**${o.driver.name}**` : '';
  const savingFormatted = `**₹${o.potentialSaving.toLocaleString('en-IN')}**`;

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
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [lightX, setLightX] = useState(0);
  const [lightY, setLightY] = useState(0);
  const [hovering, setHovering] = useState(false);

  if (!opportunity) return null;

  const o = opportunity;
  const sev = (o.severity && SEVERITY_CONFIG[o.severity]) ? SEVERITY_CONFIG[o.severity] : SEVERITY_CONFIG.low;
  const evidence = o.evidence || [];

  const handleMouseMove = (e) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const normalizedX = (x / rect.width) - 0.5;
    const normalizedY = (y / rect.height) - 0.5;

    // Subtle 3D tilt (Professional range: max 5 deg rotation)
    setRotateX(-normalizedY * 8);
    setRotateY(normalizedX * 8);

    // Light source tracking
    setLightX(x);
    setLightY(y);
  };

  const handleMouseLeave = () => {
    setHovering(false);
    setRotateX(0);
    setRotateY(0);
  };

  const activeBorder = o.severity === 'critical'
    ? 'border-red-500/30 shadow-red-500/5'
    : o.severity === 'high'
      ? 'border-orange-500/30 shadow-orange-500/5'
      : 'border-white/10 shadow-black/20';

  return (
    <motion.div
      initial={{ opacity: 0, y: 35, scale: 0.94 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ type: 'spring', stiffness: 100, damping: 20, delay: index * 0.08 }}
      className="w-full"
    >
      <div
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={handleMouseLeave}
        style={{
          transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
          transition: hovering ? 'none' : 'transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), shadow 0.6s ease',
        }}
        className={cn(
          'relative bg-white/[0.03] dark:bg-slate-900/[0.4] backdrop-blur-xl border rounded-[30px] p-6 md:p-8',
          'shadow-[0_15px_35px_rgba(0,0,0,0.05),0_5px_15px_rgba(0,0,0,0.02)]',
          'hover:bg-white/[0.05] dark:hover:bg-slate-900/[0.5] hover:shadow-[0_25px_50px_rgba(0,0,0,0.12),0_10px_20px_rgba(0,0,0,0.05)]',
          'transition-all duration-500 ease-out select-none overflow-hidden',
          activeBorder
        )}
      >
        {/* Dynamic Light Overlay (Reflective Glow) */}
        {hovering && (
          <div
            className="absolute inset-0 pointer-events-none rounded-[30px]"
            style={{
              background: `radial-gradient(220px circle at ${lightX}px ${lightY}px, rgba(255, 255, 255, 0.05), transparent 80%)`,
            }}
          />
        )}

        {/* Layout Row */}
        <div className="flex flex-col md:flex-row items-start gap-6 md:gap-8">
          
          {/* Left Block: Interactive Truck illustration */}
          <div className="flex-shrink-0">
            <TruckPreview category={o.category} />
          </div>

          {/* Central Block: Core narrative content */}
          <div className="flex-grow min-w-0 space-y-4">
            
            {/* Top row: Label, Time, Severity */}
            <div className="flex items-center gap-3 text-[11px] text-content-muted">
              <span className="font-semibold text-brand-600 dark:text-brand-400 tracking-wider uppercase">
                {t("Predictive Signal")}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {o.createdAt ? new Date(o.createdAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''}
              </span>
              <span>•</span>
              <span className={cn('font-semibold uppercase tracking-wider', sev.text)}>
                {t(o.severity)} {t("Priority")}
              </span>
            </div>

            {/* Title */}
            <h3 className="text-lg md:text-xl font-light text-content tracking-tight leading-snug">
              {o.title}
            </h3>

            {/* Conversational Text */}
            <p className="text-sm md:text-base text-content-secondary leading-relaxed font-light">
              {getConversationalNarrative(o)}
            </p>

            {/* Savings & Impact summary rail */}
            <div className="flex items-center gap-8 flex-wrap pt-2">
              <div>
                <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-0.5">{t("Monthly Savings")}</span>
                <SavingsIndicator value={o.potentialSaving} />
              </div>
              
              <div>
                <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Confidence")}</span>
                <ConfidenceRing percentage={o.confidence} size={42} strokeWidth={2.5} />
              </div>

              <div>
                <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Business Impact")}</span>
                <span className="text-xs font-semibold text-content block pt-1 bg-surface-secondary/40 px-2 py-0.5 rounded-lg border border-border/20">
                  {t(getBusinessImpact(o.category))}
                </span>
              </div>
            </div>

            {/* Advanced detailed panel toggled with spring animations */}
            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ type: 'spring', stiffness: 180, damping: 20 }}
                  className="overflow-hidden space-y-6 pt-5 mt-5 border-t border-border/30"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Why this matters & Root cause */}
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-[10px] font-semibold text-content-muted uppercase tracking-widest mb-1.5">
                          {t("Why this matters")}
                        </h4>
                        <p className="text-xs text-content-secondary leading-relaxed">
                          {t(o.rootCause || 'Unresolved telemetry variance leading to operational friction and capital burn.')}
                        </p>
                      </div>
                      <div>
                        <h4 className="text-[10px] font-semibold text-content-muted uppercase tracking-widest mb-1.5">
                          {t("Suggested Action Plan")}
                        </h4>
                        <div className="p-3 bg-white/[0.02] border border-white/5 rounded-xl text-xs text-content-secondary leading-relaxed">
                          {t(o.recommendation)}
                        </div>
                      </div>
                    </div>

                    {/* Detected changes & Timeline */}
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-[10px] font-semibold text-content-muted uppercase tracking-widest mb-2">
                          {t("Detected Changes")}
                        </h4>
                        <ul className="space-y-1.5">
                          {evidence.map((ev, idx) => (
                            <li key={idx} className="text-xs text-content-secondary flex items-start gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 mt-1.5 flex-shrink-0" />
                              <span>{t(ev)}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h4 className="text-[10px] font-semibold text-content-muted uppercase tracking-widest mb-2">
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
                      <span className="text-[10px] text-content-secondary bg-surface-secondary border border-border/50 px-2.5 py-1 rounded-lg flex items-center gap-1">
                        <Truck className="w-3.5 h-3.5 text-content-muted" />
                        {t("Vehicle:")} <strong className="text-content font-semibold">{o.truck.plate}</strong>
                      </span>
                    )}
                    {o.driver && (
                      <span className="text-[10px] text-content-secondary bg-surface-secondary border border-border/50 px-2.5 py-1 rounded-lg flex items-center gap-1">
                        <User className="w-3.5 h-3.5 text-content-muted" />
                        {t("Driver:")} <strong className="text-content font-semibold">{o.driver.name}</strong>
                      </span>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Bottom Row Actions */}
            <div className="pt-4 border-t border-border/10 flex items-center justify-between flex-wrap gap-4">
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs font-semibold text-content-muted hover:text-content transition-colors flex items-center gap-1"
              >
                {expanded ? (
                  <>{t("Hide detailed diagnosis")} <ChevronUp className="w-3.5 h-3.5" /></>
                ) : (
                  <>{t("View telemetry log & root cause")} <ChevronDown className="w-3.5 h-3.5" /></>
                )}
              </button>

              <div className="flex items-center gap-4 flex-shrink-0">
                <motion.button
                  whileTap={{ scale: 0.96 }}
                  onClick={() => onDismiss?.(o.id)}
                  className="p-2 rounded-xl text-content-muted hover:text-red-500 hover:bg-red-500/10 transition-colors flex-shrink-0"
                  title={t("Archive Signal")}
                >
                  <XCircle className="w-4 h-4" />
                </motion.button>

                <motion.button
                  whileTap={{ scale: 0.96 }}
                  onClick={() => onAssign?.(o.id)}
                  className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-semibold text-xs px-5 py-2 rounded-xl transition-all duration-200 hover:shadow-lg flex items-center gap-1.5 cursor-pointer flex-shrink-0 active:scale-[0.98]"
                >
                  <span>{t("Resolve Signal")}</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </motion.button>
              </div>
            </div>

          </div>

        </div>
      </div>
    </motion.div>
  );
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);

  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}
