import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, ChevronRight, Route, Fuel, Wrench,
  Receipt, AlertTriangle, TrendingUp, FileText,
} from 'lucide-react';

// ── Demo intelligence items (used when no real data available) ──
const DEMO_INTELLIGENCE = [
  {
    id: 'intel-1',
    type: 'trip',
    severity: 'warning',
    title: 'Trip #4092',
    description: 'Fuel spend is 16% above expected on Delhi → Jaipur route',
    action: 'Review trip',
    actionPath: '/dashboard/trips',
    icon: Route,
  },
  {
    id: 'intel-2',
    type: 'maintenance',
    severity: 'normal',
    title: 'Vehicle RJ14 XX 4821',
    description: 'Service due in 620 km. Schedule proactively to avoid downtime.',
    action: 'Schedule',
    actionPath: '/dashboard/maintenance',
    icon: Wrench,
  },
  {
    id: 'intel-3',
    type: 'expense',
    severity: 'warning',
    title: 'Driver Expense',
    description: '₹4,850 pending verification. 2 receipts flagged for review.',
    action: 'Review',
    actionPath: '/dashboard/expenses',
    icon: Receipt,
  },
  {
    id: 'intel-4',
    type: 'fuel',
    severity: 'critical',
    title: 'Fuel Anomaly',
    description: '18L drop detected on MH12-AB-3901 at 03:42 AM.',
    action: 'Investigate',
    actionPath: '/dashboard/fuel',
    icon: Fuel,
  },
];

const SEVERITY_STYLES = {
  normal: {
    icon: 'text-fg-green bg-fg-green/10 border-fg-green/15',
    dot: 'bg-fg-green',
  },
  warning: {
    icon: 'text-fg-amber bg-fg-amber/10 border-fg-amber/15',
    dot: 'bg-fg-amber',
  },
  critical: {
    icon: 'text-fg-red bg-fg-red/10 border-fg-red/15',
    dot: 'bg-fg-red',
  },
};

export function IntelligencePanel({ alerts = [], insights = [] }) {
  const navigate = useNavigate();

  // Merge real alerts + operations insights into intelligence items
  const items = useMemo(() => {
    const merged = [];

    // Map real alerts
    alerts.forEach((alert, i) => {
      merged.push({
        id: alert.id || `alert-${i}`,
        type: 'alert',
        severity: alert.severity === 'critical' ? 'critical' : 'warning',
        title: 'Fleet Alert',
        description: alert.text,
        action: 'Review',
        actionPath: '/dashboard/alerts',
        icon: AlertTriangle,
      });
    });

    // Map operations engine insights
    insights.forEach((insight) => {
      const isCritical = insight.status?.toLowerCase() === 'critical';
      const isWarning = insight.status?.toLowerCase().includes('attention');

      merged.push({
        id: insight.id,
        type: insight.type || 'insight',
        severity: isCritical ? 'critical' : isWarning ? 'warning' : 'normal',
        title: insight.title,
        description: `${insight.primaryValue}${insight.secondaryValue ? ' — ' + insight.secondaryValue : ''}`,
        action: 'View details',
        actionPath: '/dashboard/reports',
        icon: TrendingUp,
      });
    });

    // Fallback to demo if no real data
    if (merged.length === 0) return DEMO_INTELLIGENCE;
    return merged.slice(0, 6);
  }, [alerts, insights]);

  const attentionCount = items.filter(i => i.severity !== 'normal').length;
  const isDemo = alerts.length === 0 && insights.length === 0;

  return (
    <div className="h-full flex flex-col bg-white border border-border rounded-2xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border/60 shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-3.5 h-3.5 text-fg-green" />
          <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-fg-green">Vahan Intelligence</span>
          {isDemo && (
            <span className="text-[8px] font-bold tracking-widest uppercase text-fg-amber bg-fg-amber/10 px-1.5 py-0.5 rounded">Demo</span>
          )}
        </div>
        <p className="text-[12px] text-content-secondary font-light">
          {attentionCount > 0
            ? <><span className="font-semibold text-content">{attentionCount}</span> {attentionCount === 1 ? 'thing needs' : 'things need'} attention</>
            : 'All clear. Fleet operating normally.'
          }
        </p>
      </div>

      {/* Items */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5 fg-scrollbar">
        {items.map((item, i) => {
          const Icon = item.icon;
          const styles = SEVERITY_STYLES[item.severity] || SEVERITY_STYLES.normal;

          return (
            <motion.div
              key={item.id}
              className="group p-3 rounded-xl border border-border/40 hover:border-border hover:shadow-sm bg-white transition-all cursor-pointer"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.35 }}
              onClick={() => navigate(item.actionPath)}
            >
              <div className="flex items-start gap-2.5">
                <div className={`w-7 h-7 rounded-lg border flex items-center justify-center shrink-0 mt-0.5 ${styles.icon}`}>
                  <Icon className="w-3.5 h-3.5" strokeWidth={1.5} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${styles.dot} shrink-0`} />
                    <p className="text-[11px] font-semibold text-content truncate">{item.title}</p>
                  </div>
                  <p className="text-[11px] text-content-secondary font-light leading-relaxed line-clamp-2">{item.description}</p>
                  <button className="mt-1.5 text-[10px] font-semibold text-fg-green hover:text-fg-green/80 transition-colors flex items-center gap-0.5 opacity-0 group-hover:opacity-100">
                    {item.action} <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
