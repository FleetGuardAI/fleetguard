import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Fuel, AlertTriangle, ShieldAlert, BarChart3, TrendingDown, Info, Calendar } from 'lucide-react';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';
import api from '@/api/client';
import { Loader } from '@/components/ui/Loader';

const SEVERITY_COLORS = {
  CRITICAL: 'text-red-500',
  WARNING: 'text-amber-500',
  NORMAL: 'text-emerald-500'
};

const SEVERITY_BG = {
  CRITICAL: 'bg-red-50 border-red-100',
  WARNING: 'bg-amber-50 border-amber-100',
  NORMAL: 'bg-emerald-50 border-emerald-100'
};

const SEVERITY_ICONS = {
  CRITICAL: ShieldAlert,
  WARNING: AlertTriangle,
  NORMAL: Info
};

export function FinancialIntelligenceWidget() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  
  const [period, setPeriod] = useState(30); // 7 or 30
  const [summary, setSummary] = useState(null);
  const [vehiclesMap, setVehiclesMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - period);
        
        const [sumData, trucksData] = await Promise.all([
          api.fuelIntelligence.summary({
            period_start: startDate.toISOString(),
            period_end: endDate.toISOString(),
            top_n: 5
          }),
          api.trucks.list().catch(() => []) // Gracefully degrade if trucks list fails
        ]);
        
        if (!isMounted) return;
        
        setSummary(sumData);
        
        // Map license plate to vehicle ID for navigation
        const vMap = {};
        if (Array.isArray(trucksData)) {
          trucksData.forEach(v => {
            if (v.license_plate) vMap[v.license_plate] = v.id;
          });
        }
        setVehiclesMap(vMap);
      } catch (err) {
        if (!isMounted) return;
        if (err.message && err.message.includes("404")) {
           // Treat 404 as "no intelligence found" or empty state, rather than a crash
           setSummary(null); 
        } else {
           setError(err.message || 'Failed to load financial intelligence.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    
    loadData();
    return () => { isMounted = false; };
  }, [period]);

  if (loading) {
    return (
      <div className="w-full h-64 border border-border rounded-2xl bg-white flex flex-col items-center justify-center space-y-4">
        <Loader size="lg" />
        <p className="text-sm text-content-secondary animate-pulse">{t("Analyzing fleet financial exposure...")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-6 border border-red-200 rounded-2xl bg-red-50 flex flex-col items-center justify-center text-center">
        <AlertTriangle className="h-8 w-8 text-red-500 mb-3" />
        <h3 className="text-base font-semibold text-red-900">{t("Financial Intelligence Unavailable")}</h3>
        <p className="text-sm text-red-700 mt-1 max-w-md">{error}</p>
        <button 
          onClick={() => setPeriod(period)}
          className="mt-4 px-4 py-2 bg-white text-red-700 border border-red-200 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors"
        >
          {t("Retry Analysis")}
        </button>
      </div>
    );
  }

  // --- Empty / Healthy / Insufficient States ---
  if (!summary) {
    return (
      <div className="w-full p-8 border border-border rounded-2xl bg-white flex flex-col items-center justify-center text-center">
        <ShieldAlert className="h-10 w-10 text-content-muted mb-4 opacity-50" />
        <h3 className="text-lg font-semibold text-content">{t("Intelligence Engine Idle")}</h3>
        <p className="text-sm text-content-secondary mt-1">{t("No financial exposure analysis returned from the engine.")}</p>
      </div>
    );
  }

  const isHealthy = summary.affected_trucks === 0 && summary.trucks_with_sufficient_intelligence > 0;
  const isInsufficient = summary.trucks_with_sufficient_intelligence === 0;

  return (
    <div className="w-full bg-white border border-border rounded-2xl shadow-sm overflow-hidden mb-8">
      {/* HEADER & CONTROLS */}
      <div className="p-5 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-base/30">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-brand-100 text-brand-600 rounded-xl">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-content tracking-tight">{t("Fleet Financial Intelligence")}</h2>
            <p className="text-xs text-content-secondary mt-0.5">{t("Estimated impact derived from performance anomalies")}</p>
          </div>
        </div>
        
        {/* Localized Period Selector */}
        <div className="flex items-center bg-surface-secondary border border-border rounded-lg p-1">
          <button 
            onClick={() => setPeriod(7)}
            className={cn("px-3 py-1.5 text-xs font-medium rounded-md transition-colors", period === 7 ? "bg-white text-brand-600 shadow-sm" : "text-content-secondary hover:text-content")}
          >
            {t("Last 7 Days")}
          </button>
          <button 
            onClick={() => setPeriod(30)}
            className={cn("px-3 py-1.5 text-xs font-medium rounded-md transition-colors", period === 30 ? "bg-white text-brand-600 shadow-sm" : "text-content-secondary hover:text-content")}
          >
            {t("Last 30 Days")}
          </button>
        </div>
      </div>

      <div className="p-5">
        {isInsufficient ? (
          <div className="py-10 text-center bg-surface-tertiary rounded-xl border border-dashed border-border">
            <Info className="w-8 h-8 text-amber-500 mx-auto mb-3" />
            <h3 className="text-base font-medium text-content">{t("Insufficient Data")}</h3>
            <p className="text-sm text-content-secondary mt-1">{t("Some trucks do not have enough validated fuel data to establish financial impact.")}</p>
          </div>
        ) : isHealthy ? (
          <div className="py-10 text-center bg-emerald-50 rounded-xl border border-emerald-100">
            <ShieldAlert className="w-8 h-8 text-emerald-500 mx-auto mb-3" />
            <h3 className="text-base font-medium text-emerald-900">{t("Fleet Optimal")}</h3>
            <p className="text-sm text-emerald-700 mt-1">{t("No financial exposure established for this period.")}</p>
          </div>
        ) : (
          <div className="space-y-6">
            
            {/* 1. KPI ROW */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 bg-red-50 border border-red-100 rounded-xl relative overflow-hidden">
                <div className="absolute -right-4 -top-4 opacity-5">
                  <TrendingDown className="w-24 h-24 text-red-900" />
                </div>
                <p className="text-xs font-semibold text-red-800 uppercase tracking-widest">{t("Estimated Exposure")}</p>
                <p className="text-2xl font-bold text-red-600 mt-1">₹{summary.total_estimated_exposure.toLocaleString('en-IN')}</p>
              </div>
              
              <div className="p-4 bg-surface-secondary border border-border rounded-xl">
                <p className="text-xs font-semibold text-content-secondary uppercase tracking-widest">{t("Affected Trucks")}</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <p className="text-2xl font-bold text-content">{summary.affected_trucks}</p>
                  <span className="text-sm text-content-muted">/ {summary.total_trucks}</span>
                </div>
              </div>
              
              <div className="p-4 bg-surface-secondary border border-border rounded-xl">
                <p className="text-xs font-semibold text-content-secondary uppercase tracking-widest">{t("Excess Fuel")}</p>
                <p className="text-2xl font-bold text-content mt-1">{Math.round(summary.total_excess_fuel_liters).toLocaleString('en-IN')} L</p>
              </div>
              
              <div className="p-4 bg-surface-secondary border border-border rounded-xl flex flex-col justify-center">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-semibold text-content-secondary uppercase tracking-widest">{t("Intelligence Coverage")}</span>
                  <span className="text-xs font-medium text-brand-600">{Math.round((summary.trucks_with_sufficient_intelligence / Math.max(1, summary.total_trucks)) * 100)}%</span>
                </div>
                <div className="w-full bg-border h-1.5 rounded-full overflow-hidden">
                  <div className="bg-brand-500 h-full" style={{ width: `${(summary.trucks_with_sufficient_intelligence / Math.max(1, summary.total_trucks)) * 100}%`}} />
                </div>
                <p className="text-[10px] text-content-muted mt-2">{summary.trucks_with_sufficient_intelligence} trucks with sufficient data</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* 2. TOP EXPOSURES */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-content-secondary uppercase tracking-widest border-b border-border pb-2">{t("Top Financial Exposures")}</h3>
                <div className="space-y-2">
                  {summary.top_exposures.length === 0 ? (
                    <p className="text-sm text-content-muted italic py-4">{t("No exposure records available.")}</p>
                  ) : (
                    summary.top_exposures.map((truck, idx) => {
                      const Icon = SEVERITY_ICONS[truck.severity] || Info;
                      return (
                        <div 
                          key={truck.truck_id || idx}
                          onClick={() => {
                            const vid = vehiclesMap[truck.truck_id];
                            if (vid) navigate(`/dashboard/vehicles/${vid}`);
                          }}
                          className={cn(
                            "flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer group hover:shadow-md",
                            SEVERITY_BG[truck.severity] || "bg-surface-secondary border-border"
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex-shrink-0 p-1.5 bg-white/50 rounded-lg">
                              <Icon className={cn("w-4 h-4", SEVERITY_COLORS[truck.severity])} />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-sm text-content">{truck.truck_id}</span>
                                <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-white/60", SEVERITY_COLORS[truck.severity])}>
                                  {truck.severity}
                                </span>
                              </div>
                              <p className="text-xs text-content-secondary mt-0.5">
                                {truck.worst_deviation_percent < 0 ? truck.worst_deviation_percent.toFixed(1) : `+${truck.worst_deviation_percent.toFixed(1)}`}% vs baseline
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-sm font-bold text-content">₹{truck.estimated_exposure.toLocaleString('en-IN')}</p>
                              <p className="text-xs text-content-muted">{Math.round(truck.excess_fuel_liters)} L excess</p>
                            </div>
                            <ChevronRight className="w-4 h-4 text-content-muted group-hover:text-brand-500 transition-colors" />
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>

              {/* 3. CONTRIBUTING FACTORS */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-content-secondary uppercase tracking-widest border-b border-border pb-2">{t("Evidence Observed")}</h3>
                <div className="space-y-2">
                  {summary.contributing_factor_summary.length === 0 ? (
                    <p className="text-sm text-content-muted italic py-4">{t("No contributing factors logged.")}</p>
                  ) : (
                    summary.contributing_factor_summary.map((factor, idx) => (
                      <div key={idx} className="flex flex-col p-3 rounded-xl border border-border bg-surface hover:bg-surface-secondary transition-colors">
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-sm font-medium text-content capitalize">{factor.cause_type.replace(/_/g, ' ').toLowerCase()}</span>
                          <span className="text-sm font-semibold text-content">₹{factor.total_estimated_exposure.toLocaleString('en-IN')}</span>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-content-secondary">{factor.affected_truck_count} truck{factor.affected_truck_count !== 1 && 's'}</span>
                          <span className="text-content-muted">{factor.highest_observed_strength.replace(/_/g, ' ').toLowerCase()} evidence</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <div className="mt-4 p-3 bg-brand-50 border border-brand-100 rounded-xl flex gap-3 text-brand-800 text-xs items-start">
                  <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <p>{t("These are possible contributing factors based on system evidence, not confirmed causal conclusions.")}</p>
                </div>
              </div>

            </div>
          </div>
        )}
      </div>
    </div>
  );
}
