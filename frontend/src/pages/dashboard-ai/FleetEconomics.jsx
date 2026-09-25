import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp, TrendingDown, AlertTriangle, IndianRupee,
} from 'lucide-react';

const DEMO_ECONOMICS = {
  revenue: 482000,
  operatingCost: 361000,
  contribution: 121000,
  breakdown: [
    { label: 'Fuel', value: 182000, pct: 50 },
    { label: 'Driver', value: 64000, pct: 18 },
    { label: 'Tolls', value: 48000, pct: 13 },
    { label: 'Other', value: 77000, pct: 21 },
  ],
  avoidableCost: 18400,
};

function formatINR(num) {
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)}L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)}K`;
  return `₹${num}`;
}

export function FleetEconomics({ kpis = {} }) {
  const hasRealData = kpis.total_expenses_month > 0;
  const data = hasRealData ? {
    revenue: 0,
    operatingCost: kpis.total_expenses_month,
    contribution: 0,
    breakdown: [],
    avoidableCost: 0,
  } : DEMO_ECONOMICS;

  const isDemo = !hasRealData;

  return (
    <div className="bg-white border border-border rounded-2xl shadow-sm p-4 h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <IndianRupee className="w-3.5 h-3.5 text-fg-green" />
          <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-content-secondary">Today's Fleet Economics</span>
          {isDemo && (
            <span className="text-[8px] font-bold tracking-widest uppercase text-fg-amber bg-fg-amber/10 px-1.5 py-0.5 rounded">Demo</span>
          )}
        </div>
      </div>

      {/* Primary metrics row */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <motion.div
          className="text-center p-2.5 rounded-xl bg-fg-green/5 border border-fg-green/10"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, duration: 0.4 }}
        >
          <p className="text-[9px] text-content-muted uppercase tracking-widest font-semibold mb-1">Revenue</p>
          <p className="text-lg font-semibold text-content tracking-tight">{formatINR(data.revenue)}</p>
        </motion.div>

        <motion.div
          className="text-center p-2.5 rounded-xl bg-surface-tertiary border border-border/40"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.15, duration: 0.4 }}
        >
          <p className="text-[9px] text-content-muted uppercase tracking-widest font-semibold mb-1">Op. Cost</p>
          <p className="text-lg font-semibold text-content tracking-tight">{formatINR(data.operatingCost)}</p>
        </motion.div>

        <motion.div
          className="text-center p-2.5 rounded-xl bg-fg-green/5 border border-fg-green/10"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
        >
          <p className="text-[9px] text-content-muted uppercase tracking-widest font-semibold mb-1">Contribution</p>
          <p className="text-lg font-semibold text-fg-green tracking-tight">{formatINR(data.contribution)}</p>
        </motion.div>
      </div>

      {/* Cost breakdown bars */}
      {data.breakdown.length > 0 && (
        <div className="space-y-2 mb-3">
          {data.breakdown.map((item, i) => (
            <div key={item.label} className="flex items-center gap-2">
              <span className="text-[10px] text-content-secondary font-medium w-10 shrink-0">{item.label}</span>
              <div className="flex-1 h-1.5 bg-surface-tertiary rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-fg-green/60 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${item.pct}%` }}
                  transition={{ delay: 0.3 + i * 0.08, duration: 0.6, ease: 'easeOut' }}
                />
              </div>
              <span className="text-[10px] text-content-muted font-medium w-12 text-right shrink-0">{formatINR(item.value)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Avoidable cost alert */}
      {data.avoidableCost > 0 && (
        <motion.div
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-fg-amber/8 border border-fg-amber/15"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.4 }}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-fg-amber shrink-0" />
          <span className="text-[11px] text-content-secondary font-medium">
            <span className="font-semibold text-content">{formatINR(data.avoidableCost)}</span> avoidable cost detected
          </span>
        </motion.div>
      )}
    </div>
  );
}
