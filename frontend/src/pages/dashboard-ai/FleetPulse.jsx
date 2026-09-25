import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, Fuel, Route, Receipt, Wrench, AlertTriangle,
  Clock,
} from 'lucide-react';

const ICON_MAP = {
  fuel: Fuel,
  route: Route,
  Route: Route,
  Fuel: Fuel,
  trip: Route,
  expense: Receipt,
  maintenance: Wrench,
  Package: Receipt,
  CreditCard: Receipt,
  alert: AlertTriangle,
  default: Activity,
};

const DEMO_EVENTS = [
  { id: 'p1', time: '08:12', label: 'Trip #4088 started', type: 'trip', severity: 'normal' },
  { id: 'p2', time: '09:45', label: 'Fuel anomaly RJ07-LM', type: 'fuel', severity: 'critical' },
  { id: 'p3', time: '10:18', label: 'Expense ₹2,400 submitted', type: 'expense', severity: 'normal' },
  { id: 'p4', time: '10:52', label: 'Trip #4091 delayed', type: 'trip', severity: 'warning' },
  { id: 'p5', time: '11:30', label: 'Maintenance alert MH12', type: 'maintenance', severity: 'warning' },
  { id: 'p6', time: '12:05', label: 'Trip #4095 on schedule', type: 'trip', severity: 'normal' },
];

const SEVERITY_COLORS = {
  normal: 'bg-fg-green',
  warning: 'bg-fg-amber',
  critical: 'bg-fg-red',
};

export function FleetPulse({ recentActivity = [] }) {
  const events = useMemo(() => {
    if (recentActivity.length > 0) {
      return recentActivity.slice(0, 8).map((item, i) => ({
        id: item.id || `evt-${i}`,
        time: item.date ? new Date(item.date).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—',
        label: item.title || 'Activity',
        type: item.category || 'default',
        severity: 'normal',
      }));
    }
    return DEMO_EVENTS;
  }, [recentActivity]);

  const isDemo = recentActivity.length === 0;

  return (
    <div className="bg-white border border-border rounded-2xl shadow-sm p-4 h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-fg-green" />
          <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-content-secondary">Fleet Pulse</span>
          {isDemo && (
            <span className="text-[8px] font-bold tracking-widest uppercase text-fg-amber bg-fg-amber/10 px-1.5 py-0.5 rounded">Demo</span>
          )}
        </div>
        <span className="text-[10px] text-content-muted font-light">Last 4 hours</span>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Horizontal time axis */}
        <div className="flex items-center gap-0 overflow-x-auto scrollbar-hide pb-1">
          {events.map((event, i) => {
            const Icon = ICON_MAP[event.type] || ICON_MAP.default;
            const dotColor = SEVERITY_COLORS[event.severity] || SEVERITY_COLORS.normal;

            return (
              <motion.div
                key={event.id}
                className="group relative flex flex-col items-center shrink-0"
                style={{ width: `${100 / events.length}%`, minWidth: '60px' }}
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.06, duration: 0.3 }}
              >
                {/* Connector line */}
                {i < events.length - 1 && (
                  <div className="absolute top-[11px] left-1/2 w-full h-px bg-border/60 z-0" />
                )}

                {/* Dot */}
                <div className={`relative z-10 w-[9px] h-[9px] rounded-full ${dotColor} border-2 border-white shadow-sm group-hover:scale-125 transition-transform cursor-pointer`} />

                {/* Time label */}
                <span className="text-[9px] text-content-muted font-medium mt-1.5 tabular-nums">{event.time}</span>

                {/* Tooltip on hover */}
                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                  <div className="bg-[#0B1018]/95 backdrop-blur-sm text-white px-3 py-2 rounded-lg border border-white/10 shadow-lg whitespace-nowrap">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <Icon className="w-3 h-3 text-white/60" strokeWidth={1.5} />
                      <span className="text-[10px] font-semibold">{event.label}</span>
                    </div>
                    <span className="text-[9px] text-white/50">{event.time}</span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
