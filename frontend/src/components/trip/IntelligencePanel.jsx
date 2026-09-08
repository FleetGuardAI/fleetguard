import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle, 
  ShieldAlert, Activity, DollarSign, Route, Truck, User, Info
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/utils/cn';
import { CostBreakdownBar } from '@/pages/trips/IntelligenceCharts';

export function IntelligencePanel({ intelligence, isLoading }) {
  if (isLoading) {
    return (
      <Card className="p-6 border-brand-200 bg-brand-50/50 animate-pulse">
        <div className="h-6 w-1/3 bg-brand-200 rounded mb-4" />
        <div className="space-y-3">
          <div className="h-4 w-full bg-brand-100 rounded" />
          <div className="h-4 w-5/6 bg-brand-100 rounded" />
          <div className="h-4 w-4/6 bg-brand-100 rounded" />
        </div>
      </Card>
    );
  }

  if (!intelligence) {
    return (
      <Card className="p-8 border-dashed border-2 border-border bg-background-elevated flex flex-col items-center justify-center text-center h-full min-h-[400px]">
        <Activity className="w-12 h-12 text-content-muted mb-4 opacity-50" />
        <h3 className="text-lg font-semibold text-content mb-2">Awaiting Route Data</h3>
        <p className="text-sm text-content-muted max-w-xs">
          Enter pickup and destination to calculate distance and begin intelligence evaluation.
        </p>
      </Card>
    );
  }

  const {
    recommendation,
    recommendation_reasons = [],
    risk_level,
    risk_factors = [],
    expected_profit,
    expected_margin_pct,
    expected_total_cost,
    expected_revenue,
    cost_breakdown = [],
    vehicle_suitability,
    driver_suitability,
    warnings = [],
    confidence_level
  } = intelligence;

  const isTake = recommendation === 'TAKE';
  const isReview = recommendation === 'REVIEW';
  const isAvoid = recommendation === 'AVOID';

  return (
    <div className="space-y-6">
      {/* 1. Main Recommendation Banner */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "rounded-2xl p-6 border shadow-sm relative overflow-hidden",
          isTake ? "bg-emerald-50 border-emerald-200 text-emerald-900" :
          isReview ? "bg-amber-50 border-amber-200 text-amber-900" :
          "bg-rose-50 border-rose-200 text-rose-900"
        )}
      >
        <div className="absolute right-0 top-0 opacity-10 pointer-events-none transform translate-x-1/4 -translate-y-1/4">
          {isTake ? <CheckCircle className="w-48 h-48" /> : 
           isReview ? <AlertTriangle className="w-48 h-48" /> : 
           <ShieldAlert className="w-48 h-48" />}
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            {isTake ? <CheckCircle className="w-6 h-6 text-emerald-600" /> : 
             isReview ? <AlertTriangle className="w-6 h-6 text-amber-600" /> : 
             <ShieldAlert className="w-6 h-6 text-rose-600" />}
            <h2 className="text-2xl font-bold tracking-tight">
              {isTake ? "Recommended to Take" : 
               isReview ? "Requires Manual Review" : 
               "Avoid This Trip"}
            </h2>
          </div>
          <p className={cn(
            "text-sm max-w-md",
            isTake ? "text-emerald-700" : isReview ? "text-amber-700" : "text-rose-700"
          )}>
            Based on {confidence_level === 'INSUFFICIENT' ? 'limited inputs' : 'FleetGuard intelligence'}, this trip presents a <span className="font-semibold">{risk_level}</span> operational risk.
          </p>
        </div>
      </motion.div>

      {/* 2. Warnings (Missing Data) */}
      <AnimatePresence>
        {warnings.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="bg-blue-50/50 border border-blue-100 rounded-xl p-4 text-sm text-blue-800 space-y-2"
          >
            <div className="flex items-center gap-2 font-medium text-blue-900 mb-2">
              <Info className="w-4 h-4" />
              Progressive Evaluation
            </div>
            <ul className="list-disc list-inside space-y-1 text-blue-700">
              {warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 3. Financial Summary */}
      {expected_total_cost > 0 && (
        <Card className="p-6">
          <h3 className="text-sm font-medium text-content-muted mb-4 uppercase tracking-wider flex items-center gap-2">
            <DollarSign className="w-4 h-4" /> Financial Projections
          </h3>
          
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-background rounded-lg p-4 border border-border">
              <p className="text-xs text-content-muted mb-1">Expected Cost</p>
              <p className="text-xl font-bold text-content">₹{expected_total_cost.toLocaleString()}</p>
            </div>
            
            <div className="bg-background rounded-lg p-4 border border-border">
              <p className="text-xs text-content-muted mb-1">Expected Profit</p>
              <p className={cn(
                "text-xl font-bold",
                expected_profit > 0 ? "text-emerald-600" : 
                expected_profit < 0 ? "text-rose-600" : "text-content"
              )}>
                {expected_profit !== null ? `₹${expected_profit.toLocaleString()}` : '—'}
              </p>
            </div>
            
            <div className="bg-background rounded-lg p-4 border border-border">
              <p className="text-xs text-content-muted mb-1">Margin</p>
              <div className="flex items-center gap-2">
                <p className={cn(
                  "text-xl font-bold",
                  expected_margin_pct >= 15 ? "text-emerald-600" : 
                  expected_margin_pct >= 5 ? "text-amber-600" : 
                  expected_margin_pct !== null ? "text-rose-600" : "text-content"
                )}>
                  {expected_margin_pct !== null ? `${expected_margin_pct.toFixed(1)}%` : '—'}
                </p>
                {expected_margin_pct !== null && (
                  expected_margin_pct >= 15 ? <TrendingUp className="w-4 h-4 text-emerald-600" /> :
                  expected_margin_pct < 5 ? <TrendingDown className="w-4 h-4 text-rose-600" /> : null
                )}
              </div>
            </div>
          </div>

          {cost_breakdown.length > 0 && (
            <div className="pt-4 border-t border-border">
              <CostBreakdownBar items={cost_breakdown} revenue={expected_revenue} />
            </div>
          )}
        </Card>
      )}

      {/* 4. Feasibility & Factors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Suitability Cards */}
        {vehicle_suitability && (
          <Card className={cn(
            "p-5 border-l-4",
            vehicle_suitability.status === 'SUITABLE' ? "border-l-emerald-500" :
            vehicle_suitability.status === 'UNSUITABLE' ? "border-l-rose-500" : "border-l-amber-500"
          )}>
            <div className="flex items-center gap-2 mb-3">
              <Truck className="w-5 h-5 text-content-muted" />
              <h4 className="font-semibold text-content">Vehicle Suitability</h4>
              <Badge variant={
                vehicle_suitability.status === 'SUITABLE' ? 'success' :
                vehicle_suitability.status === 'UNSUITABLE' ? 'error' : 'warning'
              } className="ml-auto">{vehicle_suitability.status}</Badge>
            </div>
            <ul className="space-y-2 text-sm text-content-muted">
              {vehicle_suitability.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-border shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {driver_suitability && (
          <Card className={cn(
            "p-5 border-l-4",
            driver_suitability.status === 'SUITABLE' ? "border-l-emerald-500" :
            driver_suitability.status === 'UNSUITABLE' ? "border-l-rose-500" : "border-l-amber-500"
          )}>
            <div className="flex items-center gap-2 mb-3">
              <User className="w-5 h-5 text-content-muted" />
              <h4 className="font-semibold text-content">Driver Suitability</h4>
              <Badge variant={
                driver_suitability.status === 'SUITABLE' ? 'success' :
                driver_suitability.status === 'UNSUITABLE' ? 'error' : 'warning'
              } className="ml-auto">{driver_suitability.status}</Badge>
            </div>
            <ul className="space-y-2 text-sm text-content-muted">
              {driver_suitability.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1 w-1.5 h-1.5 rounded-full bg-border shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      {/* Decision Factors */}
      {recommendation_reasons.length > 0 && (
        <Card className="p-6">
          <h3 className="text-sm font-medium text-content-muted mb-4 uppercase tracking-wider">
            Decision Factors
          </h3>
          <div className="space-y-3">
            {recommendation_reasons.map((r, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-background border border-border">
                {r.factor_type === 'positive' ? (
                  <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                )}
                <p className="text-sm text-content">{r.description}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

    </div>
  );
}
