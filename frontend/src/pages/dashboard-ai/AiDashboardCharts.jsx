import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { getDashboardTrends } from '@/api/dashboardApi';

/**
 * Custom ultra-minimal tooltip for sparkline trends.
 */
function SparklineTooltip({ active, payload, prefix = '', suffix = '' }) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value;
  return (
    <div className="bg-fg-deep border border-fg-border px-2 py-1 rounded-lg shadow-sm text-xs font-medium text-fg-text">
      {prefix}
      {typeof value === 'number' ? value.toLocaleString('en-IN') : value ?? '—'}
      {suffix}
    </div>
  );
}

const CHART_CONFIG = [
  {
    id: 'fuel',
    title: 'Fuel Efficiency Trend',
    stroke: '#0ea5e9',
    fill: 'rgba(14, 165, 233, 0.03)',
    prefix: '',
    suffix: ' km/L',
  },
  {
    id: 'revenue',
    title: 'Revenue Trend',
    stroke: '#10b981',
    fill: 'rgba(16, 185, 129, 0.03)',
    prefix: '₹',
    suffix: '',
  },
  {
    id: 'utilization',
    title: 'Fleet Utilization',
    stroke: '#6366f1',
    fill: 'rgba(99, 102, 241, 0.03)',
    prefix: '',
    suffix: '%',
  },
  {
    id: 'maintenance',
    title: 'Maintenance Trend',
    stroke: '#f43f5e',
    fill: 'rgba(244, 63, 94, 0.03)',
    prefix: '₹',
    suffix: '',
  },
];

/**
 * Clean, secondary trends display below the Opportunity Feed.
 * Data is fetched from real backend APIs.
 */
export function AiDashboardCharts() {
  const [trends, setTrends] = useState({ fuel: [], revenue: [], utilization: [], maintenance: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardTrends()
      .then(data => setTrends(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const charts = CHART_CONFIG.map(cfg => ({
    ...cfg,
    data: trends[cfg.id] || [],
  }));

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {charts.map((chart) => {
        const latestValue = chart.data.length > 0 ? chart.data[chart.data.length - 1].value : null;
        const hasData = chart.data.length > 0 && chart.data.some(d => d.value != null && d.value > 0);

        return (
          <div
            key={chart.id}
            className="fg-card-static p-4 flex flex-col justify-between"
          >
            {/* Header */}
            <div className="mb-3">
              <span className="text-[11px] font-semibold text-fg-text-sec uppercase tracking-wider">
                {chart.title}
              </span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-base font-semibold text-fg-text">
                  {latestValue != null ? (
                    <>
                      {chart.prefix}
                      {latestValue.toLocaleString('en-IN')}
                      {chart.suffix}
                    </>
                  ) : (
                    <span className="text-fg-text-sec">No data</span>
                  )}
                </span>
                {latestValue != null && (
                   <span className="text-[10px] text-fg-text-sec">latest</span>
                )}
              </div>
            </div>

            {/* Sparkline */}
            <div className="h-16 w-full -mx-2 -mb-2 overflow-hidden">
              {hasData ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chart.data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
                    <defs>
                      <linearGradient id={`gradient-${chart.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={chart.stroke} stopOpacity={0.1} />
                        <stop offset="100%" stopColor={chart.stroke} stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="day" hide />
                    <YAxis hide domain={['dataMin - 10%', 'dataMax + 10%']} />
                    <Tooltip
                      content={<SparklineTooltip prefix={chart.prefix} suffix={chart.suffix} />}
                      cursor={{ stroke: 'rgba(255,255,255,0.05)', strokeWidth: 1, strokeDasharray: '3 3' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke={chart.stroke}
                      strokeWidth={1.5}
                      fill={`url(#gradient-${chart.id})`}
                      dot={false}
                      activeDot={{ r: 3, stroke: chart.stroke, strokeWidth: 1.5, fill: '#050B09' }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                   <span className="text-xs text-fg-text-sec">
                    {loading ? 'Loading...' : 'Awaiting data'}
                  </span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
