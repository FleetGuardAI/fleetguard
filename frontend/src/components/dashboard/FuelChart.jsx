import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceDot,
  ReferenceLine,
} from 'recharts';
import { Droplets, AlertTriangle } from 'lucide-react';

/**
 * Custom Recharts tooltip with dark theme styling.
 * @param {{ active: boolean, payload: any[], label: string }} props
 */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  const time = new Date(label).toLocaleString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'short',
  });

  const isTheft = payload.some((p) => p.payload?.is_theft_alert);

  return (
    <div className="bg-white/95 backdrop-blur-lg border border-slate-200 rounded-xl p-3.5 shadow-xl min-w-[200px]">
      <p className="text-xs text-slate-500 mb-2 font-medium">{time}</p>
      {isTheft && (
        <div className="flex items-center gap-2 mb-2 px-2 py-1 bg-red-50 rounded-lg">
          <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
          <span className="text-[11px] text-red-600 font-semibold">THEFT ALERT</span>
        </div>
      )}
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center justify-between gap-4 py-0.5">
          <div className="flex items-center gap-2">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-xs text-slate-700">{entry.name}</span>
          </div>
          <span className="text-xs font-semibold text-slate-900 tabular-nums">
            {entry.value?.toFixed(1)}L
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * Live Fuel Monitor line chart.
 * Plots Expected Burn vs Actual Filtered Level with theft markers.
 * @param {{ data: Array<{ timestamp: string, expected_level: number, actual_filtered_level: number, raw_level: number, is_theft_alert: boolean }>, truckPlate?: string }} props
 */
export default function FuelChart({ data, truckPlate = 'Select Vehicle' }) {
  const theftPoints = useMemo(
    () => data?.filter((d) => d.is_theft_alert) ?? [],
    [data]
  );

  const formattedData = useMemo(
    () =>
      data?.map((d) => ({
        ...d,
        time: new Date(d.timestamp).toLocaleTimeString('en-IN', {
          hour: '2-digit',
          minute: '2-digit',
        }),
      })) ?? [],
    [data]
  );

  return (
    <div
      className="rounded-2xl dashboard-card p-5 animate-slide-up"
      style={{ animationDelay: '400ms', animationFillMode: 'both' }}
      id="fuel-chart"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-50">
            <Droplets className="w-5 h-5 text-cyan-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Live Fuel Monitor</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {truckPlate} · Last 24 hours
            </p>
          </div>
        </div>

        {theftPoints.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-50 border border-red-200 risk-high">
            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
            <span className="text-[11px] font-semibold text-red-600">
              {theftPoints.length} Alert{theftPoints.length > 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <defs>
              <linearGradient id="expectedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />

            <XAxis
              dataKey="time"
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={{ stroke: '#cbd5e1' }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={{ stroke: '#cbd5e1' }}
              tickLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(v) => `${v}L`}
            />

            <Tooltip content={<CustomTooltip />} />

            <Legend
              verticalAlign="top"
              height={30}
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }}
            />

            <Line
              type="monotone"
              dataKey="expected_level"
              name="Expected Burn"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
              activeDot={{ r: 4, stroke: '#10b981', strokeWidth: 2, fill: '#ffffff' }}
            />

            <Line
              type="monotone"
              dataKey="actual_filtered_level"
              name="Actual (Filtered)"
              stroke="#06b6d4"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, stroke: '#06b6d4', strokeWidth: 2, fill: '#ffffff' }}
            />

            <Line
              type="monotone"
              dataKey="raw_level"
              name="Raw Sensor"
              stroke="#475569"
              strokeWidth={1}
              strokeDasharray="2 2"
              dot={false}
              activeDot={false}
              opacity={0.5}
            />

            {/* Theft alert markers */}
            {theftPoints.map((point, i) => (
              <ReferenceDot
                key={i}
                x={new Date(point.timestamp).toLocaleTimeString('en-IN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
                y={point.actual_filtered_level}
                r={6}
                fill="#ef4444"
                stroke="#fca5a5"
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend supplement */}
      <div className="flex items-center gap-6 mt-3 pt-3 border-t border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-emerald-500" style={{ borderTop: '2px dashed #10b981' }} />
          <span className="text-[10px] text-slate-500">Expected Burn Curve</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-cyan-500" />
          <span className="text-[10px] text-slate-500">EMA Filtered Level</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <span className="text-[10px] text-slate-500">Theft Alert</span>
        </div>
      </div>
    </div>
  );
}
