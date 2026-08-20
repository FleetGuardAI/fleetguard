import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, Info, Calendar, TrendingDown, Fuel, Receipt } from 'lucide-react';
import { useLanguage } from '@/i18n/LanguageContext';
import { cn } from '@/utils/cn';
import api from '@/api/client';
import { Loader } from '@/components/ui/Loader';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';

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

export function TruckFinancialIntelligence({ truckId, periodDays = 30 }) {
  const { t } = useLanguage();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    
    async function loadData() {
      if (!truckId) return;
      
      setLoading(true);
      setError(null);
      try {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - periodDays);
        
        const detail = await api.fuelIntelligence.truckDetail(truckId, {
          period_start: startDate.toISOString(),
          period_end: endDate.toISOString()
        });
        
        if (isMounted) setData(detail);
      } catch (err) {
        if (!isMounted) return;
        if (err.message && err.message.includes("404")) {
           setData(null); // Empty state 
        } else {
           setError(err.message || 'Failed to load truck intelligence.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    
    loadData();
    return () => { isMounted = false; };
  }, [truckId, periodDays]);

  if (loading) {
    return (
      <Card>
        <div className="flex flex-col items-center justify-center h-48 space-y-4">
          <Loader size="lg" />
          <p className="text-sm text-content-secondary animate-pulse">{t("Analyzing vehicle intelligence...")}</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="p-8 text-center bg-red-50 flex flex-col items-center justify-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mb-3" />
          <h3 className="text-base font-semibold text-red-900">{t("Analysis Unavailable")}</h3>
          <p className="text-sm text-red-700 mt-1">{error}</p>
        </div>
      </Card>
    );
  }

  if (!data || !data.summary || data.summary.estimated_exposure === 0) {
    return (
      <Card>
        <div className="p-10 text-center flex flex-col items-center justify-center">
          <div className="p-3 bg-emerald-50 rounded-full mb-4">
            <ShieldAlert className="h-8 w-8 text-emerald-500" />
          </div>
          <h3 className="text-base font-semibold text-content">{t("No Financial Exposure")}</h3>
          <p className="text-sm text-content-secondary mt-1 max-w-sm mx-auto">
            {t("No financial exposure established for this period. Vehicle operation is currently optimal or lacks sufficient anomaly evidence.")}
          </p>
        </div>
      </Card>
    );
  }

  const { summary, anomalies, financial_impacts, contributing_factors } = data;
  const TopIcon = SEVERITY_ICONS[summary.severity] || Info;

  return (
    <div className="space-y-6">
      {/* KPI Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Estimated Exposure */}
        <div className={cn("p-5 border rounded-xl flex flex-col justify-between relative overflow-hidden", SEVERITY_BG[summary.severity])}>
          <div className="absolute -right-4 -bottom-4 opacity-5 pointer-events-none">
            <TrendingDown className="w-32 h-32 text-content" />
          </div>
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <TopIcon className={cn("w-5 h-5", SEVERITY_COLORS[summary.severity])} />
              <h3 className="text-xs font-semibold uppercase tracking-widest text-content-secondary">{t("Estimated Exposure")}</h3>
            </div>
            <p className={cn("text-3xl font-bold tracking-tight mt-1", SEVERITY_COLORS[summary.severity])}>
              ₹{summary.estimated_exposure.toLocaleString('en-IN')}
            </p>
            <p className="text-sm text-content-secondary mt-1">
              {summary.excess_fuel_liters > 0 ? `${Math.round(summary.excess_fuel_liters)} L excess fuel` : 'Calculation pending'}
            </p>
          </div>
        </div>

        {/* Fuel Efficiency */}
        <div className="p-5 border border-border bg-white rounded-xl">
          <div className="flex items-center gap-2 mb-3">
            <Fuel className="w-5 h-5 text-brand-600" />
            <h3 className="text-xs font-semibold uppercase tracking-widest text-content-secondary">{t("Efficiency Deviation")}</h3>
          </div>
          
          <div className="flex items-end gap-3 mt-1">
            <p className="text-3xl font-bold text-content tracking-tight">
              {summary.worst_deviation_percent < 0 ? summary.worst_deviation_percent.toFixed(1) : `+${summary.worst_deviation_percent.toFixed(1)}`}%
            </p>
            <span className="text-sm text-content-muted mb-1">{t("vs Historical Baseline")}</span>
          </div>
          
          {anomalies && anomalies.length > 0 && (
            <div className="flex justify-between items-center mt-4 pt-4 border-t border-border">
              <div>
                <p className="text-xs text-content-muted">{t("Current")}</p>
                <p className="text-sm font-semibold text-content">{anomalies[0].observed_value.toFixed(2)} km/L</p>
              </div>
              <div>
                <p className="text-xs text-content-muted">{t("Baseline")}</p>
                <p className="text-sm font-semibold text-content">{anomalies[0].baseline_value.toFixed(2)} km/L</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Top Contributing Factor */}
        <div className="p-5 border border-border bg-white rounded-xl">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-brand-600" />
            <h3 className="text-xs font-semibold uppercase tracking-widest text-content-secondary">{t("Primary Signal")}</h3>
          </div>
          <p className="text-lg font-semibold text-content capitalize">
            {summary.top_contributing_factor ? summary.top_contributing_factor.replace(/_/g, ' ').toLowerCase() : t("Unknown")}
          </p>
          <div className="mt-2 inline-flex">
            <span className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider bg-surface-secondary text-content-secondary rounded">
              {summary.top_contributing_strength.replace(/_/g, ' ').toLowerCase()} Evidence
            </span>
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Possible Contributing Factors */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Info className="h-4 w-4 text-brand-600" />
              {t("Possible Contributing Factors")}
            </CardTitle>
          </CardHeader>
          <div className="p-5 pt-0 flex-1 flex flex-col">
            {!contributing_factors || contributing_factors.length === 0 ? (
              <div className="text-center py-6 text-content-muted text-sm my-auto">
                {t("No specific evidence observed for anomalies.")}
              </div>
            ) : (
              <div className="space-y-4">
                {contributing_factors.map((cf, i) => (
                  <div key={i} className="space-y-3">
                    {cf.possible_contributing_factors.map((ev, j) => (
                      <div key={j} className="p-3 bg-surface-secondary border border-border rounded-lg">
                        <div className="flex justify-between items-start mb-1">
                          <p className="text-sm font-semibold text-content capitalize">
                            {ev.cause_type.replace(/_/g, ' ').toLowerCase()}
                          </p>
                          <span className="text-[10px] uppercase font-bold text-content-secondary">
                            {ev.evidence_strength.replace(/_/g, ' ').toLowerCase()}
                          </span>
                        </div>
                        <p className="text-xs text-content-secondary mt-1">{ev.explanation}</p>
                        {ev.source_references && ev.source_references.length > 0 && (
                          <div className="mt-2 flex gap-2 flex-wrap">
                            {ev.source_references.map((ref, k) => (
                              <span key={k} className="text-[9px] px-1.5 py-0.5 bg-border text-content-muted rounded">
                                REF: {ref.split(':')[0]}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
            <div className="mt-auto pt-4 flex gap-2 items-start text-xs text-content-muted">
              <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <p>{t("These factors represent evidence observed during anomaly windows. They are supporting indicators, not confirmed root causes.")}</p>
            </div>
          </div>
        </Card>

        {/* Financial Impact Timeline */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Receipt className="h-4 w-4 text-brand-600" />
              {t("Financial Impact Records")}
            </CardTitle>
          </CardHeader>
          <div className="p-5 pt-0 flex-1">
            {!financial_impacts || financial_impacts.length === 0 ? (
              <div className="text-center py-6 text-content-muted text-sm">
                {t("No financial impact records found.")}
              </div>
            ) : (
              <div className="relative border-l-2 border-border ml-3 pl-5 space-y-6">
                {financial_impacts.map((impact, i) => {
                  const anomaly = anomalies?.find(a => a.anomaly_reference === impact.anomaly_reference);
                  const Icon = anomaly ? SEVERITY_ICONS[anomaly.severity] : Info;
                  return (
                    <div key={i} className="relative">
                      <div className={cn("absolute -left-[29px] top-1 w-6 h-6 rounded-full border-2 border-white flex items-center justify-center", 
                        anomaly ? SEVERITY_BG[anomaly.severity] : "bg-surface-secondary")}
                      >
                        <Icon className={cn("w-3 h-3", anomaly ? SEVERITY_COLORS[anomaly.severity] : "text-content-muted")} />
                      </div>
                      <div className="bg-white border border-border rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <p className="text-xs font-semibold text-content flex items-center gap-1.5">
                              <Calendar className="w-3 h-3 text-content-muted" />
                              {new Date(impact.period_start).toLocaleDateString()} - {new Date(impact.period_end).toLocaleDateString()}
                            </p>
                            {anomaly && (
                              <p className="text-[11px] text-content-secondary mt-0.5">
                                {anomaly.deviation_percent.toFixed(1)}% efficiency drop
                              </p>
                            )}
                          </div>
                          <span className="text-sm font-bold text-red-600">
                            ₹{impact.estimated_financial_exposure.toLocaleString('en-IN')}
                          </span>
                        </div>
                        <div className="flex gap-4 text-xs text-content-secondary bg-surface-secondary p-2 rounded-lg mt-2">
                          <div>
                            <span className="block text-content-muted">{t("Excess Fuel")}</span>
                            <span className="font-medium text-content">{impact.excess_fuel_liters.toFixed(1)} L</span>
                          </div>
                          <div>
                            <span className="block text-content-muted">{t("Ref Price")}</span>
                            <span className="font-medium text-content">₹{impact.fuel_price_per_liter}/{t("L")}</span>
                          </div>
                          <div>
                            <span className="block text-content-muted">{t("Price Source")}</span>
                            <span className="font-medium text-content capitalize">{impact.fuel_price_source.toLowerCase()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
