import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Search, Send, RefreshCw, Truck, Route, AlertTriangle, Clock,
} from 'lucide-react';
import { cn } from '@/utils/cn';

export function CommandHeader({
  kpis = {},
  refreshing = false,
  onRefresh,
  searchValue = '',
  onSearchChange,
  onSearchSubmit,
  userName = 'Owner',
}) {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  });

  const stats = [
    { label: 'Active Fleet', value: kpis.active_trucks || 0, icon: Truck, color: 'text-fg-green' },
    { label: 'Active Trips', value: kpis.active_trips || 0, icon: Route, color: 'text-fg-green' },
    { label: 'At Risk', value: kpis.theft_alerts || 0, icon: AlertTriangle, color: 'text-fg-amber' },
    { label: 'Delayed', value: kpis.delayed || 0, icon: Clock, color: 'text-fg-amber' },
  ];

  return (
    <div className="flex flex-col gap-3 lg:gap-0 lg:flex-row lg:items-center lg:justify-between px-1 pb-4">
      {/* Left: Identity + Search */}
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <div className="hidden xl:flex flex-col shrink-0">
          <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-fg-green leading-none">The Vaahan</span>
          <span className="text-[11px] text-content-secondary font-light mt-0.5">Fleet Intelligence</span>
        </div>

        {/* Compact search */}
        <div className="flex items-center gap-2 bg-white border border-border rounded-xl px-3.5 py-2 flex-1 max-w-md hover:border-brand-300 focus-within:border-brand-400 focus-within:shadow-[0_0_12px_rgba(34,197,94,0.08)] transition-all">
          <Search className="w-3.5 h-3.5 text-content-muted shrink-0" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => onSearchChange?.(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSearchSubmit?.()}
            placeholder={`Ask Vahan anything...`}
            className="flex-1 bg-transparent border-none outline-none text-xs text-content placeholder:text-content-muted font-light"
          />
          <button
            onClick={onSearchSubmit}
            className="p-1 rounded-lg bg-fg-green hover:bg-fg-green/90 text-white transition-colors"
          >
            <Send className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Center: Fleet Stats */}
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
        {stats.map((stat, i) => (
          <React.Fragment key={stat.label}>
            <motion.div
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-surface-tertiary transition-colors cursor-default shrink-0"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.4 }}
            >
              <stat.icon className={cn('w-3.5 h-3.5', stat.color)} strokeWidth={1.5} />
              <div className="flex items-baseline gap-1.5">
                <span className="text-sm font-semibold text-content tabular-nums">{stat.value}</span>
                <span className="text-[10px] text-content-muted font-medium uppercase tracking-wider hidden sm:inline">{stat.label}</span>
              </div>
            </motion.div>
            {i < stats.length - 1 && (
              <div className="w-px h-4 bg-border/60 shrink-0 hidden sm:block" />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Right: Date + LIVE + Refresh */}
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-[11px] text-content-muted font-light hidden lg:inline">{dateStr}</span>
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-fg-green/8 border border-fg-green/15">
          <div className="w-1.5 h-1.5 rounded-full bg-fg-green animate-pulse" />
          <span className="text-[9px] font-bold text-fg-green uppercase tracking-widest">Live</span>
        </div>
        <button
          onClick={onRefresh}
          className="p-1.5 rounded-lg border border-border bg-white hover:bg-surface-tertiary text-content-secondary transition-colors"
        >
          <RefreshCw className={cn('w-3.5 h-3.5', refreshing && 'animate-spin')} />
        </button>
      </div>
    </div>
  );
}
