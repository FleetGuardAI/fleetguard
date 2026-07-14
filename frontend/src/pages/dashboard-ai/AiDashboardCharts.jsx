import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { MOCK_TRENDS } from '@/data/aiOpportunityData';

/**
 * Custom ultra-minimal tooltip for sparkline trends.
 */
function SparklineTooltip({ active, payload, prefix = '', suffix = '' }) {
  if (!active || !payload?.length) return null;
  const value = payload[0].value;
  return (
    <div className="bg-surface border border-border px-2 py-1 rounded-lg shadow-sm text-xs font-medium text-content">
      {prefix}
      {typeof value === 'number' ? value.toLocaleString('en-IN') : value}
      {suffix}
    </div>
  );
}

/**
 * Clean, secondary trends display below the Opportunity Feed.
 */
export function AiDashboardCharts() {
  const charts = [
    {
      id: 'fuel',
      title: 'Fuel Efficiency Trend',
      data: MOCK_TRENDS.fuel,
      stroke: '#0ea5e9', // Sky blue
      fill: 'rgba(14, 165, 233, 0.03)',
      prefix: '',
      suffix: ' km/L',
      formatter: (v) => `${v.toFixed(1)}`,
    },
    {
      id: 'revenue',
      title: 'Revenue Trend',
      data: MOCK_TRENDS.revenue,
      stroke: '#10b981', // Emerald
      fill: 'rgba(16, 185, 129, 0.03)',
      prefix: '₹',
      suffix: '',
      formatter: (v) => `${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`,
    },
    {
      id: 'utilization',
      title: 'Fleet Utilization',
      data: MOCK_TRENDS.utilization,
      stroke: '#6366f1', // Indigo
      fill: 'rgba(99, 102, 241, 0.03)',
      prefix: '',
      suffix: '%',
      formatter: (v) => `${v}%`,
    },
    {
      id: 'maintenance',
      title: 'Maintenance Trend',
      data: MOCK_TRENDS.maintenance,
      stroke: '#f43f5e', // Rose
      fill: 'rgba(244, 63, 94, 0.03)',
      prefix: '₹',
      suffix: '',
      formatter: (v) => `${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {charts.map((chart) => (
        <div
          key={chart.id}
          className="bg-surface border border-border/50 rounded-2xl p-4 flex flex-col justify-between transition-all duration-300 hover:border-border hover:shadow-card"
        >
          {/* Header */}
          <div className="mb-3">
            <span className="text-[11px] font-semibold text-content-muted uppercase tracking-wider">
              {chart.title}
            </span>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-base font-semibold text-content">
                {chart.prefix}
                {chart.data[chart.data.length - 1].value.toLocaleString('en-IN')}
                {chart.suffix}
              </span>
              <span className="text-[10px] text-content-muted">latest</span>
            </div>
          </div>

          {/* Sparkline */}
          <div className="h-16 w-full -mx-2 -mb-2 overflow-hidden">
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
                  cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '3 3' }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={chart.stroke}
                  strokeWidth={1.5}
                  fill={`url(#gradient-${chart.id})`}
                  dot={false}
                  activeDot={{ r: 3, stroke: chart.stroke, strokeWidth: 1.5, fill: '#ffffff' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      ))}
    </div>
  );
}
