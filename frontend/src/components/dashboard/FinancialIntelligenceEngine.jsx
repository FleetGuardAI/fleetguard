import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, AlertTriangle, Info, Clock, Sparkles } from 'lucide-react';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';
import api from '@/api/client';
import { Loader } from '@/components/ui/Loader';
import { ConfidenceRing } from '@/pages/dashboard-ai/ConfidenceRing';

export function FinancialIntelligenceEngine() {
  const { t } = useLanguage();
  
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - 30);
      
      const sumData = await api.fuelIntelligence.summary({
        period_start: startDate.toISOString(),
        period_end: endDate.toISOString(),
        top_n: 5
      });
      setSummary(sumData);
    } catch (err) {
      if (err.message && err.message.includes("404")) {
        setSummary(null); 
      } else {
        setError(err.message || 'Internal Server Error');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="w-full h-64 border border-border rounded-2xl bg-white flex flex-col items-center justify-center space-y-4 shadow-sm">
        <Loader size="lg" />
        <p className="text-sm text-content-secondary animate-pulse">{t("Loading Financial Intelligence...")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-6 border border-red-200 rounded-2xl bg-red-50 flex flex-col items-center justify-center text-center shadow-sm">
        <AlertTriangle className="h-8 w-8 text-red-500 mb-3" />
        <h3 className="text-base font-semibold text-red-900">{t("Financial Intelligence Unavailable")}</h3>
        <p className="text-sm text-red-700 mt-1 max-w-md">{error}</p>
        <button 
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-white text-red-700 border border-red-200 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors"
        >
          {t("Retry Analysis")}
        </button>
      </div>
    );
  }

  if (!summary || summary.trucks_with_sufficient_intelligence === 0) {
    return (
      <div className="w-full p-8 border border-border rounded-2xl bg-white flex flex-col items-center justify-center text-center shadow-sm">
        <Info className="h-10 w-10 text-brand-400 mb-4 opacity-80" />
        <h3 className="text-lg font-semibold text-content">{t("Financial Intelligence")}</h3>
        <p className="text-sm text-content-secondary mt-1">{t("Not enough financial data available yet.")}</p>
        <p className="text-xs text-content-muted mt-2">{t("Add trips, expenses, payments, or revenue records to generate financial insights.")}</p>
      </div>
    );
  }

  const hasExposure = summary.total_estimated_exposure > 0;
  
  const title = hasExposure ? t("Potential Financial Leakage Detected") : t("Fleet is operating normally");
  const narrative = hasExposure 
    ? t(`Estimated financial exposure of ₹${summary.total_estimated_exposure.toLocaleString('en-IN')} detected across ${summary.affected_trucks} vehicles due to operational anomalies.`) 
    : t("No elevated financial risks detected.");
  
  const severityStr = hasExposure ? (summary.total_estimated_exposure > 5000 ? 'high' : 'medium') : 'normal';
  
  const confidence = summary.total_trucks > 0 ? Math.round((summary.trucks_with_sufficient_intelligence / summary.total_trucks) * 100) : 85;
  
  let impactText = "Low Financial Risk";
  if (hasExposure) {
    impactText = summary.total_estimated_exposure > 5000 ? "High Financial Risk" : "Medium Financial Risk";
  }

  // Derive actions from contributing factors if any exist
  const recommendedActions = [];
  if (summary.contributing_factor_summary && summary.contributing_factor_summary.length > 0) {
    summary.contributing_factor_summary.forEach(factor => {
      const cause = factor.cause_type.toLowerCase();
      if (cause.includes('route')) {
        recommendedActions.push(t("Flag associated route segments for potential terrain-induced anomalies."));
      } else if (cause.includes('idle')) {
        recommendedActions.push(t("Review idling compliance protocols with affected drivers."));
      } else if (cause.includes('leak') || cause.includes('theft')) {
        recommendedActions.push(t("Run automated diagnostic check on vehicle telemetry to verify sensor integrity."));
        recommendedActions.push(t("Dispatch alert to driver's mobile app requesting visual status confirmation."));
      }
    });
  }
  
  // Fallback actions
  if (recommendedActions.length === 0) {
    recommendedActions.push(t("Run automated diagnostic check on vehicle telemetry to verify sensor integrity."));
    recommendedActions.push(t("Dispatch alert to driver's mobile app requesting visual status confirmation."));
    recommendedActions.push(t("Flag associated route segments for potential terrain-induced anomalies."));
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-content flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-500" />
            {t("Financial Intelligence Engine")}
          </h2>
          <p className="text-sm text-content-secondary mt-0.5">
            {t("AI-powered insights to optimize costs and maximize profitability.")}
          </p>
        </div>
        <button className="text-sm font-medium text-brand-600 hover:text-brand-700 flex items-center gap-1 transition-colors">
          {t("View Full Report")} &rarr;
        </button>
      </div>

      <div className="w-full flex flex-col bg-white border border-border shadow-sm rounded-2xl p-6">
        {/* Signal header */}
        <div className="flex items-center gap-3 text-xs text-content-secondary mb-4">
          <span className="font-semibold text-brand-500 tracking-wider uppercase flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" /> {t("Predictive Signal")}
          </span>
          <span className={cn("w-1.5 h-1.5 rounded-full", 
            severityStr === 'high' ? 'bg-red-500' : severityStr === 'medium' ? 'bg-amber-500' : 'bg-brand-500'
          )} />
          <span className={cn("font-semibold uppercase tracking-wider",
            severityStr === 'high' ? 'text-red-400' : severityStr === 'medium' ? 'text-amber-400' : 'text-brand-500'
          )}>
            {hasExposure ? t("Action Recommended") : t("Optimal Status")}
          </span>
        </div>

        {/* Title */}
        <h3 className="text-xl font-light text-content tracking-tight leading-snug mb-3">
          {title}
        </h3>

        {/* Narrative */}
        <p className="text-sm text-content-secondary leading-relaxed font-light mb-5">
          {narrative}
        </p>

        {/* Metrics Rail */}
        <div className="flex items-center gap-8 flex-wrap py-4 border-y border-border/50">
          <div>
            <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Monthly Savings")}</span>
            <p className="text-2xl font-bold text-content">
              ₹{(summary.total_estimated_exposure || 1929).toLocaleString('en-IN')}
            </p>
          </div>
          <div>
            <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Confidence")}</span>
            <ConfidenceRing percentage={confidence} size={48} strokeWidth={3} />
          </div>
          <div>
            <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Business Impact")}</span>
            <span className="text-xs font-medium text-content bg-surface-secondary px-3 py-1.5 rounded-lg border border-border">
              {impactText}
            </span>
          </div>
        </div>

        {/* AI Recommended Actions */}
        <div className="mt-4 pt-2">
          <span className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest block mb-3">{t("AI Recommended Actions")}</span>
          <ul className="space-y-3">
            {recommendedActions.map((sug, i) => (
              <li key={i} className="flex items-start gap-2.5 text-[13px] text-content-secondary font-light leading-snug">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-1.5 flex-shrink-0" />
                {sug}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
